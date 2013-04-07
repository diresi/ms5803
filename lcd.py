"""LCD playground (Nokia 3310 via SPI driven by a TLS8204 as available from
https://www.olimex.com/Products/Modules/LCD/MOD-LCD3310/).

I don't use extended commands other than level 1 nor OTP.
Note: This implementation uses TLS8204 but is almost compatible to PCD8544,
except start_line_ctrl(), which is not available on the latter.
"""
import time
import RPIO
import spi
from static import ASCII, AWESOME

LCD_RESET = 24
DC = 25

LCD_START_LINE_ADDR = 66 - 2
LCD_WIDTH = 84
LCD_HEIGHT = 48
LCD_LINES = LCD_HEIGHT / 8

def gpio(port, level):
    f = RPIO.gpio_function(port)
    if f:
        RPIO.setup(port, RPIO.OUT, level)
    RPIO.forceoutput(port, level)

class Nokia3310(object):
    def __init__(self, dc=DC, lcd_reset=LCD_RESET):
        self.dc = dc
        self.lcd_reset = lcd_reset
        self.ext = 0x00

    def reset(self):
        gpio(self.lcd_reset, RPIO.LOW)
        gpio(self.lcd_reset, RPIO.HIGH)
        self.ext = 0x00

    def send(self, dc, data):
        gpio(self.dc, dc)
        if hasattr(data, "__iter__"):
            data = tuple(data)
        else:
            data = (data,)
        spi.transfer(data)

    def data(self, data):
        self.send(RPIO.HIGH, data)

    def command(self, data):
        self.send(RPIO.LOW, data)

    def function_set(self, ext = 0x00, powerdown = False):
        cmd = 0x20 | (0x03 & ext)
        if powerdown:
            cmd |= 0x04
        self.ext = ext
        self.command(cmd)

    # ext = 0x00
    def display_ctrl(self, mode = "normal"):
        assert self.ext == 0x00
        # uses bits 3 and 0 to mask 4 commands
        ctrl = {"normal" : 0x04,
                "inverse" : 0x05,
                "all" : 0x01,
                "none" : 0x00,
               }
        assert mode in ("normal", "inverse", "all", "none")
        cmd = 0x08 | ctrl[mode]
        self.command(cmd)

    def set_x(self, x):
        assert self.ext == 0x00
        self.command(0x80 | (0x7F & x))

    def set_y(self, y):
        assert self.ext == 0x00
        self.command(0x40 | (0x07 & y))

    def goto(self, x, y):
        self.set_x(x)
        self.set_y(y)

    def vlcd_range_ctrl(self, high = False):
        assert self.ext == 0x00
        cmd = 0x04 | (0x01 if high else 0x00)
        self.command(cmd)

    # ext = 0x01
    def display_config(self, reverse = False):
        # defines the bit order mapping for display ram (top down or bottom up)
        assert self.ext == 0x01
        self.command(0x08 | (0x04 if reverse else 0x00))

    def bias_ctrl(self, mode):
        assert self.ext == 0x01
        self.command(0x10 | (0x07 & mode))

    def start_line_ctrl(self, line):
        assert self.ext == 0x01
        self.command(0x04 | (0x01 & (line >> 6)))
        self.command(0x40 | (0x3F & line))

    def evr_ctrl(self, vop):
        assert self.ext == 0x01
        self.command(0x80 | (0x7F & vop))

    def setup(self):
        self.reset()

        self.function_set(0x00)
        self.vlcd_range_ctrl(False)

        self.function_set(0x01)
        self.start_line_ctrl(LCD_START_LINE_ADDR) # 6 lines with 8px each
        self.bias_ctrl(4)     # empirically determined
        self.evr_ctrl(80)     # empirically determined

        self.function_set(0x00)

        self.clear()
        self.display_ctrl("normal")

    def fill(self, overlay = False, pattern = 0xFF):
        if overlay:
            self.display_ctrl("all")
        else:
            for l in range(LCD_LINES):
                self.goto(0, l)
                self.data((pattern,) * LCD_WIDTH)
            self.goto(0, 0)

    def clear(self, overlay = False):
        if overlay:
            self.display_ctrl("none")
        else:
            self.fill(pattern = 0x00)

    def test(self):
        self.fill(pattern = 0xA5)

    def bitmap(self, bmp):
        # TLS8204 uses 102 columns and 68 lines, we can't just send the bitmap
        # as-is.
        for l in range(LCD_LINES):
            self.goto(0, l)
            offset = l * LCD_WIDTH
            self.data(bmp[offset:offset + LCD_WIDTH])

    def character(self, c):
        self.data(0x00)
        self.data(ASCII[ord(c) - 0x20])
        self.data(0x00)

    def text(self, txt):
        for x in txt:
            self.character(x)

    def watch(self):
        self.goto(LCD_WIDTH - 8 * 7, LCD_LINES - 1)
        self.text(time.strftime("%H:%M:%S"))

def setup():
    spi.openSPI(mode = 0, speed = 1000000, delay = 0)
    lcd = Nokia3310()
    lcd.setup()
    return lcd

if __name__ == "__main__":
    lcd = setup()

    while True:
        lcd.test()
        time.sleep(1)

        lcd.clear()
        lcd.goto(0, 2)
        lcd.text("resi ruleZ!")
        time.sleep(1)

        lcd.bitmap(AWESOME)
        time.sleep(1)
        break

    while True:
        lcd.watch()
        time.sleep(.5)
