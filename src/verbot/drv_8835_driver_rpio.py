import asyncio
import RPIO
from RPIO import PWM

# Default GPIO pin assignments (using M2 port of Pololu 8835 module)
MOTOR_PWM_PIN = 13
MOTOR_DIR_PIN = 6
# RPIO DMA Pulse width increment (global setting for ALL DMA channels)
DMA_PULSE_WIDTH_INCREMENT = 1 # 1 us (micro-secs), pulses are a multiple of this WITHIN a subcycle
# RPIO DMA channel used for PWM by this driver
PWM_DMA_CHANNEL_NUMBER = 0  # DMA ch 0
# RPIO DMA channel subcycle time
PWM_DMA_CHANNEL_SUBCYCLE_TIME = 100 # us , i.e. 0.1 ms == 10 KHz PWM frequency

class Motor(object):
    def init_io(self):
        # Setup digital output GPIO pin for motor direction
        RPIO.setup(MOTOR_DIR_PIN, RPIO.OUT)
        # Initialize PWM DMA
        PWM.setup(DMA_PULSE_WIDTH_INCREMENT)
        PWM.init_channel(PWM_DMA_CHANNEL_NUMBER, subcycle_time_us=PWM_DMA_CHANNEL_SUBCYCLE_TIME)
        # Set initial speed to 0 (stopped) using hardware PWM
        self.setSpeedPercent(0)

    def cleanup(self):
        self.setSpeedPercent(0)
        RPIO.cleanup()
 
    def setSpeedPercent(self, speed):
        speed = int(speed)
        if 0 == speed: # Stop = clear PWM
            PWM.clear_channel_gpio(PWM_DMA_CHANNEL_NUMBER, MOTOR_PWM_PIN)
            return
        reverse = False
        if speed < 0:
            speed = -speed
            reverse = True
        if speed > 100:
            speed = 100

        # Set motor direction
        RPIO.output(MOTOR_DIR_PIN, reverse)
        # Set PWM pulses to make up duty cycle. 
        # Since we have a short subcycle (100 us), we'll just use a single pulse and let RPIO repeat for 10 KHz
        RPIO.add_channel_pulse(PWM_DMA_CHANNEL_NUMBER, MOTOR_PWM_PIN, 0, speed)
        
 