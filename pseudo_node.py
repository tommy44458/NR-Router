import numpy as np
from typing import Any, Optional, Tuple, Union, List, Dict, Callable, NoReturn
import math

from grid import Grid, GridType, PseudoNodeType
from wire import WireDirect
from electrode import Electrode
from degree import Degree, direct_table
from electrode import Electrode


class PseudoNode():

    def __init__(self, grid: List[List[Grid]], shape_lib: dict, start_point: list, unit: float, electrode_list: list):
        self.grid = grid
        self.shape_lib: Dict[str, list] = shape_lib
        self.start_point = start_point
        self.unit = unit
        self.electrode_list: List[list] = electrode_list

    def get_point_by_shape(self, elec_point: list, shape_point: list) -> list:
        """
            elec_p is the top-lsft point in electrode
            shape_p is the point by svg path
        """
        return [elec_point[0] + shape_point[0], elec_point[1] + shape_point[1]]

    def get_grid_point(self, real_point: list, unit: float) -> list:
        """
            get gird point by real point
        """
        return [(real_point[0] - self.start_point[0]) // unit, (real_point[1] - self.start_point[1]) // unit]

    def cal_distance(self, p1: list, p2: list):
        return math.sqrt(math.pow((p2[0] - p1[0]), 2) + math.pow((p2[1] - p1[1]), 2))

    def get_grid_point_list(self, real_point: list, unit: float) -> list:
        """
            get gird point list by real point
        """
        left_up = [int((real_point[0] - self.start_point[0]) // unit), int((real_point[1] - self.start_point[1]) // unit)]
        right_up = [left_up[0] + 1, left_up[1]]
        right_down = [left_up[0] + 1, left_up[1] + 1]
        left_down = [left_up[0], left_up[1] + 1]
        return [left_up, right_up, right_down, left_down]

    def clockwise_angle(self, v1: tuple, v2: tuple) -> float:
        """
            :return angle between 2 points
        """
        x1, y1 = v1
        x2, y2 = v2
        dot = x1 * x2 + y1 * y2
        det = x1 * y2 - y1 * x2
        theta = np.arctan2(det, dot)
        theta = theta if theta > 0 else 2 * np.pi + theta
        return (theta * 180 / np.pi)

    def set_electrode_to_grid(self, point: list, elec_index: int, elec_point: list,
                              pseudo_node_type: PseudoNodeType, corner: bool = False,
                              edge_direct: WireDirect = 0):
        """
            set electrode info to grid
        """
        x = point[0]
        y = point[1]
        if self.grid[x][y].corner is False:
            self.grid[x][y].electrode_index = elec_index
            self.grid[x][y].type = GridType.PSEUDONODE
            self.grid[x][y].flow = 1
            self.grid[x][y].electrode_x = elec_point[0]
            self.grid[x][y].electrode_y = elec_point[1]
            self.grid[x][y].corner = corner
            self.grid[x][y].pseudo_node_type = pseudo_node_type
            self.grid[x][y].edge_direct = edge_direct

    def is_poi_with_in_poly(self, poi: list, poly: list):
        """
            check point is in poly
        """
        # 輸入：點，多邊形二維陣列
        # poly=[[x1,y1],[x2,y2],……,[xn,yn],[x1,y1]] 二維陣列
        sinsc = 0  # 交點個數
        for i in range(len(poly)-1):  # [0,len-1]
            s_poi = poly[i]
            e_poi = poly[i+1]
            if self.is_ray_intersects_segment(poi, s_poi, e_poi):
                sinsc += 1  # 有交點就加1

        return True if sinsc % 2 == 1 else False

    def is_ray_intersects_segment(self, poi: list, s_poi: list, e_poi: list):  # [x,y] [lng,lat]
        # 輸入：判斷點，邊起點，邊終點，都是[lng,lat]格式陣列
        if s_poi[1] == e_poi[1]:  # 排除與射線平行、重合，線段首尾端點重合的情況
            return False
        if s_poi[1] > poi[1] and e_poi[1] > poi[1]:  # 線段在射線上邊
            return False
        if s_poi[1] < poi[1] and e_poi[1] < poi[1]:  # 線段在射線下邊
            return False
        if s_poi[1] == poi[1] and e_poi[1] > poi[1]:  # 交點為下端點，對應spoint
            return False
        if e_poi[1] == poi[1] and s_poi[1] > poi[1]:  # 交點為下端點，對應epoint
            return False
        if s_poi[0] < poi[0] and e_poi[1] < poi[1]:  # 線段在射線左邊
            return False

        xseg = e_poi[0]-(e_poi[0]-s_poi[0])*(e_poi[1]-poi[1])/(e_poi[1]-s_poi[1])  # 求交
        if xseg < poi[0]:  # 交點在射線起點的左側
            return False
        return True  # 排除上述情況之後

    def find_short_grid_internal(self, grid: List[List[Grid]], elec_point: list, poly_point_list: list) -> list:
        """
            find the closest gird and inside electrode by a real point
            :return grid index [x, y]
        """
        grid_point_list = self.get_grid_point_list(elec_point, self.unit)
        grid_point_list_internal = []
        for g_p in grid_point_list:
            if self.is_poi_with_in_poly([self.grid[g_p[0]][g_p[1]].real_x, self.grid[g_p[0]][g_p[1]].real_y], poly_point_list):
                grid_point_list_internal.append(g_p)
        return self.find_short_grid_from_points(grid, grid_point_list_internal, elec_point)

    def find_short_grid_from_points(self, grid: List[List[Grid]], grid_point_list: list, elec_p: list):
        """
            find the closest gird by a real point and grid point list
            :return grid index [x, y]
        """
        ps = []
        for grid_p in grid_point_list:
            ps.append([grid[grid_p[0]][grid_p[1]].real_x, grid[grid_p[0]][grid_p[1]].real_y])
        dis = []
        for p in ps:
            dis.append(self.cal_distance(elec_p, p))
        if len(dis) > 0:
            short_p = min(dis)
            index = dis.index(short_p)
            return grid_point_list[index]
        else:
            return None

    def internal_node(self) -> List[Electrode]:
        """
            find all pseudo node for each electrode
        """
        ret: List[Electrode] = []
        covered_grid_list: List[Grid] = []
        for electrode_index, electrode in enumerate(self.electrode_list):
            if electrode[0] in self.shape_lib:
                covered_grid = None
                electrode_x = electrode[1]
                electrode_y = electrode[2]
                electrode_shape_path = self.shape_lib[electrode[0]]
                # get poly vertex list
                poly_points = []
                for j in range(len(electrode_shape_path)-1):
                    p = self.get_point_by_shape([electrode_x, electrode_y], electrode_shape_path[j])
                    poly_points.append(p)
                poly_points.append([poly_points[0][0], poly_points[0][1]])

                boundary_U = electrode_y
                boundary_D = electrode_y
                boundary_L = electrode_x
                boundary_R = electrode_x

                ret.append(Electrode(electrode_x, electrode_y, electrode[0], electrode_index))
                ret[-1].poly = poly_points

                # trace all poly vertex to get pseudo node
                for j in range(len(electrode_shape_path)-1):
                    p1 = self.get_point_by_shape([electrode_x, electrode_y], electrode_shape_path[j])
                    p2 = self.get_point_by_shape([electrode_x, electrode_y], electrode_shape_path[j+1])

                    if p1[0] > boundary_R:
                        boundary_R = p1[0]
                    if p1[0] < boundary_L:
                        boundary_L = p1[0]
                    if p1[1] < boundary_U:
                        boundary_U = p1[1]
                    if p1[1] > boundary_D:
                        boundary_D = p1[1]

                    # vertex in which grid
                    grid_p1 = self.get_grid_point(p1, self.unit)
                    grid_p2 = self.get_grid_point(p2, self.unit)

                    degree_p1_p2 = Degree.getdegree(p1[0], -p1[1], p2[0], -p2[1])

                    if direct_table[degree_p1_p2] == WireDirect.UP:
                        for k in range(grid_p1[1] - (grid_p2[1] + 1) + 1):
                            if covered_grid is None:
                                if self.grid[grid_p1[0]+2][grid_p1[1]-k].pseudo_node_type != PseudoNodeType.INTERNAL:
                                    covered_grid = self.grid[grid_p1[0]+2][grid_p1[1]-k]
                            self.set_electrode_to_grid([grid_p1[0]+1, grid_p1[1]-k], electrode_index,
                                                       [p1[0], self.grid[grid_p1[0]+1][grid_p1[1]-k].real_y],
                                                       PseudoNodeType.INTERNAL, edge_direct=direct_table[degree_p1_p2])
                            if [grid_p1[0]+1, grid_p1[1]-k] not in ret[-1].pseudo_node_set:
                                ret[-1].pseudo_node_set.append([grid_p1[0]+1, grid_p1[1]-k])
                    elif direct_table[degree_p1_p2] == WireDirect.RIGHT:
                        for k in range(grid_p2[0] - (grid_p1[0] + 1) + 1):
                            self.set_electrode_to_grid([grid_p1[0]+1+k, grid_p1[1]+1], electrode_index,
                                                       [self.grid[grid_p1[0]+1+k][grid_p1[1]+1].real_x, p1[1]],
                                                       PseudoNodeType.INTERNAL, edge_direct=direct_table[degree_p1_p2])
                            if [grid_p1[0]+1+k, grid_p1[1]+1] not in ret[-1].pseudo_node_set:
                                ret[-1].pseudo_node_set.append([grid_p1[0]+1+k, grid_p1[1]+1])
                    elif direct_table[degree_p1_p2] == WireDirect.DOWN:
                        for k in range(grid_p2[1] - (grid_p1[1] + 1) + 1):
                            self.set_electrode_to_grid([grid_p1[0], grid_p1[1]+1+k], electrode_index,
                                                       [p1[0], self.grid[grid_p1[0]][grid_p1[1]+1+k].real_y],
                                                       PseudoNodeType.INTERNAL, edge_direct=direct_table[degree_p1_p2])
                            if [grid_p1[0], grid_p1[1]+1+k] not in ret[-1].pseudo_node_set:
                                ret[-1].pseudo_node_set.append([grid_p1[0], grid_p1[1]+1+k])
                    elif direct_table[degree_p1_p2] == WireDirect.LEFT:
                        for k in range(grid_p1[0] - grid_p2[0]):
                            self.set_electrode_to_grid([grid_p1[0]-k, grid_p1[1]], electrode_index,
                                                       [self.grid[grid_p1[0]-k][grid_p1[1]].real_x, p1[1]],
                                                       PseudoNodeType.INTERNAL, edge_direct=direct_table[degree_p1_p2])
                            if [grid_p1[0]-k, grid_p1[1]] not in ret[-1].pseudo_node_set:
                                ret[-1].pseudo_node_set.append([grid_p1[0]-k, grid_p1[1]])
                    else:
                        corner_point = [((p1[0] + p2[0]) / 2), ((p1[1] + p2[1]) / 2)]
                        edge_direct: WireDirect = direct_table[degree_p1_p2]
                        grid_index = self.find_short_grid_internal(self.grid, corner_point, poly_points)
                        if grid_index is not None:
                            self.set_electrode_to_grid([grid_index[0], grid_index[1]], electrode_index,
                                                       corner_point, PseudoNodeType.INTERNAL, corner=True,
                                                       edge_direct=edge_direct)
                            if [grid_index[0], grid_index[1]] not in ret[-1].pseudo_node_set:
                                ret[-1].pseudo_node_set.append([grid_index[0], grid_index[1]])

                ret[-1].boundary_U = boundary_U
                ret[-1].boundary_D = boundary_D
                ret[-1].boundary_L = boundary_L
                ret[-1].boundary_R = boundary_R

                covered_grid_list.append(covered_grid)

        return covered_grid_list, ret
