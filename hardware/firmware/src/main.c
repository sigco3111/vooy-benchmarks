/*
 * USB OBS desk controller - firmware (Raspberry Pi Pico 2, RP2350)
 *
 * Responsibilities:
 *  - debounce two buttons (REC, SCENE) and rate-limit them (lockout)
 *  - send "BTN REC" / "BTN SCENE" lines over USB CDC to the host bridge
 *  - read "ST <rec> <t_sec> <obs_ok> <scene>" lines from the host (1 Hz heartbeat)
 *  - show OBS-reported state on the OLED and the red LED; never assume a command worked
 *  - report NO LINK when the host heartbeat stops
 *
 * Buttons do not change recording state here. The host's ST line is the only source of truth.
 */
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "config.h"
#include "hardware/gpio.h"
#include "hardware/i2c.h"
#include "oled.h"
#include "pico/stdlib.h"
#include "pico/stdio_usb.h"

typedef struct {
    uint pin;
    bool raw;            /* last raw level (true = pressed) */
    bool stable;         /* debounced level */
    uint32_t raw_since;  /* time raw level last changed */
    uint32_t last_emit;  /* time of last accepted press */
    bool has_emitted;
} button_t;

/* Returns true exactly once per accepted press. */
static bool button_poll(button_t *b, uint32_t now) {
    bool pressed = !gpio_get(b->pin);   /* active LOW with pull-up */
    if (pressed != b->raw) {
        b->raw = pressed;
        b->raw_since = now;
    }
    if (b->raw != b->stable && (now - b->raw_since) >= DEBOUNCE_MS) {
        b->stable = b->raw;
        if (b->stable) {                 /* falling edge in electrical terms = press */
            if (!b->has_emitted || (now - b->last_emit) >= LOCKOUT_MS) {
                b->has_emitted = true;
                b->last_emit = now;
                return true;
            }
        }
    }
    return false;
}

typedef struct {
    int rec;
    unsigned long t_sec;
    bool obs_ok;
    char scene[SCENE_MAX];
    uint32_t last_st_ms;       /* time of last valid ST line; 0 = never */
    bool link_seen;
} host_state_t;

typedef enum { PEND_NONE, PEND_REC, PEND_SCENE } pend_kind_t;

static host_state_t host;
static pend_kind_t pend = PEND_NONE;
static uint32_t pend_since = 0;
static int pend_rec_before = 0;
static char pend_scene_before[SCENE_MAX] = "";
static bool timed_out = false;
static uint32_t timed_out_until = 0;
static uint32_t flash_until = 0;
static const char *flash_text = NULL;

static void send_line(const char *s) {
    if (stdio_usb_connected()) {
        printf("%s\n", s);
        fflush(stdout);
    }
}

static bool link_ok(uint32_t now) {
    return host.link_seen && (now - host.last_st_ms) < LINK_TIMEOUT_MS;
}

/* Parse "ST <rec> <t_sec> <obs_ok> <scene>". Returns false on malformed input (ignored). */
static bool handle_st(const char *line, uint32_t now) {
    int rec = 0, obs = 0;
    unsigned long t = 0;
    char scene[SCENE_MAX * 2] = "";
    if (sscanf(line, "ST %d %lu %d %31s", &rec, &t, &obs, scene) != 4) return false;
    if (rec < REC_STOPPED || rec > REC_PAUSED) return false;
    if (obs != 0 && obs != 1) return false;

    /* Replace '_' with space for the display, truncate to fit. */
    for (char *p = scene; *p; p++) if (*p == '_') *p = ' ';
    strncpy(host.scene, scene, SCENE_MAX - 1);
    host.scene[SCENE_MAX - 1] = '\0';

    host.rec = rec;
    host.t_sec = t;
    host.obs_ok = (obs == 1);
    host.last_st_ms = now;
    host.link_seen = true;

    if (pend == PEND_REC && host.rec != pend_rec_before) {
        pend = PEND_NONE;                 /* OBS confirmed a change */
    }
    if (pend == PEND_SCENE && strcmp(host.scene, pend_scene_before) != 0) {
        pend = PEND_NONE;
    }
    return true;
}

static void handle_line(const char *line, uint32_t now) {
    if (line[0] == 'S' && line[1] == 'T' && line[2] == ' ') {
        handle_st(line, now);
    }
    /* Unknown lines are ignored on purpose. */
}

static void on_button(const char *cmd, uint32_t now, pend_kind_t kind) {
    if (!host.link_seen || !link_ok(now)) {
        flash_text = "NO LINK";
        flash_until = now + FLASH_MSG_MS;
        return;
    }
    if (!host.obs_ok) {
        flash_text = "NO OBS";
        flash_until = now + FLASH_MSG_MS;
        return;
    }
    if (pend != PEND_NONE) {              /* one command in flight at a time */
        return;
    }
    send_line(cmd);
    pend = kind;
    pend_since = now;
    pend_rec_before = host.rec;
    strncpy(pend_scene_before, host.scene, SCENE_MAX);
}

static void update_pend_timeout(uint32_t now) {
    if (pend != PEND_NONE && (now - pend_since) >= PEND_TIMEOUT_MS) {
        pend = PEND_NONE;
        timed_out = true;
        timed_out_until = now + FLASH_MSG_MS * 2;
    }
}

/* LED: solid while RECORDING, blink for transitions/pending, slow blink for PAUSED or no link. */
static bool led_level(uint32_t now) {
    bool up = link_ok(now);
    uint32_t period_half;
    if (!up) period_half = BLINK_SLOW_MS;
    else if (pend != PEND_NONE) period_half = BLINK_FAST_MS;
    else if (host.rec == REC_RECORDING) return true;
    else if (host.rec == REC_STARTING || host.rec == REC_STOPPING) period_half = BLINK_FAST_MS;
    else if (host.rec == REC_PAUSED) period_half = BLINK_SLOW_MS;
    else return false;                    /* STOPPED */
    return ((now / period_half) & 1u) == 0;
}

static void format_time(char *out, size_t n, unsigned long t) {
    unsigned long h = t / 3600, m = (t / 60) % 60, s = t % 60;
    snprintf(out, n, "%02lu:%02lu:%02lu", h, m, s);
}

static const char *status_word(uint32_t now) {
    if (flash_text && now < flash_until) return flash_text;
    if (!link_ok(now)) return "NO LINK";
    if (!host.obs_ok) return "NO OBS";
    if (pend == PEND_REC) return "PEND REC";
    if (pend == PEND_SCENE) return "PEND SCENE";
    if (timed_out && now < timed_out_until) return "TIMEOUT";
    switch (host.rec) {
        case REC_STOPPED:   return "IDLE";
        case REC_STARTING:  return "STARTING";
        case REC_RECORDING: return "REC";
        case REC_STOPPING:  return "STOPPING";
        case REC_PAUSED:    return "PAUSED";
        default:            return "?";
    }
}

static void draw(uint32_t now) {
    char line[32];
    char clock[16];
    oled_clear();
    oled_text(0, 0, status_word(now), 1);

    format_time(clock, sizeof clock, link_ok(now) ? host.t_sec : 0);
    oled_text_at(0, 16, clock, 2);   /* 8 chars * 12 px = 96 px wide */

    snprintf(line, sizeof line, "SCENE %s", link_ok(now) && host.obs_ok ? host.scene : "--");
    line[21] = '\0';                  /* keep to one 128 px line at scale 1 */
    oled_text(0, 5, line, 1);

    snprintf(line, sizeof line, "LINK %s  OBS %s",
             link_ok(now) ? "OK" : "--",
             (link_ok(now) && host.obs_ok) ? "OK" : "--");
    oled_text(0, 7, line, 1);
    oled_flush();
}

int main(void) {
    stdio_init_all();

    gpio_init(PIN_BTN_REC);   gpio_set_dir(PIN_BTN_REC, GPIO_IN);   gpio_pull_up(PIN_BTN_REC);
    gpio_init(PIN_BTN_SCENE); gpio_set_dir(PIN_BTN_SCENE, GPIO_IN); gpio_pull_up(PIN_BTN_SCENE);
    gpio_init(PIN_LED_REC);   gpio_set_dir(PIN_LED_REC, GPIO_OUT);  gpio_put(PIN_LED_REC, 0);

    i2c_init(i2c0, OLED_I2C_BAUD);
    gpio_set_function(PIN_I2C_SDA, GPIO_FUNC_I2C);
    gpio_set_function(PIN_I2C_SCL, GPIO_FUNC_I2C);
    gpio_pull_up(PIN_I2C_SDA);
    gpio_pull_up(PIN_I2C_SCL);
    oled_init();

    button_t btn_rec   = {.pin = PIN_BTN_REC};
    button_t btn_scene = {.pin = PIN_BTN_SCENE};
    char line[LINE_MAX];
    size_t len = 0;

    uint32_t last_hello = 0, last_draw = 0;
    bool hello_sent_once = false;

    for (;;) {
        uint32_t now = to_ms_since_boot(get_absolute_time());

        /* 1. Host input (non-blocking, line based). */
        int c;
        while ((c = getchar_timeout_us(0)) != PICO_ERROR_TIMEOUT) {
            if (c == '\r' || c == '\n') {
                if (len > 0) {
                    line[len] = '\0';
                    handle_line(line, now);
                    len = 0;
                }
            } else if (len < LINE_MAX - 1) {
                line[len++] = (char)c;
            } else {
                len = 0;                  /* overlong line: drop it */
            }
        }

        /* 2. Buttons. */
        if (button_poll(&btn_rec, now))   on_button("BTN REC", now, PEND_REC);
        if (button_poll(&btn_scene, now)) on_button("BTN SCENE", now, PEND_SCENE);

        /* 3. Timers. */
        update_pend_timeout(now);
        if (!link_ok(now) && (now - last_hello) >= HELLO_PERIOD_MS) {
            char hello[32];
            snprintf(hello, sizeof hello, "HELLO %s", FW_VERSION);
            send_line(hello);
            last_hello = now;
            hello_sent_once = true;
        }
        (void)hello_sent_once;

        /* 4. Outputs. */
        gpio_put(PIN_LED_REC, led_level(now));
        if ((now - last_draw) >= DISPLAY_PERIOD_MS) {
            draw(now);
            last_draw = now;
        }
        sleep_ms(1);
    }
    return 0;
}
