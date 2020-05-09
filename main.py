# stl
import asyncio
import websockets
import json
from typing import Tuple

# ext
# import RPi.GPIO as GPIO

PORT = 2112


if not hasattr(__import__(__name__), 'GPIO'):
    class GPIO:
        OUT=1
        BOARD=2

        @staticmethod
        def setmode(*_):
            pass

        @staticmethod
        def setup(*_):
            pass

        @staticmethod
        def output(*_):
            pass


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

    def _out(self, pins: Tuple[str], mode: int):
        for pin in pins:
            GPIO.output(self._PINS[pin.upper()], mode)

    def off(self, *pins: str):
        self._out(pins, 0)
        print(f'LOW {pins}')

    def on(self, *pins: str):
        self._out(pins, 1)
        print(f'HIGH {pins}')

    def all_off(self):
        """
        Turns all car-related GPIO outputs off.
        """
        self.off(*self._PINS.keys())

    def move_state(self, active_moves: dict):
        self.all_off()
        f_or_b = l_or_r = None

        print(active_moves)

        if active_moves['f'] ^ active_moves['b']:
            f_or_b = 'f' if active_moves['f'] else 'b'

        if active_moves['r'] ^ active_moves['l']:
            l_or_r = 'r' if active_moves['r'] else 'l'

        pins = []

        if f_or_b is not None:
            # Front or back
            if l_or_r is not None:
                # Left or right
                pins = [ l_or_r + f_or_b ]
            else:
                # Neither left nor right
                pins = [ 'l' + f_or_b, 'r' + f_or_b ]
        else:
            # Neither front nor back
            if l_or_r is not None:
                # Left or right
                pins = [ l_or_r + 'f' ]
            else:
                # Literally nothing is pressed
                pass

        self.on(*pins)
        return pins


car = Car()


def handle_inp(data):
    op = data['op']
    if op == 'steer':
        return car.move_state(data['moveState'])
    elif op == 'stop':
        car.all_off()


async def controller(ws, path):
    while True:
        msg = await ws.recv()
        if msg == 'ping':
            await ws.send('pong')
        else:
            data = json.loads(msg)
            pins = handle_inp(data)
            await ws.send(f'Activating the following pins: {pins}')

if __name__ == '__main__':
    server = websockets.serve(controller, '127.0.0.1', PORT)
    asyncio.get_event_loop().run_until_complete(server)
    asyncio.get_event_loop().run_forever()
