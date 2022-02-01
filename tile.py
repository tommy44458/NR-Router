from typing import Any, Optional, Tuple, Union, List, Dict, Callable, NoReturn
from grid import Grid
from ezdxf.addons import r12writer
from operator import itemgetter, attrgetter
from math import atan2, degrees


class Tile():
    def __init__(self, real_x=0, real_y=0, tile_x=0, tile_y=0):
        self.real_x = real_x
        self.real_y = real_y
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.capacity = 2
        self.flow = [0, 0]
        self.total_flow = 0
        self.index = -1
        self.neighbor = []
        self.corner_in: List[Grid] = []
        self.contact_pads: List[Grid] = []
        self.vertical_path: List[Grid] = []
        self.horizontal_path = []

    def to_dict(self):
        _dict = {
            'real_x': self.real_x,
            'real_y': self.real_y,
            'tile_x': self.tile_x,
            'tile_y': self.tile_y,
            'capacity': self.capacity,
            'flow': self.flow,
            'total_flow': self.total_flow,
            'index': self.index,
            'neighbor': self.neighbor,
            'corner_in': self.corner_in,
            'contact_pads': self.contact_pads,
            'vertical_path': self.vertical_path,
            'horizontal_path': self.horizontal_path,
        }

        return _dict
