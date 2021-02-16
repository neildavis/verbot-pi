from verbot.verbot_control import State as VerbotState, Controller as Verbot
import RPi.GPIO as GPIO

class VerbotObserver(Verbot.Observer):
    def state_will_change(self, state: VerbotState) -> None:
        print("New desired state={0:s}\n".format(state.name))
        pass
    
    def state_did_change(self, state: VerbotState) -> None:
        print("New current state={0:s}\n".format(state.name))
        pass

def main():
    try:
        vbo = VerbotObserver()
        vb = Verbot()
        vb.add_observer(vbo)
        vb.desired_state = VerbotState.TALK
    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    # execute only if run as a script
    main()
