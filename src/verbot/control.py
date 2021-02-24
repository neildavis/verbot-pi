from enum import Enum
import asyncio
import itertools
import apigpio
from itertools import chain
import verbot.drv_8835_driver as drv8835


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
    22: State.STOP,
    24: State.ROTATE_RIGHT,
    10: State.ROTATE_LEFT,
    9:  State.FORWARDS,
    25: State.REVERSE,
    11: State.PICK_UP,
    8:  State.PUT_DOWN,
    7:  State.TALK
}

class Controller():
    """
    GPIO controller for Verbot
    """

    def __init__(self, host="127.0.0.1", port="8888"):
        """c'tor"""
        self._address = (host, port)
        self._the_pi = apigpio.Pi()
        self._motor = drv8835.Motor(self._the_pi)
        self._current_state = State.STOP
        self._desired_state = State.STOP

    async def init_io(self):
        # Connect to pigpiod
        await self._the_pi.connect(self._address)
        # Set all GPIO pins for actions to input and pull up, and register callbacks for edge events
        init_coros = list(itertools.chain.from_iterable(
            (
                self._the_pi.set_mode(pin, apigpio.INPUT),
                self._the_pi.set_pull_up_down(pin, apigpio.PUD_UP),
                self._the_pi.add_callback(pin, apigpio.EITHER_EDGE, self._on_gpio_edge_event)
            ) for pin in GPIO_ACTIONS.keys()
        ))
        # Initialize the motor driver GPIO output pins
        init_coros.append(self._motor.init_io())
        await asyncio.gather(*init_coros)
 
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
       self._desired_state = state
       asyncio.create_task(self._on_new_desired_state())

    async def _on_new_desired_state(self):
        if self._desired_state == self._current_state:
            return; # Already in desired state
        '''
        To change state/action we must do the following:
        1. Enter 'action interrogation' mode. i.e. set motor dir CCW to start probing of action switches
        2. Observe GPIO pins as interrogation activates them one-by-one UNTIL pin matching action is triggered
        3. At this point the gearing for the necessary action is in the correct place and we can reverse the motor (CW) to perform the action
        '''
        await self._start_action_interrogation()

    async def _on_reached_desired_state(self):
        '''
        Gear has roatted to correct position for desired state.
        Begin action by setting motor to action mode (CW) and resolve current state
        '''
        self._current_state = self._desired_state
        await self._motor.setSpeedPercent(drv8835.MAX_SPEED)

    async def _start_action_interrogation(self):
        self._current_state = State.INTERROGATE
        await self._motor.setSpeedPercent(-drv8835.MAX_SPEED)
        # ... and wait for falling edge callbacks in self._on_gpio_edge_event

    def _on_gpio_edge_event(self, gpio, level, tick):
        if level == apigpio.TIMEOUT:
            return # No change, just a watchdog event

        action = GPIO_ACTIONS[gpio]
        if level == apigpio.HIGH:
            '''
            Rising edge: LOW -> HIGH. Remember pins are PULLED HIGH and go LOW when switches are activated
            Most rising edges occur as we exit a state and/or interrogation proceeds to the next switch and can be ignored
            However in the case of PICK_UP/PUT_DOWN they may occur due to the limit switches activating
            In these cases we must stop/reverse the motor to prevent arms trying to rise/fall to far
            '''
            if (action == State.PICK_UP or action == State.PUT_DOWN) and action == self._current_state:
                self.desired_state = State.STOP
        else:
            '''
            Falling edge: HIGH -> LOW. Remember pins are PULLED HIGH and go LOW when switches are activated
            '''
            if action == self._current_state:
                return  # Ignore 'noise' of switch for current state activating (again)
            if action == self._desired_state:
                # Gear has reached correct position for new desired state
                asyncio.create_task(self._on_reached_desired_state())

