"""LCD playground (Nokia 3310 via SPI)
"""
import time
import RPIO
import spi
from static import ASCII

LCD_RESET = 24
DC = 25

LCD_START_LINE_ADDR = 66 -2

def gpio(port, level):
    f = RPIO.gpio_function(port)
    if f:
        print "setup output"
        RPIO.setup(port, RPIO.OUT, level)
    RPIO.forceoutput(port, level)

class Nokia3310(object):
    def __init__(self, dc=DC, lcd_reset=LCD_RESET):
        self.dc = dc
        self.lcd_reset = lcd_reset

    def reset(self):
        gpio(self.lcd_reset, RPIO.LOW)
        time.sleep(1)
        gpio(self.lcd_reset, RPIO.HIGH)
        time.sleep(1)

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

    def setup(self):
        self.command(0x21)   # LCD Extended Commands
        self.command(0xFF)   # Set LCD Vop (Contras)

        # line mapping mode? this sets up 6 lines with 8px each. without these
        # 2 commands the lcd uses 7 lines where the first has 5px and the last 3px
        self.command(0x04 | int(not(not(LCD_START_LINE_ADDR & (1 << 6)))))   #Set Temp S6 for start line
        self.command(0x40 | (LCD_START_LINE_ADDR & ((1<<6)-1)))              #Set Temp S[5:0] for start line

        self.command(0x06)   # LCD temperature coefficent to 2
        #self.command(0x13)  # LCD bias mode 1:48.
        self.command(0x12)   # LCD bias mode 1:68.
        self.command(0x20)   # LCD Standard Commands, Horizontal addressing mode
        #self.command(0x22)  # LCD Standard Commands, Vertical addressing mode

        self.clear()
        self.mode()
        #self.command(0x08)   # LCD blank (overlay, doesn't clear screen contents)
        #self.command(0x09)   # LCD filled (overlay, doesn't clear screen contents)

    def mode(self, normal = True):
        if normal:
            self.command(0x0C)   # LCD in normal mode
        else:
            self.command(0x0D)   # LCD in inverse mode

    def fill(self, overlay = False, pattern = 0xFF):
        if overlay:
            self.command(0x09)
        else:
            for l in range(7):
                self.goto(0, l)
                self.data((pattern,) * 84)
            self.goto(0, 0)

    def clear(self, overlay = False):
        if overlay:
            self.command(0x08)
        else:
            self.fill(pattern = 0x00)

    def test(self):
        for y in range(6):
            self.command(0x80)
            self.command(0x40 | y)
            for x in range(84):
                self.data(0xa5)

    def goto(self, x, y):
        assert x < 84
        assert y < 7
        self.command(0x80 | x)
        self.command(0x40 | y)

    def bitmap(self, bmp):
        self.goto(0, 0)
        self.data(bmp)

    def character(self, c):
        self.data(0x00)
        self.data(ASCII[ord(c) - 0x20])
        self.data(0x00)

    def text(self, txt):
        for x in txt:
            self.character(x)

def setup():
    spi.openSPI(mode = 0, speed = 1000000, delay = 0)
    lcd = Nokia3310()
    lcd.reset()
    lcd.setup()
    return lcd

if __name__ == "__main__":
    lcd = setup()
    lcd.test()
    time.sleep(2)

    lcd.clear()
    lcd.goto(0, 0)
    lcd.text("resi ruleZ!")
