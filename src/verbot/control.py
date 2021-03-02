from enum import Enum
import asyncio
import RPi.GPIO as GPIO
import verbot.drv_8835_driver_rpigpio as drv8835


class State(Enum):
    """Valid states of Controller instances"""
    INTERROGATE     = 0
    STOP            = 1
    ROTATE_RIGHT    = 2
    ROTATE_LEFT     = 3
    FORWARDS        = 4
    REVERSE         = 5
    PICK_UP         = 6
    PUT_DOWN        = 7
    TALK            = 8

GPIO_ACTIONS = {
    22  : State.STOP,
    24  : State.ROTATE_RIGHT,
    10  : State.ROTATE_LEFT,
    9   : State.FORWARDS,
    25  : State.REVERSE,
    11  : State.PUT_DOWN,
    8   : State.PICK_UP,
    7   : State.TALK
}

GPIO_INTERRUPT_DEBOUNCE_MS = 25 # ms debounce on GPIO level chnage interrupt callbacks

class Controller():
    """
    GPIO controller for Verbot
    """

    def __init__(self):
        """c'tor"""
        self._motor = drv8835.Motor()
        self._current_state = State.STOP
        self._desired_state = State.STOP

    def init_io(self):
        # Initialize the motor driver GPIO output pins
        self._motor.init_io()

        # Set all GPIO pins for actions to input and pull up, and register callbacks for edge events
        GPIO.setmode(GPIO.BCM)
        for gpio in GPIO_ACTIONS.keys():
            GPIO.setup(gpio, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(gpio, GPIO.BOTH, callback=self._on_gpio_event_detect, bouncetime=25)
  
        print("GPIO pins configured")
        # We need to stash the event loop for scheduling from the RPi.GPIO threaded callback
        self._loop = asyncio.get_running_loop()

    def cleanup(self):
        GPIO.cleanup()
        self._motor.setSpeedPercent(0)
 
    @property
    def current_state(self) -> State:
        """Returns the current state"""
        return self._current_state

    @property 
    def desired_state(self) -> State:
        """Returns the desired state"""
        return self._desired_state

    @desired_state.setter
    def desired_state(self, state: State) -> None:
        """Request a new desired state"""
        if state == self._current_state: # Already in desired state
            print("Request for new desired state {0} matches current state - ignored".format(state))
            return; 
        self._desired_state = state
        print("New desired state: {0}".format(self._desired_state))
        self._on_new_desired_state()

    def _on_new_desired_state(self):
        '''
        To change state/action we must do the following:
        1. Enter 'action interrogation' mode. i.e. set motor dir CCW to start probing of action switches
        2. Observe GPIO pins as interrogation activates them one-by-one UNTIL pin matching action is triggered
        3. At this point the gearing for the necessary action is in the correct place and we can reverse the motor (CW) to perform the action
        '''
        self._start_action_interrogation()

    def _on_reached_desired_state(self):
        '''
        Gears have rotated to correct position for desired state.
        Begin action by setting motor to action mode (CW) and resolve current state
        '''
        self._current_state = self._desired_state
        self._set_motor_speed_for_current_state()

    def _start_action_interrogation(self):
        self._current_state = State.INTERROGATE
        self._set_motor_speed_for_current_state()
        # ... and wait for falling edge callbacks in self._on_gpio_edge_event

    def _set_motor_speed_for_current_state(self):
        motor_speed = 0 # No actions for now until we debug interrogate debounce
        if self._current_state == State.INTERROGATE:
            motor_speed = 100
        elif self._current_state == State.STOP:
            motor_speed = 0
        print("Current state is {0}. Motor speed will be set to {1}".format(self._current_state, motor_speed))
        self._motor.setSpeedPercent(motor_speed)

    def _on_gpio_event_detect(self, gpio):
        """
        THREADED callback from RPi.GPIO on GPIO edge event
        """
        level = GPIO.input(gpio)
        asyncio.run_coroutine_threadsafe(self._on_gpio_edge_event(gpio, level), self._loop)

    async def _on_gpio_edge_event(self, gpio, level):
        action = GPIO_ACTIONS[gpio]
        print("GPIO edge event occured on pin {0} (action={1}), level is now {2}".format(gpio, action, level))
        if level == 1:
            '''
            Rising edge: LOW -> HIGH. Remember pins are PULLED HIGH and go LOW when switches are activated
            Most rising edges occur as we exit a state and/or interrogation proceeds to the next switch and can be ignored
            However in the case of PICK_UP/PUT_DOWN they may occur due to the limit switches activating
            In these cases we must stop/reverse the motor to prevent arms trying to rise/fall to far
            '''
            if action == self._current_state:
                print("Rising edge for LIMIT SWITCH in state {0}".format(self._current_state))
                self.desired_state = State.STOP
            else:
                print("Rising edge ignored on pin {0}".format(gpio))
        else:
            '''
            Falling edge: HIGH -> LOW. Remember pins are PULLED HIGH and go LOW when switches are activated
            '''
            if action == self._current_state:
                print("Falling edge ignored since action {0} matches current state".format(action))
                return  # Ignore 'noise' of switch for current state activating (again)
            if action == self._desired_state:
                # Gear has reached correct position for new desired state
                print("Falling edge action {0} matches desired state".format(action))
                self._on_reached_desired_state()
            else:
               print("Falling edge ignored on pin {0}".format(gpio))
