import numpy as np
import math
import sys
import os
from ezdxf.addons import r12writer
from operator import itemgetter, attrgetter
from math import atan2,degrees

class Tile():
    def __init__(self):
        self.real_x = 0
        self.real_y = 0
        self.tile_x = 0
        self.tile_y = 0
        self.capacity = 2
        self.flow = [0,0]
        self.total_flow=0
        self.index = -1
        self.neighbor = []
        self.corner_in = []
        self.contact_pads = []
        self.vertical_path = []
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