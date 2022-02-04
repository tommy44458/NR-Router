from enum import IntEnum
from typing import Any, Optional, Tuple, Union, List, Dict, Callable, NoReturn


class WireDirect(IntEnum):
    UP = 0
    RIGHTUP = 1
    RIGHT = 2
    RIGHTDOWN = 3
    DOWN = 4
    LEFTDOWN = 5
    LEFT = 6
    LEFTUP = 7


class Wire():
    def __init__(self, start_x=0, start_y=0, end_x=0, end_y=0, grid_list=[]):
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.next = None
        self.head = 1
        self.grid_list = grid_list

    def to_dict(self):
        _dict = {
            'start_x': self.start_x,
            'start_y': self.start_y,
            'end_x': self.end_x,
            'end_y': self.end_y,
            'head': self.head
        }
        if self.next is not None:
            _dict['next'] = self.next.to_dict()
        else:
            _dict['next'] = None

        return _dict
