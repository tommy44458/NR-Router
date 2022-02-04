from enum import IntEnum
from wire import WireDirect
from typing import Any, Optional, Tuple, Union, List, Dict, Callable, NoReturn


class PseudoNodeType(IntEnum):
    INTERNAL = 0
    EXTERNAL = 1
    HUB = 2


class GridType(IntEnum):
    CONTACTPAD = -1
    GRID = 0
    PSEUDONODE = 1
    PSEUDOHUB = 2


class Grid():
    def __init__(self, real_x=-1, real_y=-1, grid_x=-1, grid_y=-1, type=0):
        self.index = -1
        self.real_x = int(real_x)
        self.real_y = int(real_y)
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.electrode_x = 0
        self.electrode_y = 0
        self.special = False
        self.type = type  # 0 as grids in block2, 1 as electrodes, >2 as num_electrode in a grid, -1 as contact pads in block1&3, -2 as missing pin in block1&3
        self.electrode_index = -1
        # neighbor = [[grid, capacity, cost], [], etc.]
        self.neighbor: List[List[Union[Grid, int]]] = []
        self.flow = 0
        self.cost = 0

        # pseudo node
        self.corner = False
        self.edge_direct: WireDirect = 0
        self.pseudo_node_type: PseudoNodeType = None
        self.covered = False
        self.close_electrode = False

    def to_dict(self):
        _dict = {
            'index': self.index,
            'real_x': self.real_x,
            'real_y': self.real_y,
            'grid_x': self.grid_x,
            'grid_y': self.grid_y,
            'electrode_x': self.electrode_x,
            'electrode_y': self.electrode_y,
            'special': self.special,
            'type': self.type,
            'electrode_index': self.electrode_index,
            'neighbor': self.neighbor,
            'flow': self.flow,
            'cost': self.cost,
            'corner': self.corner,
        }

        return _dict
