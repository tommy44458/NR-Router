import numpy as np
from typing import Any, Optional, Tuple, Union, List, Dict, Callable, NoReturn
import sys
import os
from operator import itemgetter, attrgetter
import math

from numpy.lib.twodim_base import triu_indices_from

from degree import Degree
from grid import Grid, PseudoNodeType
from tile import Tile
from hub import Hub
from degree import Degree, direct_table
from electrode import Electrode


class PseudoNode():

    def __init__(self, grid: List[List[Grid]], shape_lib: dict, start_point: list, unit: float, electrode_list: list):
        self.grid = grid
        self.shape_lib: Dict[str, list] = shape_lib
        self.start_point = start_point
        self.unit = unit
        self.electrode_list: List[list] = electrode_list

        self.direct_table = direct_table()

    # elec_p is the top-lsft point in electrode
    # shape_p is the point by svg path
    def get_point_by_shape(self, elec_point: list, shape_point: list) -> list:
        return [elec_point[0] + shape_point[0], elec_point[1] + shape_point[1]]

    # get gird point by real point
    def get_grid_point(self, real_point: list, unit: float) -> list:
        return [(real_point[0] - self.start_point[0]) // unit, (real_point[1] - self.start_point[1]) // unit]

    def cal_distance(self, p1: list, p2: list):
        return math.sqrt(math.pow((p2[0] - p1[0]), 2) + math.pow((p2[1] - p1[1]), 2))

    # get gird point list by real point
    def get_grid_point_list(self, real_point: list, unit: float) -> list:
        left_up = [int((real_point[0] - self.start_point[0]) // unit), int((real_point[1] - self.start_point[1]) // unit)]
        right_up = [left_up[0] + 1, left_up[1]]
        right_down = [left_up[0] + 1, left_up[1] + 1]
        left_down = [left_up[0], left_up[1] + 1]
        return [left_up, right_up, right_down, left_down]

    # return angle between 2 points
    def clockwise_angle(self, v1: tuple, v2: tuple) -> float:
        x1, y1 = v1
        x2, y2 = v2
        dot = x1 * x2 + y1 * y2
        det = x1 * y2 - y1 * x2
        theta = np.arctan2(det, dot)
        theta = theta if theta > 0 else 2 * np.pi + theta
        return (theta * 180 / np.pi)

    # set electrode info to grid
    def set_electrode_to_grid(self, point: list, elec_index: int, elec_point: list,
                              pseudo_node_type: PseudoNodeType, corner=False):
        x = point[0]
        y = point[1]
        if self.grid[x][y].corner is False:
            self.grid[x][y].electrode_index = elec_index
            self.grid[x][y].type += 1
            self.grid[x][y].electrode_x = elec_point[0]
            self.grid[x][y].electrode_y = elec_point[1]
            self.grid[x][y].corner = corner
            self.grid[x][y].pseudo_node_type = pseudo_node_type

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
        print(grid_point_list)
        grid_point_list_internal = []
        for g_p in grid_point_list:
            if self.is_poi_with_in_poly([self.grid[g_p[0]][g_p[1]].real_x, self.grid[g_p[0]][g_p[1]].real_y], poly_point_list):
                grid_point_list_internal.append(g_p)
        print(grid_point_list_internal)
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

    def internal_node(self):
        for electrode_index, electrode in enumerate(self.electrode_list):
            if electrode[0] in self.shape_lib:
                electrode_x = electrode[1]
                electrode_y = electrode[2]
                electrode_shape_path = self.shape_lib[electrode[0]]
                # get poly vertex list
                poly_points = []
                for j in range(len(electrode_shape_path)-1):
                    p = self.get_point_by_shape([electrode_x, electrode_y], electrode_shape_path[j])
                    poly_points.append(p)
                poly_points.append([poly_points[0][0], poly_points[0][1]])

                # trace all poly vertex to get pseudo node
                for j in range(len(electrode_shape_path)-1):
                    p1 = self.get_point_by_shape([electrode_x, electrode_y], electrode_shape_path[j])
                    p2 = self.get_point_by_shape([electrode_x, electrode_y], electrode_shape_path[j+1])

                    # vertex in which grid
                    grid_p1 = self.get_grid_point(p1, self.unit)
                    grid_p2 = self.get_grid_point(p2, self.unit)

                    degree_p1_p2 = Degree.getdegree(p1[0], -p1[1], p2[0], -p2[1])

                    if self.direct_table[degree_p1_p2] == 'up':
                        for k in range(grid_p1[1] - (grid_p2[1] + 1) + 1):
                            self.set_electrode_to_grid([grid_p1[0]+1, grid_p1[1]-k], electrode_index,
                                                       [p1[0], self.grid[grid_p1[0]+1][grid_p1[1]-k].real_y],
                                                       PseudoNodeType.INTERNAL)
                    elif self.direct_table[degree_p1_p2] == 'right':
                        for k in range(grid_p2[0] - (grid_p1[0] + 1) + 1):
                            self.set_electrode_to_grid([grid_p1[0]+1+k, grid_p1[1]+1], electrode_index,
                                                       [self.grid[grid_p1[0]+1+k][grid_p1[1]+1].real_x, p1[1]],
                                                       PseudoNodeType.INTERNAL)
                    elif self.direct_table[degree_p1_p2] == 'down':
                        for k in range(grid_p2[1] - (grid_p1[1] + 1) + 1):
                            self.set_electrode_to_grid([grid_p1[0], grid_p1[1]+1+k], electrode_index,
                                                       [p1[0], self.grid[grid_p1[0]][grid_p1[1]+1+k].real_y],
                                                       PseudoNodeType.INTERNAL)
                    elif self.direct_table[degree_p1_p2] == 'left':
                        for k in range(grid_p1[0] - grid_p2[0]):
                            self.set_electrode_to_grid([grid_p1[0]-k, grid_p1[1]], electrode_index,
                                                       [self.grid[grid_p1[0]-k][grid_p1[1]].real_x, p1[1]],
                                                       PseudoNodeType.INTERNAL)
                    else:
                        corner_point = [((p1[0] + p2[0]) / 2), ((p1[1] + p2[1]) / 2)]
                        grid_index = self.find_short_grid_internal(self.grid, corner_point, poly_points)
                        if grid_index is not None:
                            print(grid_index)
                            self.set_electrode_to_grid([grid_index[0], grid_index[1]], electrode_index,
                                                       corner_point, PseudoNodeType.INTERNAL, corner=True)

    def external(self, elec_list, shape_lib):
        for electrode_index, electrode in enumerate(elec_list):
            if electrode[0] in shape_lib:
                true_x = electrode[1]
                true_y = electrode[2]
                electrode_shape_path = shape_lib[electrode[0]]
                new_electrode = Electrode(true_x, true_y, electrode[0], electrode_index)

                boundary_U = true_y
                boundary_D = true_y
                boundary_L = true_x
                boundary_R = true_x
                poly_points = []

                for j in range(len(electrode_shape_path)-1):
                    x = true_x+electrode_shape_path[j][0]
                    y = true_y+electrode_shape_path[j][1]
                    poly_points.append([x, y])
                poly_points.append([poly_points[0][0], poly_points[0][1]])

                new_electrode.poly = poly_points
                for j in range(len(electrode_shape_path)-1):
                    x1 = true_x+electrode_shape_path[j][0]
                    y1 = true_y+electrode_shape_path[j][1]
                    x2 = true_x+electrode_shape_path[j+1][0]
                    y2 = true_y+electrode_shape_path[j+1][1]
                    E_grid_x1 = (x1-self.block2_shift[0]) // self.tile_unit
                    E_grid_x2 = (x2-self.block2_shift[0]) // self.tile_unit
                    E_grid_y1 = (y1-self.block2_shift[1]) // self.tile_unit
                    E_grid_y2 = (y2-self.block2_shift[1]) // self.tile_unit

                    ang = self.clockwise_angle([0, -1], [x2-x1, y2-y1])

                    if ang % 90 == 0:
                        # ->
                        if ang == 90:
                            for k in range(E_grid_x2 - (E_grid_x1 + 1) + 1):
                                ex_dis = abs(y1 - self.grids2[E_grid_x1+1+k][E_grid_y1].real_y)
                                ex_x = E_grid_x1+1+k
                                ex_y = E_grid_y1
                                in_dis = abs(y1 - self.grids4[E_grid_x1+1+k][E_grid_y1+1].real_y)
                                if ex_dis < in_dis:
                                    if self.grid_is_available(self.grids2, ex_x, ex_y, electrode_index):
                                        self.grid_set_electrode(self.grids2, ex_x, ex_y, electrode_index,
                                                                self.grids2[E_grid_x1+1+k][E_grid_y1].real_x, y1)
                        # | down
                        elif ang == 180:
                            for k in range(E_grid_y2 - (E_grid_y1 + 1) + 1):
                                ex_dis = abs(x1 - self.grids2[E_grid_x1+1][E_grid_y1+1+k].real_x)
                                ex_x = E_grid_x1+1
                                ex_y = E_grid_y1+1+k
                                in_dis = abs(x1 - self.grids4[E_grid_x1][E_grid_y1+1+k].real_x)
                                if ex_dis < in_dis:
                                    if self.grid_is_available(self.grids2, ex_x, ex_y, electrode_index):
                                        self.grid_set_electrode(self.grids2, ex_x, ex_y, electrode_index, x1,
                                                                self.grids2[E_grid_x1+1][E_grid_y1+1+k].real_y)
                        # <-
                        elif ang == 270:
                            for k in range(E_grid_x1 - E_grid_x2):
                                ex_dis = abs(y1 - self.grids2[E_grid_x1-k][E_grid_y1+1].real_y)
                                ex_x = E_grid_x1-k
                                ex_y = E_grid_y1+1
                                in_dis = abs(y1 - self.grids4[E_grid_x1-k][E_grid_y1].real_y)
                                if ex_dis < in_dis:
                                    if self.grid_is_available(self.grids2, ex_x, ex_y, electrode_index):
                                        self.grid_set_electrode(self.grids2, ex_x, ex_y, electrode_index,
                                                                self.grids2[E_grid_x1-k][E_grid_y1+1].real_x, y1)
                        # | up
                        elif ang == 360:
                            for k in range(E_grid_y1 - (E_grid_y2 + 1) + 1):
                                ex_dis = abs(x1 - self.grids2[E_grid_x1][E_grid_y1-k].real_x)
                                ex_x = E_grid_x1
                                ex_y = E_grid_y1-k
                                in_dis = abs(x1 - self.grids4[E_grid_x1+1][E_grid_y1-k].real_x)
                                if ex_dis < in_dis:
                                    if self.grid_is_available(self.grids2, ex_x, ex_y, electrode_index):
                                        self.grid_set_electrode(self.grids2, ex_x, ex_y, electrode_index, x1,
                                                                self.grids2[E_grid_x1][E_grid_y1-k].real_y)

                for j in range(len(electrode_shape_path)-1):
                    x1 = true_x+electrode_shape_path[j][0]
                    y1 = true_y+electrode_shape_path[j][1]
                    x2 = true_x+electrode_shape_path[j+1][0]
                    y2 = true_y+electrode_shape_path[j+1][1]

                    if x1 > boundary_R:
                        boundary_R = x1
                    if x1 < boundary_L:
                        boundary_L = x1
                    if y1 < boundary_U:
                        boundary_U = y1
                    if y1 > boundary_D:
                        boundary_D = y1

                    ang = self.clockwise_angle([0, -1], [x2-x1, y2-y1])

                    # 有角度
                    if ang % 90 != 0:
                        point = [(x1 + x2) / 2, (y1 + y2) / 2]
                        E_grid_x = int((point[0] - self.block2_shift[0]) // self.tile_unit)
                        E_grid_y = int((point[1] - self.block2_shift[1]) // self.tile_unit)
                        short_p = self.find_short_grid(self.grids2, [E_grid_x, E_grid_y], point)
                        ex_x = short_p[0]
                        ex_y = short_p[1]
                        if self.grid_is_available(self.grids2, ex_x, ex_y, electrode_index):
                            self.grid_set_electrode(self.grids2, ex_x, ex_y, electrode_index, point[0], point[1], True)
                            short_p_inner = self.find_short_grid_internal(self.grids4, [E_grid_x, E_grid_y], point, poly_points)
                            self.grid_set_electrode(self.grids4, short_p_inner[0], short_p_inner[1], electrode_index, point[0], point[1], True)
                            self.grids2[ex_x][ex_y].inner_grid = self.grids4[short_p_inner[0]][short_p_inner[1]]
                        else:
                            self.grid_conflict(self.grids2, ex_x, ex_y)
                            short_p_inner = self.find_short_grid_internal(self.grids2, [E_grid_x, E_grid_y], point, poly_points, [ex_x, ex_y])
                            # if short_p_inner[0] != ex_x and short_p_inner[1] != ex_y:
                            self.grid_set_electrode(self.grids2, short_p_inner[0], short_p_inner[1], electrode_index, point[0], point[1], True)
                new_electrode.boundary_U = boundary_U
                new_electrode.boundary_D = boundary_D
                new_electrode.boundary_L = boundary_L
                new_electrode.boundary_R = boundary_R

                self.electrodes.append(new_electrode)
