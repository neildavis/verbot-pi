import asyncio
import apigpio

# Motor speeds for this module are specified as numbers
# between -MAX_SPEED and MAX_SPEED, inclusive.
MAX_SPEED = 1000000

# Default GPIO pin assignments (using M2 port of Pololu 8835 module)
MOTOR_PWM_PIN = 13
MOTOR_DIR_PIN = 6
# Default PWM frequency - Since pigpio uses hardware PWM we can go very high
PWM_FREQUENCY=250000 # 250 KHz is the max PWM supported by the 8835!

class Motor(object):
    def __init__(self, pi:apigpio.Pi):
        self.the_pi = pi
 
    async def init_io(self):
        # Setup digital output GPIO pin for motor direction
        await self.the_pi.set_mode(MOTOR_DIR_PIN, apigpio.OUTPUT),
        # Set initial speed to 0 (stopped) using hardware PWM
        await self._setRawSpeedAndDir(0, 0)

    async def cleanup(self):
        await self._setRawSpeedAndDir(0, 0)

    async def setSpeed(self, speed):
        dir_value = 0
        if speed < 0:
            speed = -speed
            dir_value = 1
        if speed > MAX_SPEED:
            speed = MAX_SPEED
        await self._setRawSpeedAndDir(speed, dir_value)
 
    async def setSpeedPercent(self, speed):
        if speed < -100:
            speed = -100
        elif speed > 100:
            speed = 100
        # Map to range
        speed = speed * MAX_SPEED // 100
        await self.setSpeed(speed)

    async def _setRawSpeedAndDir(self, speed, dir):
        await asyncio.gather(
            # set motor speed via PWM
            self.the_pi.hardware_PWM(MOTOR_PWM_PIN, PWM_FREQUENCY, speed),
            # set motor direction
            self.the_pi.write(MOTOR_DIR_PIN, dir)
        )
        
 