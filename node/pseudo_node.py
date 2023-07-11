import math
from typing import Union

import numpy as np

from config import WireDirect
from node.electrode import Electrode
from node.grid import Grid, GridType, PseudoNodeType
from wire.degree import Degree, direct_table


class PseudoNode():
    """PseudoNode class.
    """

    def __init__(self, grid: list[list[Grid]], shape_lib: dict, start_point: list, unit: float, electrode_list: list):
        self.grid = grid
        self.shape_lib: dict[str, list] = shape_lib
        self.start_point = start_point
        self.unit = unit
        self.electrode_list: list[list] = electrode_list

    def get_grid(self, x: int, y: int) -> Grid:
        """get grid by index

        Args:
            x (int): x
            y (int): y

        Returns:
            Grid: grid
        """
        return self.grid[x][y]

    def get_point_by_shape(self, elec_point: list, shape_point: list) -> list:
        """Get real point by electrode point and shape point

        Args:
            elec_point (list): the top-left point in electrode
            shape_point (list): the point by svg path

        Returns:
            list: real point
        """
        return [elec_point[0] + float(shape_point[0]), elec_point[1] + float(shape_point[1])]

    def get_grid_point(self, real_point: tuple, unit: float) -> list:
        """Get gird point by real point.

        Args:
            real_point (tuple): real point
            unit (float): unit
        """
        return [int((real_point[0] - self.start_point[0]) // unit), int((real_point[1] - self.start_point[1]) // unit)]

    def cal_distance(self, p1: tuple, p2: tuple) -> float:
        """Calculate distance between 2 points

        Args:
            p1 (tuple): point1
            p2 (tuple): point2

        Returns:
            float: distance
        """
        return math.sqrt(math.pow((p2[0] - p1[0]), 2) + math.pow((p2[1] - p1[1]), 2))

    def get_grid_point_list(self, real_point: list, unit: float) -> list:
        """Get gird point list by real point

        Args:
            real_point (list): real point
            unit (float): unit

        Returns:
            list: grid point list
        """
        left_up = [int((real_point[0] - self.start_point[0]) // unit), int((real_point[1] - self.start_point[1]) // unit)]
        right_up = [left_up[0] + 1, left_up[1]]
        right_bottom = [left_up[0] + 1, left_up[1] + 1]
        left_bottom = [left_up[0], left_up[1] + 1]
        return [left_up, right_up, right_bottom, left_bottom]

    def clockwise_angle(self, v1: tuple, v2: tuple) -> float:
        """Get clockwise angle between 2 points

        Args:
            v1 (tuple): point1
            v2 (tuple): point2

        Returns:
            float: angle between 2 points
        """
        x1, y1 = v1
        x2, y2 = v2
        dot = x1 * x2 + y1 * y2
        det = x1 * y2 - y1 * x2
        theta = np.arctan2(det, dot)
        theta = theta if theta > 0 else 2 * np.pi + theta
        return (theta * 180 / np.pi)

    def set_electrode_to_grid(
            self,
            point: list,
            elec_index: int,
            elec_point: list,
            pseudo_node_type: PseudoNodeType,
            corner: bool = False,
            edge_direct: WireDirect = 0
        ):
        """Set electrode info to grid.

        Args:
            point (list): grid point
            elec_index (int): electrode index
            elec_point (list): electrode point
            pseudo_node_type (PseudoNodeType): pseudo node type
            corner (bool, optional): is corner. Defaults to False.
            edge_direct (WireDirect, optional): edge direct. Defaults to 0.
        """
        x = point[0]
        y = point[1]
        target = self.get_grid(x, y)
        if target.corner is False:
            target.electrode_index = elec_index
            target.type = GridType.PSEUDO_NODE
            target.flow = 1
            target.electrode_x = elec_point[0]
            target.electrode_y = elec_point[1]
            target.corner = corner
            target.pseudo_node_type = pseudo_node_type
            target.edge_direct = edge_direct

    def is_poi_with_in_poly(self, point: list, poly: list):
        """Check point is in poly

        Args:
            poi (list): point
            poly (list): poly
        """
        # input: point, polygon 2d array

        # poly=[[x1,y1],[x2,y2],……,[xn,yn],[x1,y1]] 2d array
        # number of intersections
        sinsc = 0
        for i in range(len(poly)-1):  # [0,len-1]
            s_point = poly[i]
            e_point = poly[i+1]
            if self.is_ray_intersects_segment(point, s_point, e_point):
                # if intersections > 0
                sinsc += 1

        return True if sinsc % 2 == 1 else False

    def is_ray_intersects_segment(self, point: list, s_point: list, e_point: list) -> bool:
        """Check ray is intersects segment. [x,y] [lng,lat].

        Args:
            point (list): point
            s_point (list): start point
            e_point (list): end point

        Returns:
            bool: is intersects
        """
        if s_point[1] == e_point[1]:  # 排除與射線平行、重合，線段首尾端點重合的情況
            return False
        if s_point[1] > point[1] and e_point[1] > point[1]:  # 線段在射線上邊
            return False
        if s_point[1] < point[1] and e_point[1] < point[1]:  # 線段在射線下邊
            return False
        if s_point[1] == point[1] and e_point[1] > point[1]:  # 交點為下端點，對應spointnt
            return False
        if e_point[1] == point[1] and s_point[1] > point[1]:  # 交點為下端點，對應epointnt
            return False
        if s_point[0] < point[0] and e_point[1] < point[1]:  # 線段在射線左邊
            return False

        xseg = e_point[0]-(e_point[0]-s_point[0])*(e_point[1]-point[1])/(e_point[1]-s_point[1])  # 求交
        if xseg < point[0]:  # 交點在射線起點的左側
            return False
        return True  # 排除上述情況之後

    def find_short_grid_internal(self, grid: list[list[Grid]], elec_point: list, poly_point_list: list) -> list:
        """Find the closest gird and inside electrode by a real point

        Args:
            grid (list[list[Grid]]): grid
            elec_point (list): real point
            poly_point_list (list): poly point list

        Returns:
            list: grid index [x, y]
        """
        grid_point_list = self.get_grid_point_list(elec_point, self.unit)
        grid_point_list_internal = []
        for g_p in grid_point_list:
            target = self.get_grid(g_p[0], g_p[1])
            if self.is_poi_with_in_poly([target.real_x, target.real_y], poly_point_list):
                grid_point_list_internal.append(g_p)
        return self.find_short_grid_from_points(grid, grid_point_list_internal, elec_point)

    def find_short_grid_from_points(self, grid: list[list[Grid]], grid_point_list: list, elec_p: list) -> Union[list, None]:
        """Find the closest gird by a real point and grid point list.

        Args:
            grid (list[list[Grid]]): grid
            grid_point_list (list): grid point list
            elec_p (list): real point

        Returns:
            Union[list, None]: grid index [x, y]
        """
        ps = []
        for grid_p in grid_point_list:
            target = self.get_grid(grid_p[0], grid_p[1])
            ps.append([target.real_x, target.real_y])
        dis = []
        for p in ps:
            dis.append(self.cal_distance(elec_p, p))
        if len(dis) > 0:
            short_p = min(dis)
            index = dis.index(short_p)
            return grid_point_list[index]
        else:
            return None

    def internal_node(self) -> tuple[list[Grid], list[Electrode]]:
        """Find all pseudo node for each electrode.

        Returns:
            tuple[list[Grid], list[Electrode]]: grid, electrode
        """
        ret: list[Electrode] = []
        covered_grid_list: list[Grid] = []
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
                    corner = None
                    p0 = None
                    p1 = self.get_point_by_shape([electrode_x, electrode_y], electrode_shape_path[j])
                    p2 = self.get_point_by_shape([electrode_x, electrode_y], electrode_shape_path[j+1])

                    # if electrode have no corner
                    if p1 == p2:
                        if j == 0:
                            corner = 0
                        else:
                            p0 = self.get_point_by_shape([electrode_x, electrode_y], electrode_shape_path[j-1])
                            if p0[1] == p1[1]:
                                if p0[0] < p1[0]:
                                    corner = 1
                                else:
                                    corner = 3
                            else:
                                corner = 2

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

                    degree_p1_p2 = Degree.get_degree(p1[0], -p1[1], p2[0], -p2[1])

                    # if electrode have no corner
                    if corner:
                        if corner == 0:
                            degree_p1_p2 = Degree.get_degree(0, -30, 30, -0)
                        elif corner == 1:
                            degree_p1_p2 = Degree.get_degree(1940, -0, 1970, -30)
                        elif corner == 2:
                            degree_p1_p2 = Degree.get_degree(1970, -1940, 1940, -1970)
                        elif corner == 3:
                            degree_p1_p2 = Degree.get_degree(30, -1970, 0, -1940)

                    if direct_table[degree_p1_p2] == WireDirect.UP:
                        for k in range(grid_p1[1] - (grid_p2[1] + 1) + 1):
                            if covered_grid is None:
                                if self.get_grid(grid_p1[0]+2, grid_p1[1]-k).pseudo_node_type != PseudoNodeType.INTERNAL:
                                    covered_grid = self.grid[grid_p1[0]+2][grid_p1[1]-k]
                            self.set_electrode_to_grid(
                                [grid_p1[0]+1, grid_p1[1]-k],
                                electrode_index,
                                [p1[0], self.get_grid(grid_p1[0]+1, grid_p1[1]-k).real_y],
                                PseudoNodeType.INTERNAL,
                                edge_direct=direct_table[degree_p1_p2]
                            )
                            if [grid_p1[0]+1, grid_p1[1]-k] not in ret[-1].pseudo_node_set:
                                ret[-1].pseudo_node_set.append([grid_p1[0]+1, grid_p1[1]-k])
                    elif direct_table[degree_p1_p2] == WireDirect.RIGHT:
                        for k in range(grid_p2[0] - (grid_p1[0] + 1) + 1):
                            self.set_electrode_to_grid(
                                [grid_p1[0]+1+k, grid_p1[1]+1],
                                electrode_index,
                                [self.get_grid(grid_p1[0]+1+k, grid_p1[1]+1).real_x, p1[1]],
                                PseudoNodeType.INTERNAL,
                                edge_direct=direct_table[degree_p1_p2]
                            )
                            if [grid_p1[0]+1+k, grid_p1[1]+1] not in ret[-1].pseudo_node_set:
                                ret[-1].pseudo_node_set.append([grid_p1[0]+1+k, grid_p1[1]+1])
                    elif direct_table[degree_p1_p2] == WireDirect.BOTTOM:
                        for k in range(grid_p2[1] - (grid_p1[1] + 1) + 1):
                            self.set_electrode_to_grid(
                                [grid_p1[0], grid_p1[1]+1+k],
                                electrode_index,
                                [p1[0], self.get_grid(grid_p1[0], grid_p1[1]+1+k).real_y],
                                PseudoNodeType.INTERNAL,
                                edge_direct=direct_table[degree_p1_p2]
                            )
                            if [grid_p1[0], grid_p1[1]+1+k] not in ret[-1].pseudo_node_set:
                                ret[-1].pseudo_node_set.append([grid_p1[0], grid_p1[1]+1+k])
                    elif direct_table[degree_p1_p2] == WireDirect.LEFT:
                        for k in range(grid_p1[0] - grid_p2[0]):
                            self.set_electrode_to_grid(
                                [grid_p1[0]-k, grid_p1[1]],
                                electrode_index,
                                [self.get_grid(grid_p1[0]-k, grid_p1[1]).real_x, p1[1]],
                                PseudoNodeType.INTERNAL,
                                edge_direct=direct_table[degree_p1_p2]
                            )
                            if [grid_p1[0]-k, grid_p1[1]] not in ret[-1].pseudo_node_set:
                                ret[-1].pseudo_node_set.append([grid_p1[0]-k, grid_p1[1]])
                    else:
                        corner_point = [((p1[0] + p2[0]) / 2), ((p1[1] + p2[1]) / 2)]
                        edge_direct: WireDirect = direct_table[degree_p1_p2]
                        grid_index = self.find_short_grid_internal(self.grid, corner_point, poly_points)
                        if grid_index is not None:
                            self.set_electrode_to_grid(
                                [grid_index[0], grid_index[1]],
                                electrode_index,
                                corner_point,
                                PseudoNodeType.INTERNAL,
                                corner=True,
                                edge_direct=edge_direct
                            )
                            if [grid_index[0], grid_index[1]] not in ret[-1].pseudo_node_set:
                                ret[-1].pseudo_node_set.append([grid_index[0], grid_index[1]])

                ret[-1].boundary_U = boundary_U
                ret[-1].boundary_D = boundary_D
                ret[-1].boundary_L = boundary_L
                ret[-1].boundary_R = boundary_R

                covered_grid_list.append(covered_grid)

        return covered_grid_list, ret
