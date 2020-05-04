# stl
import asyncio
import websockets
import json
from typing import Literal, List, Dict

# ext
import RPi.GPIO as GPIO

PORT = 2112


def compose(f, g):
    """
    Combines two functions, evaluating them RTL.
    :param f:
    :param g:
    :return:
    """
    return lambda *args, **kwargs: f(g(*args, **kwargs))


class Dir:
    L = False
    F = False
    B = False
    R = False


class Car:
    _PINS = {
        'LF': 29,
        'LB': 31,
        'RF': 38,
        'RB': 40,
    }

    def __init__(self):
        GPIO.setmode(GPIO.BOARD)
        for pin in self._PINS.values():
            GPIO.setup(pin, GPIO.OUT)

    def _out(self, pins: List[Literal['LF', 'LB', 'RF', 'RB']], mode: Literal[0, 1]):
        for pin in pins:
            GPIO.output(self._PINS[pin.upper()], mode)

    def off(self, *pins):
        self._out(pins, 0)

    def on(self, *pins):
        self._out(pins, 1)

    def all_off(self):
        """
        Turns all car-related GPIO outputs off.
        """
        self.off(*self._PINS.keys())

    def move_state(self, active_moves: dict):
        self.all_off()
        if active_moves['f'] ^ active_moves['b']:
            f_or_b = 'f' if active_moves['f'] else 'b'

        if active_moves['r'] ^ active_moves['l']:
            l_or_r = 'r' if active_moves['r'] else 'l'

        self.on()


car = Car()


def handle_inp(data):
    op = data['op']
    if op == 'steer':
        car.move_state(data['moveState'])
    elif op == 'stop':
        car.all_off()


async def controller(ws, path):
    while True:
        msg = await ws.recv()
        if msg == 'ping':
            ws.send('pong')
        else:
            data = json.loads(msg)
            handle_inp(data)


server = websockets.serve(controller, '127.0.0.1', PORT)
asyncio.get_event_loop().run_until_complete(controller())
