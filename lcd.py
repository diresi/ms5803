"""LCD playground (Nokia 3310 via SPI)
"""
import time
import RPIO
import spi

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
        spi.transfer(data)

    def data(self, data):
        self.send(RPIO.HIGH, (data,))

    def command(self, data):
        self.send(RPIO.LOW, (data,))

def setup():
    spi.openSPI(mode = 0, speed = 1000000, delay = 0)
    lcd = Nokia3310()
    lcd.reset()
    lcd.command(0x21)   # LCD Extended Commands
    #lcd.command(0xC8)   # Set LCD Vop (Contrast). 0xC8
    lcd.command(0xFF)   # Set LCD Vop (Contrast). 0xC8
    lcd.command(0x04 | int(not(not(LCD_START_LINE_ADDR & (1 << 6)))))   #Set Temp S6 for start line
    lcd.command(0x40 | (LCD_START_LINE_ADDR & ((1<<6)-1)))              #Set Temp S[5:0] for start line
    #lcd.command(0x13)  # LCD bias mode 1:48.
    lcd.command(0x12)   # LCD bias mode 1:68.
    lcd.command(0x20)   # LCD Standard Commands, Horizontal addressing mode
    #lcd.command(0x22)  # LCD Standard Commands, Vertical addressing mode
    lcd.command(0x08)   # LCD blank
    lcd.command(0x0C)   # LCD in normal mode.
    return lcd

def fill(lcd):
    for y in range(6):
        lcd.command(0x80)
        lcd.command(0x40 | y)
        for x in range(84):
            lcd.data(0xa5)

if __name__ == "__main__":
    lcd = setup()
    fill(lcd)
