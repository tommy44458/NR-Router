import numpy as np
import math
import sys
import os
from ezdxf.r12writer import r12writer
from operator import itemgetter, attrgetter
from math import atan2,degrees

class Electrode():
    def __init__(self, real_x=-1, real_y=-1, shape=-1, electrode_index=-1):
        self.real_x = int(real_x)
        self.real_y = int(real_y)
        self.shape = shape
        self.electrode_index = electrode_index
        self.boundary_U=0
        self.boundary_D=0
        self.boundary_L=0
        self.boundary_R=0
        self.surround=0
        self.index = -1

    def to_dict(self):
        _dict = {
            'real_x': self.real_x,
            'real_y': self.real_y,
            'shape': self.shape,
            'electrode_index': self.electrode_index,
            'boundary_U': self.boundary_U,
            'boundary_D': self.boundary_D,
            'boundary_L': self.boundary_L,
            'boundary_R': self.boundary_R,
            'surround': self.surround,
            'index': self.index
        }
            
        return _dict