from typing import Union

from chip import ChipSection
from config import WireDirect
from electrode import Electrode
from grid import Grid, GridType, NeighborNode, PseudoNodeType
from hub import Hub
from pseudo_node import PseudoNode
from tile import Tile


class ModelMesh():
    def __init__(self, top_section: ChipSection, mid_section: ChipSection, bottom_section: ChipSection, pseudo_node: PseudoNode):

        self.top_section = top_section
        self.mid_section = mid_section
        self.bottom_section = bottom_section

        self.pseudo_node = pseudo_node

        self.num_electrode = 0

        self.covered_grid_head_list: list[Grid] = []

        self.electrodes: list[Electrode] = []

    def get_pseudo_node(self):
        self.covered_grid_head_list, self.electrodes = self.pseudo_node.internal_node()

    def add_grid_to_neighbor(self, grid: Grid, neighbor_grid: Grid, capacity: float, cost: float):
        if neighbor_grid.close_electrode is False and neighbor_grid.type == GridType.GRID:
            grid.neighbor.append(NeighborNode(neighbor_grid, capacity, cost))

    def create_pseudo_node_connection(self):
        """
            create the edge from pseudo node to grid closest electrode
        """
        for electrode in self.electrodes:
            for pseudo_node_index, pseudo_node in enumerate(electrode.pseudo_node_set):
                # no edge grid
                if self.mid_section.is_edge_grid(pseudo_node[0], pseudo_node[1]):
                    continue

                pseudo_node_grid = self.mid_section.get_grid(pseudo_node[0], pseudo_node[1])

                # next_pseudo_point = electrode.pseudo_node_set[(pseudo_node_index + 1) % len(electrode.pseudo_node_set)]
                # previous_pseudo_point = electrode.pseudo_node_set[pseudo_node_index - 1]

                # pseudo_node_grid.neighbor.append([self.mid_section.grid[next_pseudo_point[0]][next_pseudo_point[1]], 1, 0])
                # pseudo_node_grid.neighbor.append([self.mid_section.grid[previous_pseudo_point[0]][previous_pseudo_point[1]], 1, 0])

                edge_direct = pseudo_node_grid.edge_direct
                elec_neighbor_node_list: list[NeighborNode] = []
                if edge_direct == WireDirect.UP:
                    elec_neighbor_node_list.append(NeighborNode(self.mid_section.grid[pseudo_node[0]-1][pseudo_node[1]], 1, self.mid_section.unit))
                elif edge_direct == WireDirect.RIGHT:
                    elec_neighbor_node_list.append(NeighborNode(self.mid_section.grid[pseudo_node[0]][pseudo_node[1]-1], 1, self.mid_section.unit))
                elif edge_direct == WireDirect.BOTTOM:
                    elec_neighbor_node_list.append(NeighborNode(self.mid_section.grid[pseudo_node[0]+1][pseudo_node[1]], 1, self.mid_section.unit))
                elif edge_direct == WireDirect.LEFT:
                    elec_neighbor_node_list.append(NeighborNode(self.mid_section.grid[pseudo_node[0]][pseudo_node[1]+1], 1, self.mid_section.unit))
                elif edge_direct == WireDirect.TOP_RIGHT:
                    elec_neighbor_node_list.append(NeighborNode(self.mid_section.grid[pseudo_node[0]][pseudo_node[1]-1], 1, self.mid_section.unit))
                    # only all near grid is pseudo node or grid need to add connection
                    near_grid_type = (self.mid_section.get_grid(pseudo_node[0] - 1, pseudo_node[1]).type,
                                      self.mid_section.get_grid(pseudo_node[0], pseudo_node[1] - 1).type)
                    if near_grid_type in [(GridType.PSEUDO_NODE, GridType.PSEUDO_NODE), (GridType.GRID, GridType.GRID)]:
                        elec_neighbor_node_list.append(NeighborNode(self.mid_section.grid[pseudo_node[0]-1][pseudo_node[1]-1], 1, self.mid_section.hypo_unit))
                    else:
                        pass
                    elec_neighbor_node_list.append(NeighborNode(self.mid_section.grid[pseudo_node[0]-1][pseudo_node[1]], 1, self.mid_section.unit))
                elif edge_direct == WireDirect.BOTTOM_RIGHT:
                    elec_neighbor_node_list.append(NeighborNode(self.mid_section.grid[pseudo_node[0]][pseudo_node[1]-1], 1, self.mid_section.unit))
                    # only all near grid is pseudo node or grid need to add connection
                    near_grid_type = (self.mid_section.get_grid(pseudo_node[0] + 1, pseudo_node[1]).type,
                                      self.mid_section.get_grid(pseudo_node[0], pseudo_node[1] - 1).type)
                    if near_grid_type in [(GridType.PSEUDO_NODE, GridType.PSEUDO_NODE), (GridType.GRID, GridType.GRID)]:
                        elec_neighbor_node_list.append(NeighborNode(self.mid_section.grid[pseudo_node[0]+1][pseudo_node[1]-1], 1, self.mid_section.hypo_unit))
                    else:
                        pass
                    elec_neighbor_node_list.append(NeighborNode(self.mid_section.grid[pseudo_node[0]+1][pseudo_node[1]], 1, self.mid_section.unit))
                elif edge_direct == WireDirect.TOP_LEFT:
                    elec_neighbor_node_list.append(NeighborNode(self.mid_section.grid[pseudo_node[0]-1][pseudo_node[1]], 1, self.mid_section.unit))
                    # only all near grid is pseudo node or grid need to add connection
                    near_grid_type = (self.mid_section.get_grid(pseudo_node[0] - 1, pseudo_node[1]).type,
                                      self.mid_section.get_grid(pseudo_node[0], pseudo_node[1] + 1).type)
                    if near_grid_type in [(GridType.PSEUDO_NODE, GridType.PSEUDO_NODE), (GridType.GRID, GridType.GRID)]:
                        elec_neighbor_node_list.append(NeighborNode(self.mid_section.grid[pseudo_node[0]-1][pseudo_node[1]+1], 1, self.mid_section.hypo_unit))
                    else:
                        pass
                    elec_neighbor_node_list.append(NeighborNode(self.mid_section.grid[pseudo_node[0]][pseudo_node[1]+1], 1, self.mid_section.unit))
                elif edge_direct == WireDirect.BOTTOM_LEFT:
                    elec_neighbor_node_list.append(NeighborNode(self.mid_section.grid[pseudo_node[0]+1][pseudo_node[1]], 1, self.mid_section.unit))
                    # only all near grid is pseudo node or grid need to add connection
                    near_grid_type = (self.mid_section.get_grid(pseudo_node[0] + 1, pseudo_node[1]).type,
                                      self.mid_section.get_grid(pseudo_node[0], pseudo_node[1] + 1).type)
                    if near_grid_type in [(GridType.PSEUDO_NODE, GridType.PSEUDO_NODE), (GridType.GRID, GridType.GRID)]:
                        elec_neighbor_node_list.append(NeighborNode(self.mid_section.grid[pseudo_node[0]+1][pseudo_node[1]+1], 1, self.mid_section.hypo_unit))
                    else:
                        pass
                    elec_neighbor_node_list.append(NeighborNode(self.mid_section.grid[pseudo_node[0]][pseudo_node[1]+1], 1, self.mid_section.unit))

                for neighbor_node in elec_neighbor_node_list:
                    if neighbor_node.grid.type == GridType.GRID:
                        pseudo_node_grid.neighbor.append(neighbor_node)
                        # close_grid[0].neighbor.append([pseudo_node_grid, close_grid[1], close_grid[2]])
                        neighbor_node.grid.close_electrode = True
                        neighbor_node.grid.flow = 1
                        if neighbor_node.cost > self.mid_section.unit:
                            neighbor_node.grid.corner = True
                            neighbor_node.grid.edge_direct = pseudo_node_grid.edge_direct

    def create_grid_connection(self, grid_list: list[list[Grid]], unit, hypo_unit):
        """
            create all edge between each grid and near grid
            # electrode-closed grid only connect to normal grid (GridType.GRID and not close_electrode)
        """
        for grid_x, grid_col in enumerate(grid_list):
            if grid_x == 0:
                for grid_y, grid in enumerate(grid_col):
                    if grid.type == GridType.GRID and grid.pseudo_node_type != PseudoNodeType.INTERNAL:
                        if grid.close_electrode:
                            # add connection from electrode-closed grid to normal grid
                            for x, y in [(0, 1), (0, -1), (1, 1), (1, -1), (1, 0), (-1, 1), (-1, -1), (-1, 0)]:
                                try:
                                    if abs(x + y) != 1:
                                        _unit = hypo_unit
                                    else:
                                        _unit = unit
                                    self.add_grid_to_neighbor(grid, grid_list[grid_x+x][grid_y+y], 1, _unit)
                                except:
                                    pass
                        else:
                            if grid_y == 0:
                                self.add_grid_to_neighbor(grid, grid_list[grid_x + 1][grid_y], 1, unit)
                                self.add_grid_to_neighbor(grid, grid_list[grid_x + 1][grid_y + 1], 1, hypo_unit)
                                self.add_grid_to_neighbor(grid, grid_list[grid_x][grid_y + 1], 1, unit)
                            elif grid_y == len(grid_col) - 1:
                                self.add_grid_to_neighbor(grid, grid_list[grid_x + 1][grid_y], 1, unit)
                                self.add_grid_to_neighbor(grid, grid_list[grid_x + 1][grid_y - 1], 1, hypo_unit)
                                self.add_grid_to_neighbor(grid, grid_list[grid_x][grid_y - 1], 1, unit)
                            else:
                                self.add_grid_to_neighbor(grid, grid_list[grid_x][grid_y - 1], 1, unit)
                                self.add_grid_to_neighbor(grid, grid_list[grid_x + 1][grid_y - 1], 1, hypo_unit)
                                self.add_grid_to_neighbor(grid, grid_list[grid_x + 1][grid_y], 1, unit)
                                self.add_grid_to_neighbor(grid, grid_list[grid_x + 1][grid_y + 1], 1, hypo_unit)
                                self.add_grid_to_neighbor(grid, grid_list[grid_x][grid_y + 1], 1, unit)
            elif grid_x == len(grid_list) - 1:
                for grid_y, grid in enumerate(grid_col):
                    if grid.type == GridType.GRID and grid.pseudo_node_type != PseudoNodeType.INTERNAL:
                        if grid.close_electrode:
                            # add connnection from electrode-closed grid to normal grid
                            for x, y in [(0, 1), (0, -1), (1, 1), (1, -1), (1, 0), (-1, 1), (-1, -1), (-1, 0)]:
                                try:
                                    if abs(x + y) != 1:
                                        _unit = hypo_unit
                                    else:
                                        _unit = unit
                                    self.add_grid_to_neighbor(grid, grid_list[grid_x+x][grid_y+y], 1, _unit)
                                except:
                                    pass
                        else:
                            if grid_y == 0:
                                self.add_grid_to_neighbor(grid, grid_list[grid_x - 1][grid_y], 1, unit)
                                self.add_grid_to_neighbor(grid, grid_list[grid_x - 1][grid_y + 1], 1, hypo_unit)
                                self.add_grid_to_neighbor(grid, grid_list[grid_x][grid_y + 1], 1, unit)
                            elif grid_y == len(grid_col) - 1:
                                self.add_grid_to_neighbor(grid, grid_list[grid_x - 1][grid_y], 1, unit)
                                self.add_grid_to_neighbor(grid, grid_list[grid_x - 1][grid_y - 1], 1, hypo_unit)
                                self.add_grid_to_neighbor(grid, grid_list[grid_x][grid_y - 1], 1, unit)
                            else:
                                self.add_grid_to_neighbor(grid, grid_list[grid_x][grid_y - 1], 1, unit)
                                self.add_grid_to_neighbor(grid, grid_list[grid_x - 1][grid_y - 1], 1, hypo_unit)
                                self.add_grid_to_neighbor(grid, grid_list[grid_x - 1][grid_y], 1, unit)
                                self.add_grid_to_neighbor(grid, grid_list[grid_x - 1][grid_y + 1], 1, hypo_unit)
                                self.add_grid_to_neighbor(grid, grid_list[grid_x][grid_y + 1], 1, unit)
            else:
                for grid_y, grid in enumerate(grid_col):
                    if grid.type == GridType.GRID and grid.pseudo_node_type != PseudoNodeType.INTERNAL:
                        if grid.close_electrode:
                            # add connnection from electrode-closed grid to normal grid
                            for x, y in [(0, 1), (0, -1), (1, 1), (1, -1), (1, 0), (-1, 1), (-1, -1), (-1, 0)]:
                                try:
                                    if abs(x + y) != 1:
                                        _unit = hypo_unit
                                    else:
                                        _unit = unit
                                    self.add_grid_to_neighbor(grid, grid_list[grid_x+x][grid_y+y], 1, _unit)
                                except:
                                    pass
                        else:
                            if grid_y == 0:
                                self.add_grid_to_neighbor(grid, grid_list[grid_x - 1][grid_y], 1, unit)
                                self.add_grid_to_neighbor(grid, grid_list[grid_x - 1][grid_y + 1], 1, hypo_unit)
                                self.add_grid_to_neighbor(grid, grid_list[grid_x][grid_y + 1], 1, unit)
                                self.add_grid_to_neighbor(grid, grid_list[grid_x + 1][grid_y + 1], 1, hypo_unit)
                                self.add_grid_to_neighbor(grid, grid_list[grid_x + 1][grid_y], 1, unit)
                            elif grid_y == len(grid_col) - 1:
                                self.add_grid_to_neighbor(grid, grid_list[grid_x - 1][grid_y], 1, unit)
                                self.add_grid_to_neighbor(grid, grid_list[grid_x - 1][grid_y - 1], 1, hypo_unit)
                                self.add_grid_to_neighbor(grid, grid_list[grid_x][grid_y - 1], 1, unit)
                                self.add_grid_to_neighbor(grid, grid_list[grid_x + 1][grid_y - 1], 1, hypo_unit)
                                self.add_grid_to_neighbor(grid, grid_list[grid_x + 1][grid_y], 1, unit)
                            else:
                                self.add_grid_to_neighbor(grid, grid_list[grid_x - 1][grid_y], 1, unit)
                                self.add_grid_to_neighbor(grid, grid_list[grid_x + 1][grid_y - 1], 1, hypo_unit)
                                self.add_grid_to_neighbor(grid, grid_list[grid_x - 1][grid_y + 1], 1, hypo_unit)
                                self.add_grid_to_neighbor(grid, grid_list[grid_x - 1][grid_y - 1], 1, hypo_unit)
                                self.add_grid_to_neighbor(grid, grid_list[grid_x + 1][grid_y], 1, unit)
                                self.add_grid_to_neighbor(grid, grid_list[grid_x + 1][grid_y + 1], 1, hypo_unit)
                                self.add_grid_to_neighbor(grid, grid_list[grid_x][grid_y + 1], 1, unit)
                                self.add_grid_to_neighbor(grid, grid_list[grid_x][grid_y - 1], 1, unit)

        # for covered_grid in self.covered_grid_head_list:
        #     for grid_neighbor in covered_grid.neighbor:
        #         grid_neighbor[0].covered = True

        # for electrode in self.electrodes:
        #     for point in electrode.pseudo_node_set:
        #         pseudo_node = self.mid_section.grid[point[0]][point[1]]
        #         edge = 0
        #         for near in pseudo_node.neighbor:
        #             edge += len(near[0].neighbor)
        #         if edge == 0:
        #             pseudo_node.covered = True

    def create_tile_connection(self, grid_list: list[list[Grid]], tile_array: list[list[Tile]], block: str):
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
                        if grid_list[k][l].type == GridType.CONTACT_PAD:
                            if block == 'top' and l == len(tile_col):
                                pass
                            elif block == 'bottom' and l == 0:
                                pass
                            else:
                                tile.contact_pads.append(grid_list[k][l])
                            if k == tile_x and l == tile_y:
                                capacity = [2, 2, 2, 2]
                            elif k == tile_x and l == tile_y+1:
                                capacity[3] = 2
                            elif k == tile_x+1 and l == tile_y:
                                capacity[2] = 2
                if tile_x != 0:
                    tile.neighbor.append(NeighborNode(tile_array[tile_x-1][tile_y], capacity[0]))  # left
                if tile_x != len(tile_array) - 1:
                    tile.neighbor.append(NeighborNode(tile_array[tile_x+1][tile_y], capacity[2]))  # right
                if tile_y != 0:
                    tile.neighbor.append(NeighborNode(tile_array[tile_x][tile_y-1], capacity[1]))  # top
                if tile_y != len(tile_col) - 1:
                    tile.neighbor.append(NeighborNode(tile_array[tile_x][tile_y+1], capacity[3]))  # bottom

    def create_hub_connection(self, grid_list: list[list[Grid]], hub_array: list[Hub], mid_n, tile_n, tile_array: list[list[Tile]]):
        """
            mid_grid connect to hub, hub connect to tile
        """
        mid_grid_list: list[list[Grid]] = self.mid_section.grid
        for i in range(len(hub_array)):
            if i % 5 == 0:
                hub_array[i].neighbor.append(NeighborNode(grid_list[i//5][tile_n], 1, 1819))
            else:
                hub_array[i].neighbor.append(NeighborNode(tile_array[i//5][tile_n], 1, 3117))

        grid_index = 0
        for i in range(len(hub_array) - 1):
            if i == 0:
                x = hub_array[i].real_x - self.pseudo_node.unit
                if grid_index < len(self.mid_section.grid) - 1:
                    while self.mid_section.get_grid(grid_index, mid_n).real_x < x:
                        grid_index += 1
            x = (hub_array[i].real_x + hub_array[i+1].real_x) / 2
            if grid_index < len(mid_grid_list) - 1:
                while self.mid_section.get_grid(grid_index, mid_n).real_x < x:
                    self.mid_section.get_grid(grid_index, mid_n).neighbor.append(NeighborNode(hub_array[i], 1, 1819))
                    grid_index += 1
                    if grid_index > len(mid_grid_list) - 1:
                        break

        last_connect_number = 0
        while last_connect_number < 3 and grid_index < len(mid_grid_list):
            self.mid_section.get_grid(grid_index, mid_n).neighbor.append(NeighborNode(hub_array[-1], 1, 1819))
            grid_index += 1
            last_connect_number += 1
