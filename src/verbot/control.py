from enum import Enum
import asyncio
import itertools
import struct
import apigpio
import verbot.drv_8835_pipe_driver as drv8835

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
    22  : State.STOP,           # Purple
    24  : State.ROTATE_RIGHT,   # Red
    10  : State.ROTATE_LEFT,    # Yellow
    9   : State.FORWARDS,       # Grey
    25  : State.REVERSE,        # Blue
    11  : State.PUT_DOWN,       # Brown
    8   : State.PICK_UP,        # Orange
    7   : State.TALK            # Blue
}

GPIO_BITS = 0
for gpio in GPIO_ACTIONS.keys():
    GPIO_BITS |= (1 << gpio)

MOTOR_SPEED_FOR_INTERROGATION   = 80
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
        self._motor = drv8835.Motor()
        self._current_state = State.STOP
        self._desired_state = State.STOP
        self._last_gpio_bits = GPIO_BITS # all are pulled high to begin

    async def init_io(self):
        # Connect to pigpiod
        print("Connecting to pigpiod on {0}:{1} ...".format(self._address[0], self._address[1]))
        await self._the_pi.connect(self._address)
        print("Connected to pigpiod - Configuring GPIO pins ...")
        # Set all GPIO pins for actions to input and pull up, and register callbacks for edge events
        init_coros = list(itertools.chain.from_iterable(
            (
                self._the_pi.set_mode(pin, apigpio.INPUT),
                self._the_pi.set_pull_up_down(pin, apigpio.PUD_UP),
                self._the_pi.set_glitch_filter(pin, 25000)
                #self._the_pi.add_callback(pin, apigpio.EITHER_EDGE, self._on_gpio_edge_callback)
            ) for pin in GPIO_ACTIONS.keys()
        ))
        # Wait for pigpiod to initialize everything and create the notify pipe
        await asyncio.gather(*init_coros)
        print("GPIO pins configured - Opening notify pipe")
        asyncio.create_task(self._start_observing_notify_pipe_for_gpio_changes())
 
    async def cleanup(self):
        print("Cleanup: motor")
        self._motor.cleanup()
        print("Cleanup: notify pipe")
        await self._stop_observing_notify_pipe_for_gpio_changes()
        print("Cleanup: the_pi")
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
        asyncio.create_task(self._set_motor_speed_for_current_state())
 
    async def _stop_observing_notify_pipe_for_gpio_changes(self):
        if not None == self._notify_pipe_read_task and not self._notify_pipe_read_task.done():
            self._notify_pipe_read_task.cancel()
            await self._notify_pipe_read_task
        
    async def _start_observing_notify_pipe_for_gpio_changes(self):
        # Ask pigpiod to open a pipe to send us notfications
        print("Request notify pipe open from pigpiod ...")
        pipe_handle = await self._the_pi.notify_open()
        if pipe_handle == apigpio.PI_NO_HANDLE:
            print("*ERROR* - notify_begin() pipe_handle={0}".format(pipe_handle))
            return
        print("Notify pipe created on /dev/pigpio{0}".format(pipe_handle))
        # Start observing GPIO via notify pipe - scheduled so we can continue to open and start reading from the pipe before notifcations begin
        asyncio.create_task(self._the_pi.notify_begin(pipe_handle, GPIO_BITS))
        # Open the pipe for reading
        pipe_name = "/dev/pigpio{0}".format(pipe_handle)
        print("Opening notify pipe for reading on {0}".format(pipe_name))
        with open(file=pipe_name, mode='rb', buffering=12) as pipe:
            print("Notify pipe opened for reading")
            loop = asyncio.get_event_loop()
            pipe_stream_reader = asyncio.StreamReader()
            def protocol_factory():
                return asyncio.StreamReaderProtocol(pipe_stream_reader)
            pipe_transport, _ = await loop.connect_read_pipe(protocol_factory, pipe)
            while True:
                #print("Reading 12 bytes from notify pipe...")
                self._notify_pipe_read_task = asyncio.create_task(pipe_stream_reader.read(12))
                await self._notify_pipe_read_task
                if self._notify_pipe_read_task.cancelled():
                    print("Notify pipe read was cancelled")
                    break # Stop observing GPIO changes
                # else the read completed, grab the data from the task result
                pipe_data = self._notify_pipe_read_task.result()
                #print("Got {0} bytes from notify pipe: {1}".format(len(pipe_data), pipe_data))
                '''
                Format is:
                H seqno
                H flags
                I tick
                I level

                seqno: starts at 0 each time the handle is opened and then increments by one for each report.
                flags: three flags are defined, PI_NTFY_FLAGS_WDOG, PI_NTFY_FLAGS_ALIVE, and PI_NTFY_FLAGS_EVENT.
                    If bit 5 is set (PI_NTFY_FLAGS_WDOG) then bits 0-4 of the flags indicate a GPIO which has had a watchdog timeout.
                    If bit 6 is set (PI_NTFY_FLAGS_ALIVE) this indicates a keep alive signal on the pipe/socket and is sent once a minute in the absence of other notification activity.
                    If bit 7 is set (PI_NTFY_FLAGS_EVENT) then bits 0-4 of the flags indicate an event which has been triggered.
                tick: the number of microseconds since system boot. It wraps around after 1h12m.
                level: indicates the level of each GPIO. If bit 1<<x is set then GPIO x is high.
                '''
                seqno, flags, tick, level = struct.unpack("HHII", pipe_data)
                if flags & apigpio.NTFY_FLAGS_ALIVE or flags & apigpio.NTFY_FLAGS_WDOG or flags & apigpio.NTFY_FLAGS_EVENT:
                    print("Notify pipe notification ignored due to flags")
                    continue # not interested in these events
                gpio_changed_bits = level ^ self._last_gpio_bits # a '1' where the state has changed (NOT the new level)
                # Find all GPIOs we're interested in that have changed
                for gpio in GPIO_ACTIONS.keys():
                    gpio_mask = (1 << gpio)
                    if gpio_changed_bits & gpio_mask:
                        old_level = (self._last_gpio_bits & gpio_mask) >> gpio
                        new_level = (level & gpio_mask) >> gpio
                        print("Notify: seqno={0} flags={1} tick={2} GPIO #{3} : {4}->{5}".format(seqno, flags, tick, gpio, old_level, new_level))
                        self._on_gpio_edge_event(gpio, new_level, tick)
                        break
                self._last_gpio_bits = level
            pipe_transport.close()
        print("Notify pipe  closed for reading ... requesting pipe close from pigpiod ...".format(pipe_name))
        await self._the_pi.notify_close(pipe_handle)
        print("Notify pipe {0} closed by pigpiod".format(pipe_name))

    async def _set_motor_speed_for_current_state(self):
        motor_speed = MOTOR_SPEED_FOR_ACTIONS
        if self._current_state == State.INTERROGATE:
            motor_speed = MOTOR_SPEED_FOR_INTERROGATION
        elif self._current_state == State.STOP:
            motor_speed = MOTOR_SPEED_STOPPED
        print("Current state is {0}. Motor speed will be set to {1}".format(self._current_state, motor_speed))
        self._motor.setSpeedPercent(motor_speed)

    def _on_gpio_edge_callback(self, gpio, level, tick):
        if level == apigpio.TIMEOUT:
            return # No change, just a watchdog event
        self._on_gpio_edge_event(gpio, level, tick)

    def _on_gpio_edge_event(self, gpio, level, tick):
        action = GPIO_ACTIONS[gpio]
        print("GPIO edge event occured on pin {0} (action={1}), level is now {2}, tick={3}".format(gpio, action, level, tick))
        if level == apigpio.HIGH:
            '''
            Rising edge: LOW -> HIGH. Remember pins are PULLED HIGH and go LOW when switches are activated
            Most rising edges occur as we exit a state and/or interrogation proceeds to the next switch and can be ignored
            However in the case of PICK_UP/PUT_DOWN they may occur due to the limit switches activating
            In these cases we must stop/reverse the motor to prevent arms trying to rise/fall to far
            '''
            if action == self._current_state:
                print("Rising edge LIMIT switch in state {0}".format(self._current_state))
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
                asyncio.create_task(self._on_reached_desired_state())
            else:
               print("Falling edge ignored on pin {0}".format(gpio))
