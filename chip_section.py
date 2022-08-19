import math
import os
from typing import Any, Callable, Dict, List, NoReturn, Optional, Tuple, Union

import numpy as np

from electrode import Electrode
from grid import Grid, GridType
from hub import Hub
from tile import Tile


class ChipSection():
    def __init__(self, start_point: list, width: int, height: int, unit: float, radius: float):
        self.start_point = start_point
        self.width = width
        self.height = height
        self.unit = unit
        self.hypo_unit = int(unit * 2) - 1   # int(unit*2) - 1  # 2 * unit - 1  # unit * math.sqrt(2)
        self.redius = radius
        self.grid: List[List[Grid]] = []
        self.tile: List[List[Tile]] = []
        self.hub: List[Hub] = []
        self.hub_gap = 208

    def init_grid(self, grid_type=GridType.GRID, ref_pin=None):
        self.grid = []
        for i in range(self.width // self.unit + 1):
            self.grid.append([])
            for j in range(self.height // self.unit + 1):
                if ref_pin and [i, j] in ref_pin:
                    self.grid[i].append(Grid(i * self.unit + self.start_point[0], j * self.unit + self.start_point[1], i, j, GridType.REF))
                else:
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
        for i in range((self.width // self.unit) + 4 * (self.width // self.unit - 1) + 5):
            if i % 5 == 0:
                # grid
                self.hub.append(Hub(self.grid[i//5][0].real_x, y, 0, i))
            else:
                # tile
                offset = self.redius + (i % 5) * self.hub_gap
                self.hub.append(Hub(self.grid[i//5][0].real_x + offset, y, 1, i))
