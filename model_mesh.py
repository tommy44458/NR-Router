import numpy as np
from typing import Any, Optional, Tuple, Union, List, Dict, Callable, NoReturn
import math

from grid import Grid, GridType
from wire import WireDirect
from tile import Tile
from hub import Hub
from electrode import Electrode
from chip_section import ChipSection
from pseudo_node import PseudoNode


class ModelMesh():
    def __init__(self, top_section: ChipSection, mid_section: ChipSection, down_section: ChipSection, pseudo_node: PseudoNode):

        self.top_section = top_section
        self.mid_section = mid_section
        self.down_section = down_section

        self.pesudo_node = pseudo_node

        self.num_electrode = 0

        self.electrodes: List[Electrode] = []
        self.contactpads = []

    def get_pseudo_node(self):
        self.electrodes = self.pesudo_node.internal_node()

    def create_pseudo_node_connection(self):
        for electrode in self.electrodes:
            for pseudo_node in electrode.pseudo_node_set:
                # no closed grid
                if pseudo_node[0] == len(self.mid_section.grid) or pseudo_node[1] == len(self.mid_section.grid[0]):
                    continue
                if pseudo_node[0] == 0 or pseudo_node[1] == 0:
                    continue

                pseudo_node_grid = self.mid_section.grid[pseudo_node[0]][pseudo_node[1]]
                edge_direct = pseudo_node_grid.edge_direct
                close_elec_grid_list: List[List[Union[Grid, int]]] = []
                if edge_direct == WireDirect.UP:
                    close_elec_grid_list.append([self.mid_section.grid[pseudo_node[0]-1][pseudo_node[1]], 1, self.mid_section.unit])
                elif edge_direct == WireDirect.RIGHT:
                    close_elec_grid_list.append([self.mid_section.grid[pseudo_node[0]][pseudo_node[1]-1], 1, self.mid_section.unit])
                elif edge_direct == WireDirect.DOWN:
                    close_elec_grid_list.append([self.mid_section.grid[pseudo_node[0]+1][pseudo_node[1]], 1, self.mid_section.unit])
                elif edge_direct == WireDirect.LEFT:
                    close_elec_grid_list.append([self.mid_section.grid[pseudo_node[0]][pseudo_node[1]+1], 1, self.mid_section.unit])
                elif edge_direct == WireDirect.RIGHTUP:
                    close_elec_grid_list.append([self.mid_section.grid[pseudo_node[0]][pseudo_node[1]-1], 1, self.mid_section.unit])
                    close_elec_grid_list.append([self.mid_section.grid[pseudo_node[0]-1][pseudo_node[1]-1], 1, self.mid_section.unit*1.5])
                    close_elec_grid_list.append([self.mid_section.grid[pseudo_node[0]-1][pseudo_node[1]], 1, self.mid_section.unit])
                elif edge_direct == WireDirect.RIGHTDOWN:
                    close_elec_grid_list.append([self.mid_section.grid[pseudo_node[0]][pseudo_node[1]-1], 1, self.mid_section.unit])
                    close_elec_grid_list.append([self.mid_section.grid[pseudo_node[0]+1][pseudo_node[1]-1], 1, self.mid_section.unit*1.5])
                    close_elec_grid_list.append([self.mid_section.grid[pseudo_node[0]+1][pseudo_node[1]], 1, self.mid_section.unit])
                elif edge_direct == WireDirect.LEFTUP:
                    close_elec_grid_list.append([self.mid_section.grid[pseudo_node[0]-1][pseudo_node[1]], 1, self.mid_section.unit])
                    close_elec_grid_list.append([self.mid_section.grid[pseudo_node[0]-1][pseudo_node[1]+1], 1, self.mid_section.unit*1.5])
                    close_elec_grid_list.append([self.mid_section.grid[pseudo_node[0]][pseudo_node[1]+1], 1, self.mid_section.unit])
                elif edge_direct == WireDirect.LEFTDOWN:
                    close_elec_grid_list.append([self.mid_section.grid[pseudo_node[0]+1][pseudo_node[1]], 1, self.mid_section.unit])
                    close_elec_grid_list.append([self.mid_section.grid[pseudo_node[0]+1][pseudo_node[1]+1], 1, self.mid_section.unit*1.5])
                    close_elec_grid_list.append([self.mid_section.grid[pseudo_node[0]][pseudo_node[1]+1], 1, self.mid_section.unit])

                for close_grid in close_elec_grid_list:
                    if close_grid[0].type == GridType.GRID:
                        close_grid[0].neighbor.append([pseudo_node_grid, close_grid[1], close_grid[2]])
                        close_grid[0].close_electrode = True
        pass
