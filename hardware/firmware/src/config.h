#ifndef CONFIG_H
#define CONFIG_H

/* Firmware identity (sent in HELLO) */
#define FW_VERSION "0.1.0"

/* ---- Pin map (Raspberry Pi Pico 2, RP2350). Physical pin numbers in comments.
 * Verified against Pico SDK src/boards/include/boards/pico2.h (I2C0 SDA=4, SCL=5)
 * and the Pico 2 pinout. Physical pins 6/7/17/19/20 are the expected positions; re-check on the real board. */
#define PIN_BTN_REC     14  /* GP14, physical pin 19, active LOW, internal pull-up */
#define PIN_BTN_SCENE   13  /* GP13, physical pin 17, active LOW, internal pull-up */
#define PIN_LED_REC     15  /* GP15, physical pin 20, through 330 ohm to LED anode */
#define PIN_I2C_SDA      4  /* GP4, physical pin 6, I2C0 SDA */
#define PIN_I2C_SCL      5  /* GP5, physical pin 7, I2C0 SCL */

/* ---- OLED (Adafruit 938, SSD1306 128x64) */
#define OLED_I2C_ADDR   0x3C      /* 0x3D if the address jumper is changed */
#define OLED_I2C_BAUD   400000    /* 400 kHz target */
#define OLED_WIDTH      128
#define OLED_HEIGHT     64

/* ---- Timing (ms) */
#define DEBOUNCE_MS       20    /* input must be stable this long */
#define LOCKOUT_MS       250    /* minimum gap between two accepted presses of the same button */
#define HELLO_PERIOD_MS 2000    /* HELLO period while no host status has arrived */
#define LINK_TIMEOUT_MS 3000    /* no ST line for this long -> NO LINK */
#define PEND_TIMEOUT_MS 3000    /* command not confirmed by host within this time -> TIMEOUT */
#define FLASH_MSG_MS    1500    /* short messages such as NO OBS */
#define BLINK_FAST_MS    100    /* 5 Hz blink: half period 100 ms */
#define BLINK_SLOW_MS    500    /* 1 Hz blink: half period 500 ms */
#define DISPLAY_PERIOD_MS 100

/* ---- Protocol */
#define LINE_MAX 96
#define SCENE_MAX 16

/* Recording states as sent by the host (ST rec field) */
#define REC_STOPPED    0
#define REC_STARTING   1
#define REC_RECORDING  2
#define REC_STOPPING   3
#define REC_PAUSED     4

#endif
