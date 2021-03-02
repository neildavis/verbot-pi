import asyncio
import RPi.GPIO as GPIO

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
        GPIO.setmode(GPIO.BCM)
        GPIO.setup([MOTOR_PWM_PIN, MOTOR_DIR_PIN], GPIO.OUT)
        # Set initial speed to 0 (stopped) using hardware PWM
        self.setSpeedPercent(0)

    def cleanup(self):
        self.setSpeedPercent(0)
        GPIO.cleanup()

    def setSpeedPercent(self, speed):
        dir = GPIO.HIGH if speed < 0 else GPIO.LOW
        # No PWM for now. -ve speeds are -100, +ve speeds all +100
        speed = GPIO.LOW if speed == 0 else GPIO.HIGH
 
        # Set motor direction
        GPIO.output(MOTOR_DIR_PIN, dir)
        # Set motor speed. No PWM for now, just use digital out
        GPIO.output(MOTOR_PWM_PIN, speed)
        
 