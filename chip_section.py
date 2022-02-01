import numpy as np
from typing import Any, Optional, Tuple, Union, List, Dict, Callable, NoReturn
import os
from grid import Grid, GridType
from tile import Tile
from hub import Hub

from electrode import Electrode


class ChipSection():
    def __init__(self, start_point: list, width: int, height: int, unit: float, radius: float):
        self.start_point = start_point
        self.width = width
        self.height = height
        self.unit = unit
        self.redius = radius
        self.grid: List[List[Grid]] = []
        self.tile: List[List[Tile]] = []
        self.hub: List[Hub] = []

    def init_grid(self, grid_type=GridType.GRID):
        self.grid = []
        for i in range(self.width // self.unit + 1):
            self.grid.append([])
            for j in range(self.height // self.unit + 1):
                self.grid[i].append(Grid(i * self.unit + self.start_point[0], j * self.unit + self.start_point[1], i, j, grid_type))

    def init_tile(self):
        self.tile = []
        for i in range(self.width // self.unit):
            self.tile.append([])
            for j in range(self.height // self.unit):
                self.tile[i].append(Tile(i * self.unit + self.start_point[0] + (self.unit / 2),
                                    j * self.unit + self.start_point[1] + (self.unit / 2), i, j))

    def init_hub(self, y: float):
        self.hub = []
        for i in range((self.width // self.unit) + 2 * (self.width // self.unit - 1)):
            if i % 3 == 0:
                # grid
                self.hub.append(Hub(self.grid[i//3][0].real_x, y, 0, i))
            else:
                # tile
                offset = i % 3
                self.hub.append(Hub(self.grid[i//3][0].real_x + offset * (self.unit / 3), y, 1, i))
