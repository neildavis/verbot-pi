import asyncio
from verbot.control import Controller as Verbot

async def main():
    verbot = Verbot(host="192.168.1.192")
    await verbot.init_io()
    pass

if __name__ == "__main__":
    # execute only if run as a script
    asyncio.run(main())
