import numpy as np
from typing import Any, Optional, Tuple, Union, List, Dict, Callable, NoReturn
import math
import sys
import os
from ezdxf.addons import r12writer
from operator import itemgetter, attrgetter
from math import atan2, degrees

from degree import Degree
from grid import Grid, GridType
from tile import Tile
from hub import Hub
from electrode import Electrode
from wire import Wire
from draw import Draw
from model_mesh import ModelMesh


class ModelFlow():

    def __init__(self, mesh: ModelMesh):
        self.mesh = mesh
        self.flownodes: List[Union[int, Grid, Hub, Tile, Electrode]] = []
        self.special_index = []
        self.node_index = 0
        self.global_t = Tile()

    def create_grid_flownode(self, grid_array: List[List[Grid]]):
        for grid_col in grid_array:
            for grid in grid_col:
                grid.index = self.node_index
                self.node_index += 1
                self.flownodes.append(grid)
                # add connect pad end node
                if grid.type == GridType.CONTACTPAD:
                    self.global_t.contact_pads.append(grid)
                elif grid.type == GridType.GRID:
                    self.node_index += 1
                    self.flownodes.append(0)

    def create_tile_flownode(self, tile_array: List[List[Tile]]):
        for tile_col in tile_array:
            for tile in tile_col:
                tile.index = self.node_index
                self.node_index += 1
                self.flownodes.append(tile)
                self.node_index += 1
                self.flownodes.append(0)

    def create_hub_flownode(self, hub_array: List[Hub]):
        for hub in hub_array:
            hub.index = self.node_index
            self.node_index += 1
            self.flownodes.append(hub)

    def create_electrode_flownode(self, electrode_list: List[Electrode]):
        for electrode in electrode_list:
            electrode.index = self.node_index
            self.node_index += 1
            self.flownodes.append(electrode)

    def create_all_flownode(self):
        self.create_grid_flownode(self.mesh.top_section.grid)
        self.create_grid_flownode(self.mesh.mid_section.grid)
        self.create_grid_flownode(self.mesh.down_section.grid)
        self.create_tile_flownode(self.mesh.top_section.tile)
        self.create_tile_flownode(self.mesh.down_section.tile)
        self.create_hub_flownode(self.mesh.top_section.hub)
        self.create_hub_flownode(self.mesh.down_section.hub)
        self.create_electrode_flownode(self.mesh.electrodes)

        self.global_t.index = self.node_index
        self.flownodes.append(self.global_t)
        self.node_index += 1

    def create_tile_path(self, tile_array: List[List[Tile]], hub_array: List[Hub], start: int, end: int, shift: int, all_path: List[Wire]):
        for tile_x, tile_col in enumerate(tile_array):
            for j in range(start, end, shift):
                for c_node in tile_col[j].corner_in:
                    if c_node.real_x < tile_col[j].real_x:
                        if tile_col[j].flow[0] == 1:
                            all_path.append(Wire(int(hub_array[tile_x*3+1].real_x), int(tile_col[j].real_y), int(c_node.real_x), int(c_node.real_y)))
                            tile_col[j].flow[0] = 0
                        elif tile_col[j].flow[1] == 1:
                            all_path.append(Wire(int(hub_array[tile_x*3+2].real_x), int(tile_col[j].real_y), int(c_node.real_x), int(c_node.real_y)))
                            tile_col[j].flow[1] = 0
                    else:
                        if tile_col[j].flow[1] == 1:
                            all_path.append(Wire(int(hub_array[tile_x*3+2].real_x), int(tile_col[j].real_y), int(c_node.real_x), int(c_node.real_y)))
                            tile_col[j].flow[1] = 0
                        elif tile_col[j].flow[0] == 1:
                            all_path.append(Wire(int(hub_array[tile_x*3+1].real_x), int(tile_col[j].real_y), int(c_node.real_x), int(c_node.real_y)))
                            tile_col[j].flow[0] = 0
                if len(tile_col[j].vertical_path) != 0:
                    if tile_col[j].flow[0] == 1:
                        all_path.append(Wire(int(hub_array[tile_x*3+1].real_x), int(tile_col[j].real_y),
                                        int(hub_array[tile_x*3+1].real_x), int(tile_col[j].vertical_path[0].real_y)))
                        tile_col[j].vertical_path[0].flow[0] = 1
                    if tile_col[j].flow[1] == 1:
                        all_path.append(Wire(int(hub_array[tile_x*3+2].real_x), int(tile_col[j].real_y),
                                        int(hub_array[tile_x*3+2].real_x), int(tile_col[j].vertical_path[0].real_y)))
                        tile_col[j].vertical_path[0].flow[1] = 1
