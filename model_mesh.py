from typing import Any, Optional, Tuple, Union, List, Dict, Callable, NoReturn
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

    def get_pseudo_node(self):
        self.electrodes = self.pesudo_node.internal_node()

    def add_grid_to_neighbor(self, grid: Grid, neighbor_grid: Grid, capacity: float, cost: float):
        if neighbor_grid.close_electrode is False and neighbor_grid.type == GridType.GRID:
            grid.neighbor.append([neighbor_grid, capacity, cost])

    def create_pseudo_node_connection(self):
        """
            create the edge from pseudo node to grid closest electrode
        """
        for electrode in self.electrodes:
            for pseudo_node_index, pseudo_node in enumerate(electrode.pseudo_node_set):
                # no closed grid
                if pseudo_node[0] == len(self.mid_section.grid) or pseudo_node[1] == len(self.mid_section.grid[0]):
                    continue
                if pseudo_node[0] == 0 or pseudo_node[1] == 0:
                    continue

                pseudo_node_grid = self.mid_section.grid[pseudo_node[0]][pseudo_node[1]]

                # next_pseudo_point = electrode.pseudo_node_set[(pseudo_node_index + 1) % len(electrode.pseudo_node_set)]
                # previous_pseudo_point = electrode.pseudo_node_set[pseudo_node_index - 1]

                # pseudo_node_grid.neighbor.append([self.mid_section.grid[next_pseudo_point[0]][next_pseudo_point[1]], 1, 0])
                # pseudo_node_grid.neighbor.append([self.mid_section.grid[previous_pseudo_point[0]][previous_pseudo_point[1]], 1, 0])

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
                    # only all near grid is pseudo node or grid need to add connection
                    near_grid_type = (self.mid_section.grid[pseudo_node[0]-1][pseudo_node[1]].type,
                                      self.mid_section.grid[pseudo_node[0]][pseudo_node[1]-1].type)
                    if near_grid_type in [(GridType.PSEUDONODE, GridType.PSEUDONODE), (GridType.GRID, GridType.GRID)]:
                        close_elec_grid_list.append([self.mid_section.grid[pseudo_node[0]-1][pseudo_node[1]-1], 1, self.mid_section.hypo_unit])
                    else:
                        pass
                    close_elec_grid_list.append([self.mid_section.grid[pseudo_node[0]-1][pseudo_node[1]], 1, self.mid_section.unit])
                elif edge_direct == WireDirect.RIGHTDOWN:
                    close_elec_grid_list.append([self.mid_section.grid[pseudo_node[0]][pseudo_node[1]-1], 1, self.mid_section.unit])
                    # only all near grid is pseudo node or grid need to add connection
                    near_grid_type = (self.mid_section.grid[pseudo_node[0]+1][pseudo_node[1]].type,
                                      self.mid_section.grid[pseudo_node[0]][pseudo_node[1]-1].type)
                    if near_grid_type in [(GridType.PSEUDONODE, GridType.PSEUDONODE), (GridType.GRID, GridType.GRID)]:
                        close_elec_grid_list.append([self.mid_section.grid[pseudo_node[0]+1][pseudo_node[1]-1], 1, self.mid_section.hypo_unit])
                    else:
                        pass
                    close_elec_grid_list.append([self.mid_section.grid[pseudo_node[0]+1][pseudo_node[1]], 1, self.mid_section.unit])
                elif edge_direct == WireDirect.LEFTUP:
                    close_elec_grid_list.append([self.mid_section.grid[pseudo_node[0]-1][pseudo_node[1]], 1, self.mid_section.unit])
                    # only all near grid is pseudo node or grid need to add connection
                    near_grid_type = (self.mid_section.grid[pseudo_node[0]-1][pseudo_node[1]].type,
                                      self.mid_section.grid[pseudo_node[0]][pseudo_node[1]+1].type)
                    if near_grid_type in [(GridType.PSEUDONODE, GridType.PSEUDONODE), (GridType.GRID, GridType.GRID)]:
                        close_elec_grid_list.append([self.mid_section.grid[pseudo_node[0]-1][pseudo_node[1]+1], 1, self.mid_section.hypo_unit])
                    else:
                        pass
                    close_elec_grid_list.append([self.mid_section.grid[pseudo_node[0]][pseudo_node[1]+1], 1, self.mid_section.unit])
                elif edge_direct == WireDirect.LEFTDOWN:
                    close_elec_grid_list.append([self.mid_section.grid[pseudo_node[0]+1][pseudo_node[1]], 1, self.mid_section.unit])
                    # only all near grid is pseudo node or grid need to add connection
                    near_grid_type = (self.mid_section.grid[pseudo_node[0]+1][pseudo_node[1]].type,
                                      self.mid_section.grid[pseudo_node[0]][pseudo_node[1]+1].type)
                    if near_grid_type in [(GridType.PSEUDONODE, GridType.PSEUDONODE), (GridType.GRID, GridType.GRID)]:
                        close_elec_grid_list.append([self.mid_section.grid[pseudo_node[0]+1][pseudo_node[1]+1], 1, self.mid_section.hypo_unit])
                    else:
                        pass
                    close_elec_grid_list.append([self.mid_section.grid[pseudo_node[0]][pseudo_node[1]+1], 1, self.mid_section.unit])

                for close_grid in close_elec_grid_list:
                    if close_grid[0].type == GridType.GRID:
                        pseudo_node_grid.neighbor.append(close_grid)
                        # close_grid[0].neighbor.append([pseudo_node_grid, close_grid[1], close_grid[2]])
                        close_grid[0].close_electrode = True
                        if close_grid[2] > self.mid_section.unit:
                            close_grid[0].corner = True
                            close_grid[0].edge_direct = pseudo_node_grid.edge_direct

    def create_grid_connection(self, grid_array: List[List[Grid]], unit, hypo_unit):
        """
            create all edge between each grid and near grid
            # electrode-closed grid only connect to normal grid (GridType.GRID and not close_electrode)
        """
        for grid_x, grid_col in enumerate(grid_array):
            if grid_x == 0:
                for grid_y, grid in enumerate(grid_col):
                    if grid.type == GridType.GRID and grid.covered is False:
                        if grid.close_electrode:
                            # add connnection from electrode-closed grid to normal grid
                            for x, y in [(0, 1), (0, -1), (1, 1), (1, -1), (1, 0), (-1, 1), (-1, -1), (-1, 0)]:
                                try:
                                    if abs(x + y) != 1:
                                        _unit = hypo_unit
                                    else:
                                        _unit = unit
                                    self.add_grid_to_neighbor(grid, grid_array[grid_x+x][grid_y+y], 1, _unit)
                                except:
                                    pass
                        else:
                            if grid_y == 0:
                                self.add_grid_to_neighbor(grid, grid_array[grid_x + 1][grid_y], 1, unit)
                                self.add_grid_to_neighbor(grid, grid_array[grid_x + 1][grid_y + 1], 1, hypo_unit)
                                self.add_grid_to_neighbor(grid, grid_array[grid_x][grid_y + 1], 1, unit)
                            elif grid_y == len(grid_col) - 1:
                                self.add_grid_to_neighbor(grid, grid_array[grid_x + 1][grid_y], 1, unit)
                                self.add_grid_to_neighbor(grid, grid_array[grid_x + 1][grid_y - 1], 1, hypo_unit)
                                self.add_grid_to_neighbor(grid, grid_array[grid_x][grid_y - 1], 1, unit)
                            else:
                                self.add_grid_to_neighbor(grid, grid_array[grid_x][grid_y - 1], 1, unit)
                                self.add_grid_to_neighbor(grid, grid_array[grid_x + 1][grid_y - 1], 1, hypo_unit)
                                self.add_grid_to_neighbor(grid, grid_array[grid_x + 1][grid_y], 1, unit)
                                self.add_grid_to_neighbor(grid, grid_array[grid_x + 1][grid_y + 1], 1, hypo_unit)
                                self.add_grid_to_neighbor(grid, grid_array[grid_x][grid_y + 1], 1, unit)
            elif grid_x == len(grid_array) - 1:
                for grid_y, grid in enumerate(grid_col):
                    if grid.type == GridType.GRID and grid.covered is False:
                        if grid.close_electrode:
                            # add connnection from electrode-closed grid to normal grid
                            for x, y in [(0, 1), (0, -1), (1, 1), (1, -1), (1, 0), (-1, 1), (-1, -1), (-1, 0)]:
                                try:
                                    if abs(x + y) != 1:
                                        _unit = hypo_unit
                                    else:
                                        _unit = unit
                                    self.add_grid_to_neighbor(grid, grid_array[grid_x+x][grid_y+y], 1, _unit)
                                except:
                                    pass
                        else:
                            if grid_y == 0:
                                self.add_grid_to_neighbor(grid, grid_array[grid_x - 1][grid_y], 1, unit)
                                self.add_grid_to_neighbor(grid, grid_array[grid_x - 1][grid_y + 1], 1, hypo_unit)
                                self.add_grid_to_neighbor(grid, grid_array[grid_x][grid_y + 1], 1, unit)
                            elif grid_y == len(grid_col) - 1:
                                self.add_grid_to_neighbor(grid, grid_array[grid_x - 1][grid_y], 1, unit)
                                self.add_grid_to_neighbor(grid, grid_array[grid_x - 1][grid_y - 1], 1, hypo_unit)
                                self.add_grid_to_neighbor(grid, grid_array[grid_x][grid_y - 1], 1, unit)
                            else:
                                self.add_grid_to_neighbor(grid, grid_array[grid_x][grid_y - 1], 1, unit)
                                self.add_grid_to_neighbor(grid, grid_array[grid_x - 1][grid_y - 1], 1, hypo_unit)
                                self.add_grid_to_neighbor(grid, grid_array[grid_x - 1][grid_y], 1, unit)
                                self.add_grid_to_neighbor(grid, grid_array[grid_x - 1][grid_y + 1], 1, hypo_unit)
                                self.add_grid_to_neighbor(grid, grid_array[grid_x][grid_y + 1], 1, unit)
            else:
                for grid_y, grid in enumerate(grid_col):
                    if grid.type == GridType.GRID and grid.covered is False:
                        if grid.close_electrode:
                            # add connnection from electrode-closed grid to normal grid
                            for x, y in [(0, 1), (0, -1), (1, 1), (1, -1), (1, 0), (-1, 1), (-1, -1), (-1, 0)]:
                                try:
                                    if abs(x + y) != 1:
                                        _unit = hypo_unit
                                    else:
                                        _unit = unit
                                    self.add_grid_to_neighbor(grid, grid_array[grid_x+x][grid_y+y], 1, _unit)
                                except:
                                    pass
                        else:
                            if grid_y == 0:
                                self.add_grid_to_neighbor(grid, grid_array[grid_x - 1][grid_y], 1, unit)
                                self.add_grid_to_neighbor(grid, grid_array[grid_x - 1][grid_y + 1], 1, hypo_unit)
                                self.add_grid_to_neighbor(grid, grid_array[grid_x][grid_y + 1], 1, unit)
                                self.add_grid_to_neighbor(grid, grid_array[grid_x + 1][grid_y + 1], 1, hypo_unit)
                                self.add_grid_to_neighbor(grid, grid_array[grid_x + 1][grid_y], 1, unit)
                            elif grid_y == len(grid_col) - 1:
                                self.add_grid_to_neighbor(grid, grid_array[grid_x - 1][grid_y], 1, unit)
                                self.add_grid_to_neighbor(grid, grid_array[grid_x - 1][grid_y - 1], 1, hypo_unit)
                                self.add_grid_to_neighbor(grid, grid_array[grid_x][grid_y - 1], 1, unit)
                                self.add_grid_to_neighbor(grid, grid_array[grid_x + 1][grid_y - 1], 1, hypo_unit)
                                self.add_grid_to_neighbor(grid, grid_array[grid_x + 1][grid_y], 1, unit)
                            else:
                                self.add_grid_to_neighbor(grid, grid_array[grid_x - 1][grid_y], 1, unit)
                                self.add_grid_to_neighbor(grid, grid_array[grid_x + 1][grid_y - 1], 1, hypo_unit)
                                self.add_grid_to_neighbor(grid, grid_array[grid_x - 1][grid_y + 1], 1, hypo_unit)
                                self.add_grid_to_neighbor(grid, grid_array[grid_x - 1][grid_y - 1], 1, hypo_unit)
                                self.add_grid_to_neighbor(grid, grid_array[grid_x + 1][grid_y], 1, unit)
                                self.add_grid_to_neighbor(grid, grid_array[grid_x + 1][grid_y + 1], 1, hypo_unit)
                                self.add_grid_to_neighbor(grid, grid_array[grid_x][grid_y + 1], 1, unit)
                                self.add_grid_to_neighbor(grid, grid_array[grid_x][grid_y - 1], 1, unit)

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
        for i in range(len(hub_array)):
            if i % 5 == 0:
                if grid_array[i//5][tile_n].special == False:
                    hub_array[i].neighbor.append([grid_array[i//5][tile_n], 1, 1819])
            else:
                hub_array[i].neighbor.append([tile_array[i//5][tile_n], 1, 3117])

        grid_index = 0
        for i in range(len(hub_array) - 1):
            x = (hub_array[i].real_x + hub_array[i+1].real_x) / 2
            if grid_index < len(mid_grid_array) - 1:
                while mid_grid_array[grid_index][mid_n].real_x < x:
                    mid_grid_array[grid_index][mid_n].neighbor.append([hub_array[i], 1, 1819])
                    grid_index += 1
                    if grid_index > len(mid_grid_array) - 1:
                        break

        while grid_index < len(mid_grid_array):
            mid_grid_array[grid_index][mid_n].neighbor.append([hub_array[-1], 1, 1819])
            grid_index += 1
