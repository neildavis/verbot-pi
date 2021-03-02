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

_PI_CMD_WRITE = 4
_PI_CMD_HP = 86

class Motor(object):

    def __init__(self, *args, **kwargs):
        pass

    async def init_io(self):
        try:
            print("Opening pigpiod input pipe for writing on {0}".format(PIGPIOD_PIPE_IN))
            self._pig_pipe_in = open(PIGPIOD_PIPE_IN, mode='wb')
            print("Pipe opened")
            loop = asyncio.get_event_loop()
            print("Connecting asyncio pipe writer")
            self._pipe_write_transport, _ = await loop.connect_write_pipe(asyncio.Protocol, self._pig_pipe_in)
            print("Write pipe connected")
        except Exception as e:
            print("*ERROR* opening pigpiod input pipe {0}: {1}".format(PIGPIOD_PIPE_IN, e))

    async def cleanup(self):
        await self._setRawSpeedAndDir(0, 0)
        # Close pipes
        self._pipe_transport.close()
        self._pig_pipe_in.close()

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
        # hardware_PWM : pigpio message format
        # I p1 gpio
        # I p2 PWMfreq
        # I p3 4
        ## extension ##
        # I PWMdutycycle
        pwm_data = struct.pack('IIIII', _PI_CMD_HP, MOTOR_PWM_PIN, PWM_FREQUENCY, 4, speed)
        
        await self._pipe_write_transport.write(pwm_data)
 
        # Write : pigpio message format
        # I p1 gpio
        # I p2 level
        dir_data = struct.pack('IIII', _PI_CMD_WRITE, MOTOR_DIR_PIN, dir, 0)
        await self._pipe_write_transport.write(dir_data)
 