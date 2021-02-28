import asyncio
from aiohttp import web
from jsonrpcserver import method as json_rpc_method, async_dispatch
from verbot.control import State, Controller as Verbot

class Server:

    def __init__(self, bind_addr="127.0.0.1", listen_port=8080, pigpiod_addr="127.0.0.1", pigpiod_port=8888):
        self._app = web.Application()
        self._bind_addr = bind_addr
        self._listen_port = listen_port
        self._app.router.add_post("/", self._handle_json_rpc_request)
        self._verbot = Verbot(host=pigpiod_addr, port=pigpiod_port)

    def start_server(self):
        """
        This is a synchronous function.
        It will run the asyncio event loop and not return until the loop is stopped
        """
        # wait whilst we initialize verbot controller
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._verbot.init_io())
        # Set a signal handler to get a chance to shutdown gracefully
        self._app.on_shutdown.append(self._on_shutdown)
        try:
            web.run_app(self._app, host=self._bind_addr, port=self._listen_port)
            # web.run_app() runs the event loop indefinitely
        except KeyboardInterrupt:
            self._verbot.cleanup()

    async def _handle_json_rpc_request(self, request):
        request = await request.text()
        # Because jsonrpcserver doesnt support instance methods as @json_rpc_method
        # we need to stash our instance 'self' as a context
        response = await async_dispatch(request=request, context=self)
        if response.wanted:
            return web.json_response(response.deserialized(), status=response.http_status)
        else:
            return web.Response(status=400) # Bad Request

    async def _on_shutdown(self, app):
        await self._verbot.cleanup()
    
@json_rpc_method
async def verbot_action(server, action):
    ACTIONS_STATES={
        "stop"          : State.STOP,
        "forwards"      : State.FORWARDS,
        "reverse"       : State.REVERSE,
        "rotate_left"   : State.ROTATE_LEFT,
        "rotate_right"  : State.ROTATE_RIGHT,
        "pick_up"       : State.PICK_UP,
        "put_down"      : State.PUT_DOWN,
        "talk"          : State.TALK
    }
    new_state = ACTIONS_STATES.get(action)
    if not new_state == None:
        server._verbot.desired_state = new_state

