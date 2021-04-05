import subprocess
from aiy.voice import tts

from verbot.shared import State

def power_off_pi():
    tts.say('Night night')
    subprocess.call('sudo shutdown now', shell=True)

def reboot_pi():
    tts.say('Restarting. Please hold')
    subprocess.call('sudo reboot', shell=True)

def say_ip():
    ip_address = subprocess.check_output("hostname -I | cut -d' ' -f1", shell=True)
    tts.say('My IP address is %s' % ip_address.decode('utf-8'))

COMMANDS = {
    "stop"          : State.STOP,
    "forwards"      : State.FORWARDS,
    "backwards"     : State.REVERSE,
    "reverse"       : State.REVERSE,
    "left"          : State.ROTATE_LEFT,
    "turn left"     : State.ROTATE_LEFT,
    "right"         : State.ROTATE_RIGHT,
    "turn right"    : State.ROTATE_RIGHT,
    "pick up"       : State.PICK_UP,
    "put down"      : State.PUT_DOWN,
    "power off"     : power_off_pi,
    "shut down"     : power_off_pi,
    "reboot"        : reboot_pi,
    "ip address"    : say_ip
}


