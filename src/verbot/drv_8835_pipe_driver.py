import asyncio
import struct


# Motor speeds for this module are specified as numbers
# between -MAX_SPEED and MAX_SPEED, inclusive.
MAX_SPEED = 1000000

# Default GPIO pin assignments (using M2 port of Pololu 8835 module)
MOTOR_PWM_PIN = 13
MOTOR_DIR_PIN = 6
# Default PWM frequency - Since pigpio uses hardware PWM we can go very high
PWM_FREQUENCY=250000 # 250 KHz is the max PWM supported by the 8835!

PIGPIOD_PIPE_IN = "/dev/pigpio"
PIGPIOD_PIPE_OUT = "/dev/pigout"
PIGPIOD_PIPE_ERR = "/dev/pigerr"

class Motor(object):

    def __init__(self, *args, **kwargs):
        pass

    async def init_io(self):
        pass

    async def cleanup(self):
        self._setRawSpeedAndDir(0, 0)

    async def setSpeed(self, speed):
        dir_value = 0
        if speed < 0:
            speed = -speed
            dir_value = 1
        if speed > MAX_SPEED:
            speed = MAX_SPEED
        await self._setRawSpeedAndDir(speed, dir_value)
 
    async def setSpeedPercent(self, speed):
        dir_value = 0
        if speed < 0:
            speed = -speed
            dir_value = 1
        if speed > 100:
            speed = 100
        # Map to range
        speed = speed * MAX_SPEED // 100
        await self._setRawSpeedAndDir(speed, dir_value)

    async def _setRawSpeedAndDir(self, speed, dir):

        print("Opening pigpiod input pipe for writing on {0}".format(PIGPIOD_PIPE_IN))
        with open(PIGPIOD_PIPE_IN, mode='wb') as pipe: 
            print("Pipe opened")
            loop = asyncio.get_event_loop()
            print("Connecting asyncio pipe writer")
            transport, _ = await loop.connect_write_pipe(asyncio.Protocol, pipe)
            print("Write pipe connected.")

            # hardware_PWM : pigpio message format
            # I p1 gpio
            # I p2 PWMfreq
            # I p3 4
            ## extension ##
            # I PWMdutycycle
            pwm_data = "hp {0} {1} {2}".format(MOTOR_PWM_PIN, PWM_FREQUENCY, speed).encode("latin-1")
            transport.write(pwm_data)

            # Write : pigpio message format
            # I p1 gpio
            # I p2 level
            dir_data = "w {0} {1}".format(MOTOR_DIR_PIN, dir).encode("latin-1")
            transport.write(dir_data)

            # Flush
            transport.close()