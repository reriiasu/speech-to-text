import asyncio
import websockets
import webbrowser
import os
from typing import Optional

python_root_dir = os.path.dirname(os.path.abspath(__file__))
app_root_dir = os.path.dirname(python_root_dir)


class WebSocketServer:
    def __init__(self, loop):
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.loop = loop
        self.server = None

    async def start_server(self):
        self.server = await websockets.serve(self.handler, "localhost", 8765)
        self.call_websocket_client()

    def call_websocket_client(self):
        path = os.path.join(app_root_dir, "websocket_client", "websocket_client.html")
        webbrowser.open("file://" + path)

    async def handler(self, ws: websockets.WebSocketServerProtocol, path):
        self.websocket = ws
        try:
            await ws.wait_closed()
        finally:
            if self.websocket is ws:
                self.websocket = None

    async def stop_server(self):
        if self.server is not None:
            self.server.close()
            await self.server.wait_closed()

    async def send_message(self, message: str):
        if self.websocket is not None:
            await self.websocket.send(message)

    def send_message_threadsafe(self, message: str):
        if self.websocket is not None:
            asyncio.run_coroutine_threadsafe(self.send_message(message), self.loop)
