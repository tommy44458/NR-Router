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
        self.electrode_x2 = 0
        self.electrode_y2 = 0
        self.special = False
        self.type = type  # 0 as grids in block2, 1 as electrodes, >2 as num_electrode in a grid, -1 as contact pads in block1&3, -2 as missing pin in block1&3
        self.electrode_index = -1
        self.in_x = -1
        self.in_y = -1
        self.out_x = -1
        self.out_y = -1
        self.safe_distance = 0
        self.safe_distance2 = 0
        self.neighbor_electrode: List[List[Union[Grid, int]]] = []
        # neighbor = [[grid, capacity, cost], [], etc.]
        self.neighbor: List[List[Union[Grid, int]]] = []
        self.flow = 0
        self.cost = 0

        # pseudo node
        self.corner = False
        self.edge_direct: WireDirect = 0
        self.pseudo_node_type: PseudoNodeType = None
        self.conflict = False
        self.inner_grid = None
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
            'electrode_x2': self.electrode_x2,
            'electrode_y2': self.electrode_y2,
            'special': self.special,
            'type': self.type,
            'electrode_index': self.electrode_index,
            'in_x': self.in_x,
            'in_y': self.in_y,
            'out_x': self.out_x,
            'out_y': self.out_y,
            'safe_distance': self.safe_distance,
            'safe_distance2': self.safe_distance2,
            'neighbor_electrode': self.neighbor_electrode,
            'neighbor': self.neighbor,
            'flow': self.flow,
            'cost': self.cost,
            'inner_grid': self.inner_grid,
            'corner': self.corner,
        }

        return _dict
