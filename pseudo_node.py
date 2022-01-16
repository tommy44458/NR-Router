import numpy as np
from typing import Any, Optional, Tuple, Union, List, Dict, Callable, NoReturn
import sys
import os
from operator import itemgetter, attrgetter
from math import atan2, degrees

from numpy.lib.twodim_base import triu_indices_from

from degree import Degree
from grid import Grid
from tile import Tile
from hub import Hub
from electrode import Electrode


class Pseudo():

    def __init__(self, shape, shape_scope, block_shift, tile_unit, elec_list):
        self.shape = shape
        self.shape_scope = shape_scope
        self.block_shift = block_shift
        self.tile_unit = tile_unit
        self.elec_list = elec_list

    # elec_p is the top-lsft point in electrode
    # shape_p is the point by svg path
    def get_point_by_shape(self, elec_p: list, shape_p: list) -> list:
        return [elec_p[0] + shape_p[0], elec_p[1] + shape_p[1]]

    # get gird point by real point
    def get_grid_point(self, p, unit) -> list:
        return [(p[0] - self.block_shift[0]) // unit, (p[1] - self.block_shift[1]) // unit]

    # return angle between 2 points
    def clockwise_angle(self, v1, v2) -> float:
        x1, y1 = v1
        x2, y2 = v2
        dot = x1 * x2 + y1 * y2
        det = x1 * y2 - y1 * x2
        theta = np.arctan2(det, dot)
        theta = theta if theta > 0 else 2 * np.pi + theta
        return (theta * 180 / np.pi)


    # set electrode info to grid
    def grid_set_electrode(self, grid: Grid, point: list, elec_index: int, elec_p: list, corner = False):
        x = point[0]
        y = point[1]
        grid[x, y].electrode_index = elec_index
        grid[x, y].type += 1
        grid[x, y].electrode_x = elec_p[0]
        grid[x, y].electrode_y = elec_p[1]
        grid[x, y].corner = corner


    def internal_straight(self, grid: Grid):
        num_electrode = 0
        for electrode in self.elec_list:
            for i in range(len(self.shape)):
                if electrode[2] == self.shape[i]:
                    shape_path = self.shape_scope[i]
                    for j in range(len(shape_path)-1):
                        p1 = self.get_point_by_shape(
                            [electrode[1], electrode[0]], shape_path[j])
                        p2 = self.get_point_by_shape(
                            [electrode[1], electrode[0]], shape_path[j + 1])
                        # vertex in which grid
                        grid_p1 = self.get_grid_point(self, p1, self.tile_unit)
                        grid_p2 = self.get_grid_point(self, p2, self.tile_unit)

                        ang = self.clockwise_angle([0, -1], [x2-x1, y2-y1])

                        # 直線
                        if ang % 90 == 0:
                            # ->
                            if ang == 90:
                                for k in range(grid_p2[0] - (grid_p1[0] + 1) + 1):
                                    self.grid_set_electrode(
                                        self.grids4, grid_p1[0]+1+k, grid_p1[1]+1, num_electrode, self.grids4[grid_p1[0]+1+k][grid_p1[1]+1].real_x, y1)
                            # ## | down
                            if ang == 180:
                                for k in range(grid_p2[1] - (grid_p1[1] + 1) + 1):
                                    self.grid_set_electrode(
                                        self.grids4, grid_p1[0], grid_p1[1]+1+k, num_electrode, x1, self.grids4[grid_p1[0]][grid_p1[1]+1+k].real_y)
                            # <-
                            elif ang == 270:
                                for k in range(grid_p1[0] - grid_p2[0]):
                                    self.grid_set_electrode(
                                        self.grids4, grid_p1[0]-k, grid_p1[1], num_electrode, self.grids4[grid_p1[0]-k][grid_p1[1]].real_x, y1)
                            # | up
                            elif ang == 360:
                                for k in range(grid_p1[1] - (grid_p2[1] + 1) + 1):
                                    self.grid_set_electrode(
                                        self.grids4, grid_p1[0]+1, grid_p1[1]-k, num_electrode, x1, self.grids4[grid_p1[0]+1][grid_p1[1]-k].real_y)
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
                        if ang % 90 != 0:
                            if x1 > x2:
                                # |
                                #  \ _
                                if y1 > y2:
                                    point = [(x1 + x2) / 2, (y1 + y2) / 2]
                                    E_grid_x = (
                                        point[0] - self.block2_shift[0]) // self.tile_unit
                                    E_grid_y = (
                                        point[1] - self.block2_shift[1]) // self.tile_unit
                                    in_x = int(E_grid_x+1)
                                    in_y = int(E_grid_y)
                                    self.grid_set_electrode(
                                        self.grids4, in_x, in_y, num_electrode, point[0], point[1], True)
                                #  |
                                # /
                                else:
                                    point = [(x1 + x2) / 2, (y1 + y2) / 2]
                                    E_grid_x = (
                                        point[0] - self.block2_shift[0]) // self.tile_unit
                                    E_grid_y = (
                                        point[1] - self.block2_shift[1]) // self.tile_unit
                                    in_x = int(E_grid_x)
                                    in_y = int(E_grid_y)
                                    self.grid_set_electrode(
                                        self.grids4, in_x, in_y, num_electrode, point[0], point[1], True)
                            elif x1 < x2:
                                # \
                                #  |
                                if y1 < y2:
                                    point = [(x1 + x2) / 2, (y1 + y2) / 2]
                                    E_grid_x = (
                                        point[0] - self.block2_shift[0]) // self.tile_unit
                                    E_grid_y = (
                                        point[1] - self.block2_shift[1]) // self.tile_unit
                                    in_x = int(E_grid_x)
                                    in_y = int(E_grid_y+1)
                                    self.grid_set_electrode(
                                        self.grids4, in_x, in_y, num_electrode, point[0], point[1], True)
                                #  /
                                # |
                                else:
                                    point = [(x1 + x2) / 2, (y1 + y2) / 2]
                                    E_grid_x = (
                                        point[0] - self.block2_shift[0]) // self.tile_unit
                                    E_grid_y = (
                                        point[1] - self.block2_shift[1]) // self.tile_unit
                                    in_x = int(E_grid_x+1)
                                    in_y = int(E_grid_y+1)
                                    self.grid_set_electrode(
                                        self.grids4, in_x, in_y, num_electrode, point[0], point[1], True)
            num_electrode += 1

    def internal_corner(self, shape, shape_scope):
        num_electrode = 0
        for electrode in self.list_electrodes:
            for i in range(len(shape)):
                if electrode[2] == shape[i]:
                    true_x = electrode[1]
                    true_y = electrode[0]
                    # new_electrode = Electrode(true_x, true_y, i, num_electrode)
                    electrode_shape_path = shape_scope[i]
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

                        # 直線
                        if ang % 90 == 0:
                            # ->
                            if ang == 90:
                                for k in range(E_grid_x2 - (E_grid_x1 + 1) + 1):
                                    self.grid_set_electrode(
                                        self.grids4, E_grid_x1+1+k, E_grid_y1+1, num_electrode, self.grids4[E_grid_x1+1+k][E_grid_y1+1].real_x, y1)
                            # ## | down
                            if ang == 180:
                                for k in range(E_grid_y2 - (E_grid_y1 + 1) + 1):
                                    self.grid_set_electrode(
                                        self.grids4, E_grid_x1, E_grid_y1+1+k, num_electrode, x1, self.grids4[E_grid_x1][E_grid_y1+1+k].real_y)
                            # <-
                            elif ang == 270:
                                for k in range(E_grid_x1 - E_grid_x2):
                                    self.grid_set_electrode(
                                        self.grids4, E_grid_x1-k, E_grid_y1, num_electrode, self.grids4[E_grid_x1-k][E_grid_y1].real_x, y1)
                            # | up
                            elif ang == 360:
                                for k in range(E_grid_y1 - (E_grid_y2 + 1) + 1):
                                    self.grid_set_electrode(
                                        self.grids4, E_grid_x1+1, E_grid_y1-k, num_electrode, x1, self.grids4[E_grid_x1+1][E_grid_y1-k].real_y)
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
                        if ang % 90 != 0:
                            if x1 > x2:
                                # |
                                #  \ _
                                if y1 > y2:
                                    point = [(x1 + x2) / 2, (y1 + y2) / 2]
                                    E_grid_x = (
                                        point[0] - self.block2_shift[0]) // self.tile_unit
                                    E_grid_y = (
                                        point[1] - self.block2_shift[1]) // self.tile_unit
                                    in_x = int(E_grid_x+1)
                                    in_y = int(E_grid_y)
                                    self.grid_set_electrode(
                                        self.grids4, in_x, in_y, num_electrode, point[0], point[1], True)
                                #  |
                                # /
                                else:
                                    point = [(x1 + x2) / 2, (y1 + y2) / 2]
                                    E_grid_x = (
                                        point[0] - self.block2_shift[0]) // self.tile_unit
                                    E_grid_y = (
                                        point[1] - self.block2_shift[1]) // self.tile_unit
                                    in_x = int(E_grid_x)
                                    in_y = int(E_grid_y)
                                    self.grid_set_electrode(
                                        self.grids4, in_x, in_y, num_electrode, point[0], point[1], True)
                            elif x1 < x2:
                                # \
                                #  |
                                if y1 < y2:
                                    point = [(x1 + x2) / 2, (y1 + y2) / 2]
                                    E_grid_x = (
                                        point[0] - self.block2_shift[0]) // self.tile_unit
                                    E_grid_y = (
                                        point[1] - self.block2_shift[1]) // self.tile_unit
                                    in_x = int(E_grid_x)
                                    in_y = int(E_grid_y+1)
                                    self.grid_set_electrode(
                                        self.grids4, in_x, in_y, num_electrode, point[0], point[1], True)
                                #  /
                                # |
                                else:
                                    point = [(x1 + x2) / 2, (y1 + y2) / 2]
                                    E_grid_x = (
                                        point[0] - self.block2_shift[0]) // self.tile_unit
                                    E_grid_y = (
                                        point[1] - self.block2_shift[1]) // self.tile_unit
                                    in_x = int(E_grid_x+1)
                                    in_y = int(E_grid_y+1)
                                    self.grid_set_electrode(
                                        self.grids4, in_x, in_y, num_electrode, point[0], point[1], True)
            num_electrode += 1

    def set_grid_by_electrode_edge_opt2(self, shape, shape_scope):
        for electrode in self.list_electrodes:
            for i in range(len(shape)):
                if electrode[2] == shape[i]:
                    true_x = electrode[1]
                    true_y = electrode[0]
                    new_electrode = Electrode(
                        true_x, true_y, i, self.num_electrode)
                    # print(new_electrode.to_dict())
                    self.electrodes.append(new_electrode)
                    boundary_U = true_y
                    boundary_D = true_y
                    boundary_L = true_x
                    boundary_R = true_x
                    electrode_shape_path = shape_scope[i]
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
                                    ex_dis = abs(
                                        y1 - self.grids2[E_grid_x1+1+k][E_grid_y1].real_y)
                                    ex_x = E_grid_x1+1+k
                                    ex_y = E_grid_y1
                                    in_dis = abs(
                                        y1 - self.grids4[E_grid_x1+1+k][E_grid_y1+1].real_y)
                                    if ex_dis < in_dis:
                                        if self.grid_is_available(self.grids2, ex_x, ex_y, self.num_electrode):
                                            self.grid_set_electrode(
                                                self.grids2, ex_x, ex_y, self.num_electrode, self.grids2[E_grid_x1+1+k][E_grid_y1].real_x, y1)
                            # | down
                            elif ang == 180:
                                for k in range(E_grid_y2 - (E_grid_y1 + 1) + 1):
                                    ex_dis = abs(
                                        x1 - self.grids2[E_grid_x1+1][E_grid_y1+1+k].real_x)
                                    ex_x = E_grid_x1+1
                                    ex_y = E_grid_y1+1+k
                                    in_dis = abs(
                                        x1 - self.grids4[E_grid_x1][E_grid_y1+1+k].real_x)
                                    if ex_dis < in_dis:
                                        if self.grid_is_available(self.grids2, ex_x, ex_y, self.num_electrode):
                                            self.grid_set_electrode(
                                                self.grids2, ex_x, ex_y, self.num_electrode, x1, self.grids2[E_grid_x1+1][E_grid_y1+1+k].real_y)
                            # <-
                            elif ang == 270:
                                for k in range(E_grid_x1 - E_grid_x2):
                                    ex_dis = abs(
                                        y1 - self.grids2[E_grid_x1-k][E_grid_y1+1].real_y)
                                    ex_x = E_grid_x1-k
                                    ex_y = E_grid_y1+1
                                    in_dis = abs(
                                        y1 - self.grids4[E_grid_x1-k][E_grid_y1].real_y)
                                    if ex_dis < in_dis:
                                        if self.grid_is_available(self.grids2, ex_x, ex_y, self.num_electrode):
                                            self.grid_set_electrode(
                                                self.grids2, ex_x, ex_y, self.num_electrode, self.grids2[E_grid_x1-k][E_grid_y1+1].real_x, y1)
                            # | up
                            elif ang == 360:
                                for k in range(E_grid_y1 - (E_grid_y2 + 1) + 1):
                                    ex_dis = abs(
                                        x1 - self.grids2[E_grid_x1][E_grid_y1-k].real_x)
                                    ex_x = E_grid_x1
                                    ex_y = E_grid_y1-k
                                    in_dis = abs(
                                        x1 - self.grids4[E_grid_x1+1][E_grid_y1-k].real_x)
                                    if ex_dis < in_dis:
                                        if self.grid_is_available(self.grids2, ex_x, ex_y, self.num_electrode):
                                            self.grid_set_electrode(
                                                self.grids2, ex_x, ex_y, self.num_electrode, x1, self.grids2[E_grid_x1][E_grid_y1-k].real_y)

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
                            E_grid_x = int(
                                (point[0] - self.block2_shift[0]) // self.tile_unit)
                            E_grid_y = int(
                                (point[1] - self.block2_shift[1]) // self.tile_unit)
                            short_p = self.find_short_grid(
                                self.grids2, [E_grid_x, E_grid_y], point)
                            ex_x = short_p[0]
                            ex_y = short_p[1]
                            if self.grid_is_available(self.grids2, ex_x, ex_y, self.num_electrode):
                                self.grid_set_electrode(
                                    self.grids2, ex_x, ex_y, self.num_electrode, point[0], point[1], True)
                                short_p_inner = self.find_short_grid_internal(
                                    self.grids4, [E_grid_x, E_grid_y], point, poly_points)
                                self.grid_set_electrode(
                                    self.grids4, short_p_inner[0], short_p_inner[1], self.num_electrode, point[0], point[1], True)
                                self.grids2[ex_x][ex_y].inner_grid = self.grids4[short_p_inner[0]
                                                                                 ][short_p_inner[1]]
                            else:
                                self.grid_conflict(self.grids2, ex_x, ex_y)
                                short_p_inner = self.find_short_grid_internal(
                                    self.grids2, [E_grid_x, E_grid_y], point, poly_points, [ex_x, ex_y])
                                # if short_p_inner[0] != ex_x and short_p_inner[1] != ex_y:
                                self.grid_set_electrode(
                                    self.grids2, short_p_inner[0], short_p_inner[1], self.num_electrode, point[0], point[1], True)
                    self.electrodes[-1].boundary_U = boundary_U
                    self.electrodes[-1].boundary_D = boundary_D
                    self.electrodes[-1].boundary_L = boundary_L
                    self.electrodes[-1].boundary_R = boundary_R
            self.num_electrode += 1
