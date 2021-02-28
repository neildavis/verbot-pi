from jsonrpcclient import request

HOST="127.0.0.1:8080"

VALID_ACTIONS={
    "s" : "stop",
    "stop" : "stop",
    "f" : "forwards",
    "forward" : "forwards",
    "forwards" : "forwards",
    "b" : "reverse",
    "backward" : "reverse",
    "backwards" : "reverse",
    "reverse" : "reverse",
    "l" : "rotate_left",
    "left" : "rotate_left",
    "rotate left" : "rotate_left",
    "r" : "rotate_right",
    "right" : "rotate_right",
    "rotate right" : "rotate_right",
    "u" : "pick_up",
    "up" : "pick_up",
    "pick up" : "pick_up",
    "arms up" : "pick_up",
    "d" : "put_down",
    "down" : "put_down",
    "arms down" : "put_down",
    "put down" : "put_down",
    "t" : "talk",
    "talk" : "talk"
}

print("CTRL+C to exit")
while True:
    try:
        cmd = input('Command: ')
        action = VALID_ACTIONS.get(cmd)
        if not action:
            print("{0} is not a valid command. Valid commands are {1}".format(cmd, VALID_ACTIONS.keys()))
            continue
        response = request("http://{0}".format(HOST), "verbot_action", action=action)
    except KeyboardInterrupt:
        print("\nGoodbye!\n")
        break
    except Exception as e:
        print("ERROR: {0}".format(e))
