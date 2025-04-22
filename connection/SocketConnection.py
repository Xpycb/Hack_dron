import websockets
import asyncio
import threading
import queue


class SocketConnection:
    def __init__(self):
        self.websocket = None
        self.received_queue = queue.Queue()
        self.sending_queue = queue.Queue()
        self.connected = False
        self.loop = asyncio.new_event_loop()

    async def _connect(self):
        """Асинхронное подключение к симулятору"""
        self.websocket = await websockets.connect('wss://game.1t.ru/ws')
        self.connected = True
        print("Успешно подключились к симулятору!")

        while True:
            data = await self.websocket.recv()
            self.received_queue.put(data)

            if not self.sending_queue.empty():
                await self.websocket.send(self.sending_queue.get())

    def connect(self):
        """Синхронное подключение"""
        threading.Thread(
            target=self.loop.run_until_complete,
            args=(self._connect(),)
        ).start()

        while not self.connected:
            pass  # Ждем подключения

    def send(self, data: str):
        self.sending_queue.put(data)

    def receive(self):
        return self.received_queue.get()

    def close(self):
        asyncio.run_coroutine_threadsafe(
            self.websocket.close(),
            self.loop
        )