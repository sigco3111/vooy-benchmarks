#include "oled.h"

#include <string.h>

#include "config.h"
#include "font5x7.h"
#include "hardware/i2c.h"

static uint8_t fb[OLED_WIDTH * OLED_HEIGHT / 8];

static void cmd_list(const uint8_t *cmds, size_t n) {
    /* Control byte 0x00 = command stream. Each command is sent in its own write. */
    for (size_t i = 0; i < n; i++) {
        uint8_t buf[2] = {0x00, cmds[i]};
        i2c_write_blocking(i2c0, OLED_I2C_ADDR, buf, 2, false);
    }
}

void oled_init(void) {
    static const uint8_t init_seq[] = {
        0xAE,         /* display off */
        0xD5, 0x80,   /* clock divide ratio / oscillator */
        0xA8, 0x3F,   /* multiplex ratio 64 */
        0xD3, 0x00,   /* display offset 0 */
        0x40,         /* start line 0 */
        0x8D, 0x14,   /* charge pump on */
        0x20, 0x00,   /* horizontal addressing mode */
        0xA1,         /* segment remap */
        0xC8,         /* COM scan direction remapped */
        0xDA, 0x12,   /* COM pins config for 128x64 */
        0x81, 0xCF,   /* contrast */
        0xD9, 0xF1,   /* pre-charge */
        0xDB, 0x40,   /* VCOMH deselect */
        0xA4,         /* display from RAM */
        0xA6,         /* normal (not inverted) */
        0xAF,         /* display on */
    };
    cmd_list(init_seq, sizeof init_seq);
    oled_clear();
    oled_flush();
}

void oled_clear(void) { memset(fb, 0, sizeof fb); }

static void put_pixel_block(int x, int y, int s) {
    for (int dy = 0; dy < s; dy++) {
        for (int dx = 0; dx < s; dx++) {
            int px = x + dx, py = y + dy;
            if (px < 0 || px >= OLED_WIDTH || py < 0 || py >= OLED_HEIGHT) continue;
            fb[(py >> 3) * OLED_WIDTH + px] |= (uint8_t)(1u << (py & 7));
        }
    }
}

static const uint8_t *glyph_for(char c) {
    if (c >= 'a' && c <= 'z') c = (char)(c - 32);   /* font has uppercase only */
    if (c < 0x20 || c > 0x5F) c = ' ';
    return font5x7[(uint8_t)c - 0x20];
}

int oled_text_at(int x, int y, const char *s, int scale) {
    for (; *s; s++) {
        const uint8_t *g = glyph_for(*s);
        for (int col = 0; col < 5; col++) {
            for (int row = 0; row < 7; row++) {
                if (g[col] & (1u << row)) put_pixel_block(x + col * scale, y + row * scale, scale);
            }
        }
        x += 6 * scale;   /* 5 px glyph + 1 px spacing, scaled */
        if (x >= OLED_WIDTH) break;
    }
    return x;
}

int oled_text(int x, int page, const char *s, int scale) {
    return oled_text_at(x, page * 8, s, scale);
}

void oled_flush(void) {
    for (int page = 0; page < OLED_HEIGHT / 8; page++) {
        uint8_t set_page[] = {0x00, (uint8_t)(0xB0 | page), 0x00, 0x10};
        i2c_write_blocking(i2c0, OLED_I2C_ADDR, set_page, sizeof set_page, false);
        /* Data writes: control byte 0x40 followed by 128 bytes, split in 16-byte chunks. */
        for (int chunk = 0; chunk < OLED_WIDTH; chunk += 16) {
            uint8_t buf[17];
            buf[0] = 0x40;
            memcpy(&buf[1], &fb[page * OLED_WIDTH + chunk], 16);
            i2c_write_blocking(i2c0, OLED_I2C_ADDR, buf, sizeof buf, false);
        }
    }
}
