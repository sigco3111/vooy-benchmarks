#ifndef OLED_H
#define OLED_H

#include <stdbool.h>
#include <stdint.h>

/* Minimal SSD1306 driver for a 128x64 I2C OLED (Adafruit 938).
 * The framebuffer is kept in RAM (1024 bytes) and pushed with oled_flush(). */

void oled_init(void);
void oled_clear(void);
/* Draws text at pixel column x, page row (0..7), scale 1 (5x7 glyph) or 2 (10x14). Returns next x. */
int  oled_text(int x, int page, const char *s, int scale);
/* Same as oled_text, but starts at pixel row y (0..63). Used for the large clock line. */
int  oled_text_at(int x, int y, const char *s, int scale);
void oled_flush(void);

#endif
