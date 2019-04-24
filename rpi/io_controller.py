import time
import smbus
import numpy as np
import gpiozero as gpio

from apds9960 import APDS9960


###########################
# Motor related functions #
###########################

motor_pins = {
    'AIN1': gpio.DigitalOutputDevice(27),
    'AIN2': gpio.DigitalOutputDevice(23),
    'PWMA': gpio.PWMOutputDevice(22),
    'BIN1': gpio.DigitalOutputDevice(17),
    'BIN2': gpio.DigitalOutputDevice(15),
    'PWMB': gpio.PWMOutputDevice(14),
    'STBY': gpio.DigitalOutputDevice(18),
}


def get_motor_pins(motor):
    if motor not in ('a', 'b'):
        raise ValueError('motor should be in ("a", "b")!')

    in1, in2, pwm = ((motor_pins['AIN1'], motor_pins['AIN2'], motor_pins['PWMA'])
                     if motor == 'a' else
                     (motor_pins['BIN1'], motor_pins['BIN2'], motor_pins['PWMB']))
    return in1, in2, pwm


def set_motor_speed(motor, speed):
    speed = np.clip(speed, -1, 1)

    motor_pins['STBY'].on()

    in1, in2, pwm = get_motor_pins(motor)

    if speed < 0:
        in1.off()
        in2.on()
    else:
        in1.on()
        in2.off()

    pwm.value = abs(speed)


def motor_short_brake(motor):
    in1, in2, _ = get_motor_pins(motor)
    in1.on()
    in2.on()


#################################
# I2C Proximity/Color functions #
#################################

i2c_channels = {
    'GU2': 0x01,
    'GU3': 0x02,
    'GU4': 0x04,
    'GU5': 0x08,
    'FU1': 0x10,
    'FU2': 0x20,
    'FU4': 0x40,
}

mux_address = 0x70
i2c_bus = smbus.SMBus(1)
ground_threshold = 200


def set_i2c_channel(channel):
    if channel not in i2c_channels.keys():
        raise ValueError('channel should be one of {}'.format(list(i2c_channels.keys())))

    # 0x04 is the register for switching channels
    # See http://www.ti.com/lit/ds/symlink/tca9548a.pdf
    i2c_bus.write_byte_data(mux_address, 0x04, i2c_channels[channel])


def get_ground(sensor):
    return get_dist(sensor) > ground_threshold


def get_color(sensor):
    set_i2c_channel(sensor)

    apds = APDS9960(i2c_bus)
    apds.enableLightSensor()

    time.sleep(0.11)

    red = apds.readRedLight()
    green = apds.readGreenLight()
    blue = apds.readBlueLight()
    ambient = apds.readAmbientLight()

    return (red, green, blue, ambient)


def get_dist(sensor):
    set_i2c_channel(sensor)

    apds = APDS9960(i2c_bus)
    apds.enableProximitySensor()

    time.sleep(0.01)

    return apds.readProximity()


##################
# Buzzer utility #
##################

buzzer = gpio.Buzzer(13, active_high=False)


def buzz(duration):
    buzzer.beep(on_time=duration, n=1)


################
# Leds utility #
################

leds = [gpio.LED(5), gpio.LED(6)]


def led_on(led_id):
    if not (1 <= led_id <= len(leds)):
        raise ValueError('led_id should be in (1, {})!'.format(len(leds)))

    leds[led_id - 1].on()


def led_off(led_id):
    if not (1 <= led_id <= len(leds)):
        raise ValueError('led_id should be in (1, {})!'.format(len(leds)))

    leds[led_id - 1].off()
