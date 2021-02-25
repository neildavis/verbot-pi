from jsonrpcclient import request

VALID_ACTIONS=[
    "stop",
    "forwards",
    "reverse",
    "rotate_left",
    "rotate_right",
    "pick_up",
    "put_down",
    "talk"
]

while True:
    cmd = input('Command: ')
    if not cmd in VALID_ACTIONS:
        print("{0} is not a valid command. Valid commands are {1}".format(cmd, VALID_ACTIONS))
        continue
    try:
        response = request("http://127.0.0.1:8080", "verbot_action", action=cmd)
    except Exception as e:
        print("ERROR: {0}".format(e))