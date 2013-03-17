"""Implemnts I2C readout of MS5803-14BA sensors.
http://www.meas-spec.com/product/t_product.aspx?id=8684

Note: I tried connecting the sensor to my raspi via SPI, but wasn't able to get
(meaningful) reponses.
"""
import time
import smbus

# crc4 and test taken from AN520
def crc4(words):
    n_rem = 0x00
    crc_read = words[-1]
    words[-1] &= 0xff00
    for w in words:
        bytes = [0x00ff & x for x in [w >> 8, w]]
        for b in bytes:
            n_rem ^= b
            for i in range(8):
                if n_rem & 0x8000:
                    n_rem = (n_rem << 1) ^ 0x3000
                else:
                    n_rem = n_rem << 1

    n_rem = 0x000f & (n_rem >> 12)
    words[-1] = crc_read
    return n_rem ^ 0x00

def verify_crc4(words):
    assert (words[-1] & 0x00ff) == crc4(words)

def test_crc4():
    words = [0x3132,0x3334,0x3536,0x3738,0x3940,0x4142,0x4344,0x4500]
    assert 0x0b == crc4(words)

    words[-1] = 0x450b
    verify_crc4(words)

class MS5803_14BA(object):
    def __init__(self, bus, addr):
        self.bus = bus
        self.addr = addr
        self.C = []

    def reset(self):
        self.bus.write_byte(self.addr, 0x1e)

    def prom(self):
        words = []
        for i in range(8):
            h, l = self.bus.read_i2c_block_data(self.addr, 0xa0 | (2*i), 2)
            words.append(h << 8 | l)
        verify_crc4(words)
        self.C = words
        assert len(self.C) == 8

    def adc(self, cmd, osr):
        # osr: 0 = 256, 1 = 512, 2 = 1024, 3 = 2048, 4 = 4096
        assert 0 <= osr <= 4
        self.bus.write_byte(self.addr, cmd | (2 * osr))
        time.sleep(.01) # conversion time for osr=4096 is 8.22ms
        h, m, l = self.bus.read_i2c_block_data(self.addr, 0, 3)
        return (h << 16) | (m << 8) | l

    def pressure(self, osr = 4):
        return self.adc(0x40, osr)

    def temperature(self, osr = 4):
        return self.adc(0x50, osr)

    def read(self, second_order_compensation = True):
        d1 = self.pressure()
        d2 = self.temperature()
        dT = d2 - (self.C[5] << 8)
        t = 2000 + ((dT * self.C[6]) >> 23)

        # 1st order temperature compensation
        off = (self.C[2] << 16) + ((self.C[4] * dT) >> 7)
        sens = (self.C[1] << 15) + ((self.C[3] * dT) >> 8)

        if second_order_compensation:
            # 2nd order temperature compensation
            if t < 2000:
                # low temp
                t2 = (3 * (dT ** 2)) >> 33
                off2 = (3 * (t - 2000) ** 2) >> 1
                sens2 = (5 * (t - 2000) ** 2) >> 3
                if t < -1500:
                    # very low temp
                    off2 = off2 + 7 * (t + 1500) ** 2
                    sens2 = sens2 + 4 * (t + 1500) ** 2
            else:
                # high temp
                t2 = (7 * (dT ** 2)) >> 37
                off2 = (1 * (t - 2000) ** 2) >> 4
                sens2 = 0

            t = t - t2
            off = off - off2
            sens = sens - sens2

        # temperature compensated pressure
        # Note: This algorithm apperantly requires a float division at this
        # point. I can't match the data sheet example pressure otherwise.
        # p = ((d1 * (sens >> 21)) - off) >> 15
        p = int(round(((d1 * (sens / float(1 << 21))) - off) / (2 ** 15)))

        return t / 100.,  p / 10.

class MS5803_14BA_Test(MS5803_14BA):
    # test class using static values from data sheet.
    # this is actually stolen from git://github.com/bagges/ms5803-14ba.git

    def __init__(self, *a, **kw):
        self.C = [0, 46546, 42845, 29751, 29457, 32745, 29059, 0]

    def reset(self):
        pass

    def prom(self):
        pass

    def temperature(self):
        return 8387300

    def pressure(self):
        return 4311550

    def test(self):
        # data sheet values only use 1st order correction
        t, p = self.read(False)
        assert t == 20.15
        assert p == 1000.5

        # but it doesn't make a difference with these values :)
        t, p = self.read(True)
        assert t == 20.15
        assert p == 1000.5

if __name__ == "__main__":
    test_crc4()
    MS5803_14BA_Test().test()

    s = MS5803_14BA(smbus.SMBus(0), 0x77)
    s.reset()
    time.sleep(.003) # startup time
    s.prom()
    d = []
    tmax = pmax = 0.
    tmin = pmin = 1E6
    def f(x):
        return "%.02f" % x
    while True:
        d.append(s.read())
        if len(d) > 5:
            d[:-5] = []
        t = sum([x[0] for x in d]) / len(d)
        p = sum([x[1] for x in d]) / len(d)
        pmax = max(p, pmax)
        pmin = min(p, pmin)
        tmax = max(t, tmax)
        tmin = min(t, tmin)
        print " ".join([f(x) for x in [t, tmin, tmax, tmax - tmin, p, pmin, pmax, pmax - pmin]])
        time.sleep(.2)
