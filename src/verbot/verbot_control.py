from enum import Enum
from abc import ABC
import RPi.GPIO as GPIO
from typing import *

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

class Controller():
    """GPIO controller for Verbot"""

    class Observer(ABC):
        """Abstract - Defines the interface for state observers of Controller instances"""
        def state_will_change(self, state: State) -> None:
            """Called when the a new desired state is requested"""
            pass

        def state_did_change(self, state: State) -> None:
            """Called when the new desired state is reached"""
            pass


    def __init__(self):
        """c'tor"""
        self.__current_state = State.STOP
        self.__desired_state = State.STOP
        self.__observers = []

    @property
    def current_state(self) -> State:
        """Returns the current state"""
        return self.__current_state

    @property 
    def desired_state(self) -> State:
        """Returns the desired state"""
        return self.__desired_state

    @desired_state.setter
    def desired_state(self, state: State) -> None:
       """Request a new desired state"""
       self.__desired_state = state
       self._notify_new_desired_state()

    def add_observer(self, obs: Observer) -> None:
        """Add an object as an observer to receive state chnage notifications. 
        The observer object should implement the methods in the Controller.Observer class
        """
        if obs not in self.__observers:
            self.__observers.append(obs)
    
    def remove_observer(self, obs: Observer) -> None:
        """Remove an observer object"""
        self.__observers.remove(obs)

    def _set_new_current_state(self, state):
       self.__current_state = state
       self._notify_new_current_state()

    def _notify_new_desired_state(self):
        for obs in self.__observers:
            obs.state_will_change(self.__desired_state)
        
    def _notify_new_current_state(self):
        for obs in self.__observers:
            obs.state_did_change(self.__current_state)
        
