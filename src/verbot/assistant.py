import logging
import threading

import apigpio
from google.assistant.library.event import EventType

from aiy.assistant import auth_helpers
from aiy.assistant.library import Assistant
from aiy.board import Board, Led

from verbot.assistant_commands import COMMANDS
from verbot.shared import State

class VerbotAssistant():
    """
    Google Voice Assistant for Verbot
    """
    def __init__(self, pi:apigpio.Pi):
        self._the_pi = pi
        self._callback = None
        self._task = threading.Thread(target=self._run_task, daemon=True)
        self._can_start_conversation = False
        self._conversation_in_progress = False
        self._assistant = None
        self._board = Board()

    def start(self, callback=None):
        """
        Starts the assistant event loop and begins processing events.
        """
        self._callback = callback
        self._task.start()

    def stop(self):
        # TODO: Clean shutdown of assitant task thread instead of just daemon-izing it!
        self._update_led(Led.OFF, 0.0)

    def toggle_conversation(self):
        if self._can_start_conversation:
            self._assistant.start_conversation()
        elif self._conversation_in_progress:
            self._assistant.stop_conversation()
        
    def _run_task(self):
        credentials = auth_helpers.get_assistant_credentials()
        with Assistant(credentials) as assistant:
            self._assistant = assistant
            for event in assistant.start():
                self._process_event(event)

    def _process_event(self, event):
        logging.info(event)
        if event.type == EventType.ON_START_FINISHED:
            self._update_led(Led.ON, 0.1)
            self._can_start_conversation = True
            # Start the voicehat button trigger.
            logging.info('Assistant ready')

        elif event.type == EventType.ON_CONVERSATION_TURN_STARTED:
            self._conversation_in_progress = True
            self._can_start_conversation = False
            self._update_led(Led.ON, 1.0)

        elif event.type == EventType.ON_END_OF_UTTERANCE:
            self._update_led(Led.PULSE_SLOW, 0.1)

        elif event.type == EventType.ON_RECOGNIZING_SPEECH_FINISHED and event.args:
            print('You said:', event.args['text'])
            text = event.args['text'].lower()
            self._on_recognized_speech(text)

        elif event.type == EventType.ON_RESPONDING_STARTED:
            self._update_led(Led.PULSE_SLOW, 1.0)

        elif (event.type == EventType.ON_CONVERSATION_TURN_FINISHED
              or event.type == EventType.ON_CONVERSATION_TURN_TIMEOUT
              or event.type == EventType.ON_NO_RESPONSE):
            self._update_led(Led.ON, 0.1)
            self._can_start_conversation = True
            self._conversation_in_progress = False

    def _on_recognized_speech(self, text):
        action = COMMANDS.get(text)
        if callable(action):
            self._assistant.stop_conversation()
            action()
        elif isinstance(action, State) and callable(self._callback):
            self._assistant.stop_conversation()
            self._callback(action)


    def _update_led(self, state, brightness):
        self._board.led.state = state
        self._board.led.brightness = brightness

 
