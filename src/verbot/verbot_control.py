from enum import Enum
import RPi.GPIO as GPIO

class VerbotController():
    """GPIO controller for Verbot"""

    class State(Enum):
        """Valid states of VerbotController instances"""
        INTERROGATE     = 0
        STOP            = 1
        ROTATE_RIGHT    = 2
        ROTATE_LEFT     = 3
        FORWARDS        = 4
        REVERSE         = 5
        PICK_UP         = 6
        PUT_DOWN        = 7
        TALK            = 8

    class Observer:
        """Defines the interface for state observers of VerbotController instances"""
        def state_will_change(self, state):
            """Called when the a new desired state is requested"""
            pass
        def state_did_change(self, state):
            """Called when the new desired state is reached"""
            pass


    @property
    def current_state(self):
        return self.__current_state

    def __init__(self):
        """c'tor"""
        self.__current_state = self.State.STOP
        self.__desired_state = self.State.STOP
        self.__observers = []

    def add_observer(self, obs):
        """Add an object as an observer to receive state chnage notifications. 
        The observer object should implement the methods in the VerbotController.Observer class
        """
        if obs not in self.__observers:
            self.__observers.append(obs)
    
    def remove_observer(self, obs):
        """Remove an observer object"""
        self.__observers.remove(obs)

    def move_forward(self):
        """Request for Verbot to move forwards"""
        self._set_new_desired_state(self.State.FORWARDS)


    def _set_new_desired_state(self, state):
       self.__desired_state = state
       self._notify_new_desired_state()

    def _set_new_current_state(self, state):
       self.__current_state = state
       self._notify_new_current_state()

    def _notify_new_desired_state(self):
        for obs in self.__observers:
            obs.state_will_change(self.__desired_state)
        
    def _notify_new_current_state(self):
        for obs in self.__observers:
            obs.state_did_change(self.__current_state)
        
