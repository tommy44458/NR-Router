from typing import Any, Callable, Dict, List, NoReturn, Optional, Tuple, Union

from grid import Grid
from wire import Wire


class Electrode():
    def __init__(self, real_x=-1, real_y=-1, shape: str = 'base', electrode_index=-1):
        self.real_x = int(real_x)
        self.real_y = int(real_y)
        self.shape = shape
        self.electrode_index = electrode_index
        self.boundary_U = 0
        self.boundary_D = 0
        self.boundary_L = 0
        self.boundary_R = 0
        self.surround = 0
        self.index = -1
        self.poly: list = []
        self.pseudo_node_set: List[Grid] = []
        self.routing_wire: List[Wire] = []

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
