import numpy as np
from typing import Any, Optional, Tuple, Union, List, Dict, Callable, NoReturn
import math
from time import time

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
        """
            create the edge between pseudo node and grid closest electrode
        """
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

    def create_grid_connection(self, grid_array: List[List[Grid]], unit):
        for grid_x, grid_col in enumerate(grid_array):
            if grid_x == 0:
                for grid_y, grid in enumerate(grid_col):
                    if grid_y == 0:
                        grid.neighbor.append([grid_array[grid_x + 1][grid_y], 1, unit])
                        grid.neighbor.append([grid_array[grid_x + 1][grid_y + 1], 1, unit*1.5])
                        grid.neighbor.append([grid_array[grid_x][grid_y + 1], 1, unit])
                    elif grid_y == len(grid_col) - 1:
                        grid.neighbor.append([grid_array[grid_x + 1][grid_y], 1, unit])
                        grid.neighbor.append([grid_array[grid_x + 1][grid_y - 1], 1, unit*1.5])
                        grid.neighbor.append([grid_array[grid_x][grid_y - 1], 1, unit])
                    else:
                        grid.neighbor.append([grid_array[grid_x][grid_y - 1], 1, unit])
                        grid.neighbor.append([grid_array[grid_x + 1][grid_y - 1], 1, unit*1.5])
                        grid.neighbor.append([grid_array[grid_x + 1][grid_y], 1, unit])
                        grid.neighbor.append([grid_array[grid_x + 1][grid_y + 1], 1, unit*1.5])
                        grid.neighbor.append([grid_array[grid_x][grid_y + 1], 1, unit])
            elif grid_x == len(grid_array) - 1:
                for grid_y, grid in enumerate(grid_col):
                    if grid_y == 0:
                        grid.neighbor.append([grid_array[grid_x - 1][grid_y], 1, unit])
                        grid.neighbor.append([grid_array[grid_x - 1][grid_y + 1], 1, unit*1.5])
                        grid.neighbor.append([grid_array[grid_x][grid_y + 1], 1, unit])
                    elif grid_y == len(grid_col) - 1:
                        grid.neighbor.append([grid_array[grid_x - 1][grid_y], 1, unit])
                        grid.neighbor.append([grid_array[grid_x - 1][grid_y - 1], 1, unit*1.5])
                        grid.neighbor.append([grid_array[grid_x][grid_y - 1], 1, unit])
                    else:
                        grid.neighbor.append([grid_array[grid_x][grid_y - 1], 1, unit])
                        grid.neighbor.append([grid_array[grid_x - 1][grid_y - 1], 1, unit*1.5])
                        grid.neighbor.append([grid_array[grid_x - 1][grid_y], 1, unit])
                        grid.neighbor.append([grid_array[grid_x - 1][grid_y + 1], 1, unit*1.5])
                        grid.neighbor.append([grid_array[grid_x][grid_y + 1], 1, unit])
            else:
                for grid_y, grid in enumerate(grid_col):
                    if grid_y == 0:
                        grid.neighbor.append([grid_array[grid_x - 1][grid_y], 1, unit])
                        grid.neighbor.append([grid_array[grid_x - 1][grid_y + 1], 1, unit*1.5])
                        grid.neighbor.append([grid_array[grid_x][grid_y + 1], 1, unit])
                        grid.neighbor.append([grid_array[grid_x + 1][grid_y + 1], 1, unit*1.5])
                        grid.neighbor.append([grid_array[grid_x + 1][grid_y], 1, unit])
                    elif grid_y == len(grid_col) - 1:
                        grid.neighbor.append([grid_array[grid_x - 1][grid_y], 1, unit])
                        grid.neighbor.append([grid_array[grid_x - 1][grid_y - 1], 1, unit*1.5])
                        grid.neighbor.append([grid_array[grid_x][grid_y - 1], 1, unit])
                        grid.neighbor.append([grid_array[grid_x + 1][grid_y - 1], 1, unit*1.5])
                        grid.neighbor.append([grid_array[grid_x + 1][grid_y], 1, unit])
                    else:
                        grid.neighbor.append([grid_array[grid_x - 1][grid_y], 1, unit])
                        grid.neighbor.append([grid_array[grid_x + 1][grid_y - 1], 1, unit*1.5])
                        grid.neighbor.append([grid_array[grid_x - 1][grid_y + 1], 1, unit*1.5])
                        grid.neighbor.append([grid_array[grid_x - 1][grid_y - 1], 1, unit*1.5])
                        grid.neighbor.append([grid_array[grid_x + 1][grid_y], 1, unit])
                        grid.neighbor.append([grid_array[grid_x + 1][grid_y + 1], 1, unit*1.5])
                        grid.neighbor.append([grid_array[grid_x][grid_y + 1], 1, unit])
                        grid.neighbor.append([grid_array[grid_x][grid_y - 1], 1, unit])

    def create_tile_connection(self, grid_array: List[List[Grid]], tile_array: List[List[Tile]], block: str):
        """
            tile append near contactpad, tile connnect to near tile
        """
        for tile_x, tile_col in enumerate(tile_array):
            for tile_y, tile in enumerate(tile_col):
                # [u, l, d, r]
                capacity = [8, 8, 8, 8]
                for k in (tile_x, tile_x+1):
                    for l in (tile_y, tile_y+1):
                        # contact pad
                        if grid_array[k][l].type == GridType.CONTACTPAD:
                            if grid_array[k][l].special == False:
                                if block == 'top' and l == len(tile_col):
                                    pass
                                elif block == 'down' and l == 0:
                                    pass
                                else:
                                    tile.contact_pads.append(grid_array[k][l])
                            if k == tile_x and l == tile_y:
                                capacity = [2, 2, 2, 2]
                            elif k == tile_x and l == tile_y+1:
                                capacity[3] = 2
                            elif k == tile_x+1 and l == tile_y:
                                capacity[2] = 2
                if tile_x != 0:
                    tile.neighbor.append([tile_array[tile_x-1][tile_y], capacity[0]])  # left
                if tile_x != len(tile_array) - 1:
                    tile.neighbor.append([tile_array[tile_x+1][tile_y], capacity[2]])  # right
                if tile_y != 0:
                    tile.neighbor.append([tile_array[tile_x][tile_y-1], capacity[1]])  # top
                if tile_y != len(tile_col) - 1:
                    tile.neighbor.append([tile_array[tile_x][tile_y+1], capacity[3]])  # down

    def create_hub_connection(self, grid_array: List[List[Grid]], hub_array: List[Hub], mid_n, tile_n, tile_array: List[List[Tile]]):
        """
            mid_grid connect to hub, hub connect to tile
        """
        mid_grid_array: List[List[Grid]] = self.mid_section.grid
        mid_grid_unit: float = self.mid_section.unit
        for i in range(len(hub_array)):
            left = int((hub_array[i].real_x-self.top_section.start_point[0]) // mid_grid_unit)
            right = int((hub_array[i].real_x-self.top_section.start_point[0]) // mid_grid_unit+1)
            if i % 3 == 0:
                if (hub_array[i].real_x - mid_grid_array[left][mid_n].real_x) > (mid_grid_unit/2):
                    near = right
                else:
                    near = left
                if grid_array[i//3][tile_n].special == False:
                    mid_grid_array[near][mid_n].neighbor.append([hub_array[i], 1, 1819])
                    hub_array[i].neighbor.append([grid_array[i//3][tile_n], 1, 1819])
            elif i % 3 == 1:
                if abs(mid_grid_array[right][mid_n].real_x - hub_array[i].real_x) > abs(mid_grid_array[left][mid_n].real_x - hub_array[i].real_x):
                    mid_grid_array[left][mid_n].neighbor.append([hub_array[i], 1, 1819])
                else:
                    mid_grid_array[right][mid_n].neighbor.append([hub_array[i], 1, 1819])
                hub_array[i].neighbor.append([tile_array[i//3][tile_n], 1, 3117])
            else:
                if abs(hub_array[i].real_x - mid_grid_array[left][mid_n].real_x) > abs(hub_array[i].real_x - mid_grid_array[right][mid_n].real_x):
                    mid_grid_array[right][mid_n].neighbor.append([hub_array[i], 1, 1819])
                else:
                    mid_grid_array[left][mid_n].neighbor.append([hub_array[i], 1, 1819])
                hub_array[i].neighbor.append([tile_array[i//3][tile_n], 1, 3117])
