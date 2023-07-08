from typing import Any, Callable, Dict, List, NoReturn, Optional, Tuple, Union

from electrode import Electrode
from grid import Grid, GridType
from hub import Hub
from model_mesh import ModelMesh
from tile import Tile


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
                if grid.covered == False:
                    grid.index = self.node_index
                    self.node_index += 1
                    self.flownodes.append(grid)
                    # add connect pad end node
                    if grid.type == GridType.CONTACT_PAD:
                        self.global_t.contact_pads.append(grid)
                    elif grid.type == GridType.GRID or grid.type == GridType.PSEUDONODE:
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
        self.create_electrode_flownode(self.mesh.electrodes)
        self.create_grid_flownode(self.mesh.mid_section.grid)
        self.create_hub_flownode(self.mesh.top_section.hub)
        self.create_hub_flownode(self.mesh.bottom_section.hub)
        self.create_tile_flownode(self.mesh.top_section.tile)
        self.create_tile_flownode(self.mesh.bottom_section.tile)
        self.create_grid_flownode(self.mesh.top_section.grid)
        self.create_grid_flownode(self.mesh.bottom_section.grid)

        self.global_t.index = self.node_index
        self.flownodes.append(self.global_t)
        self.node_index += 1
