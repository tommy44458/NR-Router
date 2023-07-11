from typing import Union

from model.model_mesh import ModelMesh
from node.electrode import Electrode
from node.grid import Grid, GridType
from node.hub import Hub
from node.tile import Tile


class ModelFlow():
    """Model flow class.
    """
    def __init__(self, mesh: ModelMesh):
        self.mesh = mesh
        self.flownodes: list[Union[int, Grid, Hub, Tile, Electrode]] = []
        self.node_index: int = 0
        self.global_t: Tile = Tile()

    def setup(self):
        self.create_all_flownode()

    def create_grid_flownode(self, grid_list: list[list[Grid]]):
        """Create flownode for grids.

        Args:
            grid_list (list[list[Grid]]): grid list
        """
        for grid_col in grid_list:
            for grid in grid_col:
                if grid.covered == False:
                    grid.index = self.node_index
                    self.node_index += 1
                    self.flownodes.append(grid)
                    # add connect pad end node
                    if grid.type == GridType.CONTACT_PAD:
                        self.global_t.contact_pads.append(grid)
                    elif grid.type == GridType.GRID or grid.type == GridType.PSEUDO_NODE:
                        self.node_index += 1
                        self.flownodes.append(0)

    def create_tile_flownode(self, tile_list: list[list[Tile]]):
        """Create flownode for tiles.

        Args:
            tile_list (list[list[Tile]]): tile list
        """
        for tile_col in tile_list:
            for tile in tile_col:
                tile.index = self.node_index
                self.node_index += 1
                self.flownodes.append(tile)
                self.node_index += 1
                self.flownodes.append(0)

    def create_hub_flownode(self, hub_list: list[Hub]):
        """Create flownode for hubs.

        Args:
            hub_list (list[Hub]): hub list
        """
        for hub in hub_list:
            hub.index = self.node_index
            self.node_index += 1
            self.flownodes.append(hub)

    def create_electrode_flownode(self, electrode_list: list[Electrode]):
        """Create flownode for electrodes.

        Args:
            electrode_list (list[Electrode]): electrode list
        """
        for electrode in electrode_list:
            electrode.index = self.node_index
            self.node_index += 1
            self.flownodes.append(electrode)

    def create_all_flownode(self):
        """Create flownode for all nodes.
        """
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
