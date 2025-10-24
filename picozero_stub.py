# ==== picozero_stub.py ==== #
from machine import Pin, PWM
from time import sleep

class DigitalOutputDevice:
    def __init__(self, pin):
        self.pin = Pin(pin, Pin.OUT)
    def on(self):
        self.pin.value(1)
    def off(self):
        self.pin.value(0)
    def value(self, v=None):
        if v is None:
            return self.pin.value()
        self.pin.value(int(bool(v)))

class DigitalInputDevice:
    def __init__(self, pin):
        self.pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self._callbacks = []
        self.last = self.pin.value()

    def when_activated(self, func):
        self._callbacks.append(func)

    def when_deactivated(self, func):
        self._callbacks.append(func)

    def check(self):
        val = self.pin.value()
        if val != self.last:
            for cb in self._callbacks:
                cb()
        self.last = val

class Robot:
    def __init__(self, motor1_pins, motor2_pins):
        self.m1a = PWM(Pin(motor1_pins[0]))
        self.m1b = PWM(Pin(motor1_pins[1]))
        self.m2a = PWM(Pin(motor2_pins[0]))
        self.m2b = PWM(Pin(motor2_pins[1]))
        for m in (self.m1a, self.m1b, self.m2a, self.m2b):
            m.freq(1000)

    def value(self, speeds):
        left, right = speeds
        self.m1a.duty_u16(int(65535 * max(0, left)))
        self.m1b.duty_u16(int(65535 * max(0, -left)))
        self.m2a.duty_u16(int(65535 * max(0, right)))
        self.m2b.duty_u16(int(65535 * max(0, -right)))

    def stop(self):
        self.m1a.duty_u16(0)
        self.m1b.duty_u16(0)
        self.m2a.duty_u16(0)
        self.m2b.duty_u16(0)
