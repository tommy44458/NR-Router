from enum import IntEnum
from typing import Union

from config import WireDirect


class PseudoNodeType(IntEnum):
    INTERNAL = 0
    EXTERNAL = 1
    HUB = 2


class GridType(IntEnum):
    CONTACT_PAD = -1
    GRID = 0
    PSEUDO_NODE = 1
    PSEUDOHUB = 2
    REF = 3
    CORNER = 4

class NeighborNode():
    def __init__(self, grid: 'Grid' = None, capacity: int = None, cost: int = None):
        self.grid: 'Grid' = grid
        self.capacity: int = capacity
        self.cost: int = cost


class Grid():
    def __init__(self, real_x: int = -1, real_y: int = -1, grid_x: int = -1, grid_y: int = -1, type: int = 0):
        self.index: int = -1
        self.real_x: int = int(real_x)
        self.real_y: int = int(real_y)
        self.grid_x: int = grid_x
        self.grid_y: int = grid_y
        self.electrode_x: int = 0
        self.electrode_y: int = 0
        # 0 as grids in block2, 1 as electrodes, >2 as num_electrode in a grid, -1 as contact pads in block1&3, -2 as missing pin in block1&3
        self.type = type
        self.electrode_index = -1
        # neighbor = [[grid, capacity, cost], [], etc.]
        self.neighbor: list[NeighborNode] = []
        self.flow: int = 0
        self.cost: int = 0

        # pseudo node
        self.corner = False
        self.edge_direct: WireDirect = 0
        self.pseudo_node_type: PseudoNodeType = None
        self.covered = False
        self.close_electrode = False
