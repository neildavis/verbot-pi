# Motor speeds for this module are specified as numbers
# between -MAX_SPEED and MAX_SPEED, inclusive.
MAX_SPEED = 255

# Default GPIO pin assignments (using M2 port of Pololu 8835 module)
MOTOR_PWM_PIN = 13
MOTOR_DIR_PIN = 6
# Default PWM frequency - Note pigpio will match nearest based on sample rate
PWM_FREQUENCY=250000 # 250 KHz is the max PWM supported by the 8835!

PIGPIOD_PIPE_IN = "/dev/pigpio"
PIGPIOD_PIPE_OUT = "/dev/pigout"
PIGPIOD_PIPE_ERR = "/dev/pigerr"

class Motor(object):

    def init_io(self):
        with open(PIGPIOD_PIPE_IN, mode='wb') as pipe: 
            # Set PWM range
            pwm_data = "_PI_CMD_PRS {0} {1}\n".format(MOTOR_PWM_PIN, MAX_SPEED).encode("latin-1")
            pipe.write(pwm_data)
            # Set PWM frequency
            pwm_data = "_PI_CMD_PFS {0} {1}\n".format(MOTOR_PWM_PIN, PWM_FREQUENCY).encode("latin-1")
            pipe.write(pwm_data)
            

    def cleanup(self):
        self._setRawSpeedAndDir(0, 0)

    def setSpeed(self, speed):
        dir_value = 0
        if speed < 0:
            speed = -speed
            dir_value = 1
        if speed > MAX_SPEED:
            speed = MAX_SPEED
        self._setRawSpeedAndDir(speed, dir_value)
 
    def setSpeedPercent(self, speed):
        dir_value = 0
        if speed < 0:
            speed = -speed
            dir_value = 1
        if speed > 100:
            speed = 100
        # Map to range
        speed = speed * MAX_SPEED // 100
        self._setRawSpeedAndDir(speed, dir_value)

    def _setRawSpeedAndDir(self, speed, dir):

        print("Opening pigpiod input pipe for writing motor cmd on {0}: speed={1} dir={2}".format(PIGPIOD_PIPE_IN, speed, dir))
        with open(PIGPIOD_PIPE_IN, mode='wb') as pipe: 
            # Set direction first
            dir_data = "w {0} {1}\n".format(MOTOR_DIR_PIN, dir).encode("latin-1")
            pipe.write(dir_data)
            pwm_data = "_PI_CMD_PWM {0} {1}\n".format(MOTOR_PWM_PIN, int(speed)).encode("latin-1")
            pipe.write(pwm_data)
