import asyncio
import itertools
import apigpio
import verbot.drv_8835_driver as drv8835
from verbot.shared import State
from verbot.assistant import VerbotAssistant

GPIO_ACTIONS = {
    22  : State.STOP,           # Purple
    26  : State.ROTATE_RIGHT,   # Red
    10  : State.ROTATE_LEFT,    # Yellow
    9   : State.FORWARDS,       # Grey
    25  : State.REVERSE,        # Blue
    11  : State.PUT_DOWN,       # Brown
    8   : State.PICK_UP,        # Orange
    7   : State.TALK,           # Blue
    16  : State.ASSISTANT       # Voice assistant
}

MOTOR_SPEED_FOR_INTERROGATION   = 40
MOTOR_SPEED_FOR_ACTIONS         = -100
MOTOR_SPEED_STOPPED             = 0

class Controller():
    """
    GPIO controller for Verbot
    """

    def __init__(self, host="127.0.0.1", port="8888"):
        """c'tor"""
        self._address = (host, port)
        self._the_pi = apigpio.Pi()
        self._motor = drv8835.Motor(self._the_pi)
        self._assistant = VerbotAssistant(self._the_pi)
        self._current_state = State.STOP
        self._desired_state = State.STOP

    async def init_io(self):
        self._loop = asyncio.get_running_loop()
        # Connect to pigpiod
        print("Connecting to pigpiod on {0}:{1} ...".format(self._address[0], self._address[1]))
        await self._the_pi.connect(self._address)
        print("Connected to pigpiod - Configuring GPIO pins ...")
        # Set all GPIO pins for actions to input and pull up, and register callbacks for edge events
        init_coros = list(itertools.chain.from_iterable(
            (
                self._the_pi.set_mode(pin, apigpio.INPUT),
                self._the_pi.set_pull_up_down(pin, apigpio.PUD_UP),
                self._the_pi.add_callback(pin, apigpio.EITHER_EDGE, self._on_gpio_edge_event),
                self._the_pi.set_glitch_filter(pin, 25000)
            ) for pin in GPIO_ACTIONS.keys()
        ))
        # Initialize the motor driver GPIO output pins
        init_coros.append(self._motor.init_io())
        # await it all
        await asyncio.gather(*init_coros)
        print("GPIO pins configured - Starting assistant ...")
        self._assistant.start(callback=self._on_assistant_action)

    async def cleanup(self):
        self._assistant.stop()
        await self._motor.setSpeedPercent(0)
        await self._the_pi.stop()
 
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

        if state == State.ASSISTANT:
            print("Request for new desired state {0}. Desired state will be set to STOP and assistant started/stopped".format(state))
            state = State.STOP
            self._assistant.toggle_conversation()

        if state == self._current_state: # Already in desired state
            print("Request for new desired state {0} matches current state - ignored".format(state))
            return; 

        self._desired_state = state
        print("New desired state: {0}".format(self._desired_state))
        asyncio.create_task(self._on_new_desired_state())

    async def _on_new_desired_state(self):
        '''
        To change state/action we must do the following:
        1. Enter 'action interrogation' mode. i.e. set motor dir CCW to start probing of action switches
        2. Observe GPIO pins as interrogation activates them one-by-one UNTIL pin matching action is triggered
        3. At this point the gearing for the necessary action is in the correct place and we can reverse the motor (CW) to perform the action
        '''
        await self._start_action_interrogation()

    async def _on_reached_desired_state(self):
        '''
        Gears have rotated to correct position for desired state.
        Begin action by setting motor to action mode (CW) and resolve current state
        '''
        self._current_state = self._desired_state
        await self._set_motor_speed_for_current_state()

    async def _start_action_interrogation(self):
        self._current_state = State.INTERROGATE
        await self._set_motor_speed_for_current_state()
        # ... and wait for falling edge callbacks in self._on_gpio_edge_event

    async def _set_motor_speed_for_current_state(self):
        motor_speed = MOTOR_SPEED_FOR_ACTIONS
        if self._current_state == State.INTERROGATE:
            motor_speed = MOTOR_SPEED_FOR_INTERROGATION
        elif self._current_state == State.STOP:
            motor_speed = MOTOR_SPEED_STOPPED
        print("Current state is {0}. Motor speed will be set to {1}".format(self._current_state, motor_speed))
        await self._motor.setSpeedPercent(motor_speed)

    def _on_gpio_edge_event(self, gpio, level, tick):
        if level == apigpio.TIMEOUT:
            return # No change, just a watchdog event

        action = GPIO_ACTIONS[gpio]
        edge_event_type = "RISING" if level == apigpio.HIGH else "FALLING"
        print("EVENT (tick={4}): {0} edge event on GPIO #{1} ({2}), level={3}".format(edge_event_type, gpio, action, level, tick))

        # Special case for Assistant button press, distinct from the the other inputs which are action switches
        if action == State.ASSISTANT:
            if level == apigpio.LOW:
                self.desired_state = State.ASSISTANT
            return

        if level == apigpio.HIGH:
            '''
            Rising edge: LOW -> HIGH. Remember pins are PULLED HIGH and go LOW when switches are activated
            Most rising edges occur as we exit a state and/or interrogation proceeds to the next switch and can be ignored
            However in the case of PICK_UP/PUT_DOWN they may occur due to the limit switches in series activating
            In these cases we must stop/reverse the motor to prevent arms trying to rise/fall to far
            '''
            if action == self._current_state:
                print("LIMIT switch for state {0}".format(self._current_state))
                self.desired_state = State.STOP
        else:
            '''
            Falling edge: HIGH -> LOW. Remember pins are PULLED HIGH and go LOW when switches are activated
            '''
            if action == self._current_state:
                return  # Ignore 'noise' of switch for current state activating (again)
            if action == self._desired_state:
                # Gear has reached correct position for new desired state
                print("Action {0} matches desired state".format(action))
                asyncio.create_task(self._on_reached_desired_state())

    def _on_assistant_action(self, state):
        """
        Assistant callback. Called on worker thread
        """
        if isinstance(state, State):
            print("ASSISTANT: request for state {}".format(state))
            # Note: this is called on an alternative thread, so we need to schedule it on the main thread loop
            asyncio.run_coroutine_threadsafe(self._set_new_desired_state_threadsafe_wrapper(state), self._loop)           

    async def _set_new_desired_state_threadsafe_wrapper(self, state: State):
        """
        A coroutine to wrap the property setter for when we need to call it from a callback thread
        """
        self.desired_state = state

