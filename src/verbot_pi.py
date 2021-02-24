import asyncio
from verbot.control import Controller as Verbot, State

verbot = None

async def connect():
    global verbot
    verbot = Verbot(host="192.168.1.192")
    await verbot.init_io()
    await asyncio.sleep(1)

async def do_states(interval=30.0):
    while True:
        print("*** TEST **** FORWARDS (Grey)")
        verbot.desired_state = State.FORWARDS
        await asyncio.sleep(interval)
        print("*** TEST **** REVERSE (Blue)")
        verbot.desired_state = State.REVERSE
        await asyncio.sleep(interval)
        print("*** TEST **** ROTATE LEFT (Yellow)")
        verbot.desired_state = State.ROTATE_LEFT
        await asyncio.sleep(interval)
        print("*** TEST **** ROTATE RIGHT (Red)")
        verbot.desired_state = State.ROTATE_RIGHT
        await asyncio.sleep(interval)
        print("*** TEST **** PICK UP (Brown)")
        verbot.desired_state = State.PICK_UP
        await asyncio.sleep(interval)
        print("*** TEST **** PUT DOWN (ORANGE)")
        verbot.desired_state = State.PUT_DOWN
        await asyncio.sleep(interval)
        print("*** TEST **** TALK (Green)")
        verbot.desired_state = State.TALK
        await asyncio.sleep(interval)
        print("*** TEST **** STOP (Purple)")
        verbot.desired_state = State.STOP
        await asyncio.sleep(interval)

async def main():
    await connect()
    await asyncio.sleep(1.0)
    await do_states()

if __name__ == "__main__":
    # execute only if run as a script
    asyncio.run(main())
