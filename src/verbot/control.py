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
        self.address = (host, port)
        self.the_pi = apigpio.Pi()
        self.motor = drv8835.Motor(self.the_pi)
        self._current_state = State.STOP
        self._desired_state = State.STOP

    async def init_io(self):
        # Connect to pigpiod
        await self.the_pi.connect(self.address)
        # Set all GPIO pins for actions to input and pull up
        init_coros = list(itertools.chain.from_iterable(
            (
                self.the_pi.set_mode(pin, apigpio.INPUT),
                self.the_pi.set_pull_up_down(pin, apigpio.PUD_UP)
            ) for pin in GPIO_ACTIONS.keys()
        ))
        # Initialize the motor driver GPIO output pins
        init_coros.append(self.motor.init_io())
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
       asyncio.create_task(self._on_new_desried_state())

    async def _on_new_desried_state(self):
        pass

