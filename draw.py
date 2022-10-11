from typing import Any, Callable, Dict, List, NoReturn, Optional, Tuple, Union

from ezdxf.document import Modelspace
from ezdxf.entities import BoundaryPaths

from degree import Degree, wire_offset_table
from electrode import Electrode
from grid import Grid, GridType
from hub import Hub
from tile import Tile
from wire import Wire


class Draw():
    def __init__(self, routing_wire: List[List[Wire]], wire_width: float, mini_wire_width: float):

        # routing path from electrode to contact pad
        self.routing_wire = routing_wire

        # chip config
        self.mini_width = mini_wire_width / 2
        self.regular_width = wire_width / 2
        self.line_buffer = self.regular_width * 0.0

        # wire config
        self.wire_offset_table, self.dia = wire_offset_table()
        self.regular_tan_offset = 0.41421356237 * self.regular_width
        self.mini_tan_offset = 0.41421356237 * self.mini_width
        # ang(45)
        self.regular_dia_offset = self.dia * self.regular_width
        self.mini_dia_offset = self.dia * self.mini_width

    def order_vertex(self, vertex: list) -> list:
        """
            Order the vertex list
        """
        vertex.sort(key=lambda x: (x[0]))
        vertex_left = vertex[0:2]
        vertex_right = vertex[2:4]
        vertex_left.sort(key=lambda x: (x[1]))
        vertex_right.sort(key=lambda x: (x[1]), reverse=False)
        vertex_left.extend(vertex_right)
        return vertex_left

    def draw_path(self, previous_wire: Wire, wire: Wire, next_wire: Wire, width: float, tan: float, dia: float, dxf: Modelspace):
        # get current wire start and end
        start_point = [wire.start_x, wire.start_y]
        end_point = [wire.end_x, wire.end_y]

        if previous_wire is not None:
            previous_point = [previous_wire.start_x, previous_wire.start_y]
            degree_previous_start = Degree.getdegree(previous_point[0], previous_point[1], start_point[0], start_point[1])
        else:
            # no previous wire
            degree_previous_start = None

        if next_wire is not None:
            next_point = [next_wire.end_x, next_wire.end_y]
            degree_end_next = Degree.getdegree(end_point[0], end_point[1], next_point[0], next_point[1])
        else:
            degree_end_next = None

        # no wire need to be drow
        if start_point == end_point:
            return None

        degree_start_end = Degree.getdegree(start_point[0], start_point[1], end_point[0], end_point[1])

        tan = tan
        dia_offset = dia

        wire_start = [start_point[0], start_point[1], start_point[0], start_point[1]]

        # get offset table
        start_offset = self.wire_offset_table.get(degree_previous_start, {}).get(degree_start_end, None)
        if start_offset is not None:
            for i in range(4):
                if start_offset[i] == 1:
                    wire_start[i] += width
                elif start_offset[i] == -1:
                    wire_start[i] -= width
                elif start_offset[i] == 2:
                    wire_start[i] += tan
                elif start_offset[i] == -2:
                    wire_start[i] -= tan
                elif start_offset[i] == 3:
                    wire_start[i] += dia_offset
                elif start_offset[i] == -3:
                    wire_start[i] -= dia_offset

        wire_end = [end_point[0], end_point[1], end_point[0], end_point[1]]

        end_offset = self.wire_offset_table.get(degree_start_end, {}).get(degree_end_next, None)
        if end_offset is not None:
            for i in range(4):
                if end_offset[i] == 1:
                    wire_end[i] += width
                elif end_offset[i] == -1:
                    wire_end[i] -= width
                elif end_offset[i] == 2:
                    wire_end[i] += tan
                elif end_offset[i] == -2:
                    wire_end[i] -= tan
                elif end_offset[i] == 3:
                    wire_end[i] += dia_offset
                elif end_offset[i] == -3:
                    wire_end[i] -= dia_offset

        vertex = [[wire_start[0], -wire_start[1]], [wire_start[2], -wire_start[3]], [wire_end[0], -wire_end[1]], [wire_end[2], -wire_end[3]]]
        vertex_order = self.order_vertex(vertex)
        dxf.add_solid(vertex_order)

    def draw_contact_pad(self, contactpad_list: List[list], dxf: Modelspace):
        for pad in contactpad_list:
            dxf.add_circle(center=(pad[0], -pad[1]), radius=750.0)

    def draw_electrodes(self, electrodes: List[list], shape_lib: dict, mesh_electrode_list: List[Electrode], dxf: Modelspace, hatch_path: BoundaryPaths):
        for elec_index, elec in enumerate(electrodes):
            shape = elec[0]
            x = elec[1]
            y = -elec[2]
            vertex_order = []
            for shape_p in shape_lib[shape]:
                vertex_order.append((x + float(shape_p[0]), y - float(shape_p[1])))
            dxf.add_polyline2d(vertex_order, close=True)
            if len(mesh_electrode_list[elec_index].routing_wire) == 0:
                hatch_path.add_polyline_path(vertex_order)

    def draw_grid(self, start_point: list, unit: float, gird_length: list, dxf: Modelspace):
        # col
        for i in range(gird_length[0]):
            dxf.add_line((start_point[0]+unit*i, -start_point[1]), (start_point[0] + unit*i, -(start_point[1]+unit*(gird_length[1]-1))))
        # row
        for i in range(gird_length[1]):
            dxf.add_line((start_point[0], -(start_point[1]+unit*i)), (start_point[0]+unit*(gird_length[0]-1), -(start_point[1]+unit*i)))

    def draw_pseudo_node(self, grids: List[List[Grid]], hatch_path: BoundaryPaths, dxf: Modelspace = None):
        width = 60
        mini_width = 30
        cover_width = 120
        num = 0
        for i in range(len(grids)):
            for j in range(len(grids[i])):
                if grids[i][j].electrode_index >= 0:
                    x = grids[i][j].real_x
                    y = -grids[i][j].real_y
                    if grids[i][j].covered is False:
                        if grids[i][j].corner:
                            hatch_path.add_polyline_path([(x, y-mini_width), (x+mini_width, y), (x, y+mini_width), (x-mini_width, y)])
                        else:
                            hatch_path.add_polyline_path([(x, y-width), (x+width, y), (x, y+width), (x-width, y)])
                    else:
                        hatch_path.add_polyline_path([(x, y-cover_width), (x+cover_width, y), (x, y+cover_width), (x-cover_width, y)])
                    num += 1
                # elif grids[i][j].close_electrode and dxf is not None:
                #     for next_grid in grids[i][j].neighbor:
                #         dxf.add_line([grids[i][j].real_x, -grids[i][j].real_y], [next_grid[0].real_x, -next_grid[0].real_y])
                # elif grids[i][j].close_electrode is False and dxf is not None:
                if dxf is not None:
                    for next_grid in grids[i][j].neighbor:
                        dxf.add_line([grids[i][j].real_x, -grids[i][j].real_y], [next_grid[0].real_x, -next_grid[0].real_y])

        print('grid num: ', num)

    def draw_pseudo_node_corner(self, grids: List[List[Grid]], hatch_path: BoundaryPaths):
        width = 60
        for i in range(len(grids)):
            for j in range(len(grids[i])):
                if grids[i][j].electrode_index >= 0 and grids[i][j].corner:
                    x = grids[i][j].real_x
                    y = -grids[i][j].real_y
                    hatch_path.add_polyline_path([(x, y-width), (x+width, y), (x, y+width), (x-width, y)])

    def draw_hub(self, hub: List[Hub], hatch_path: BoundaryPaths, dxf: Modelspace = None):
        width = 60
        for i in range(len(hub)):
            x = hub[i].real_x
            y = -hub[i].real_y
            hatch_path.add_polyline_path([(x, y-width), (x+width, y), (x, y+width), (x-width, y)])
            if dxf is not None:
                for next in hub[i].neighbor:
                    dxf.add_line([hub[i].real_x, -hub[i].real_y], [next[0].real_x, -next[0].real_y])

    def draw_tile(self, tile: List[List[Tile]], hatch_path: BoundaryPaths, dxf: Modelspace = None):
        width = 60
        for i in range(len(tile)):
            for j in range(len(tile[i])):
                x = tile[i][j].real_x
                y = -tile[i][j].real_y
                hatch_path.add_polyline_path([(x, y-width), (x+width, y), (x, y+width), (x-width, y)])
                if dxf is not None:
                    for next in tile[i][j].neighbor:
                        dxf.add_line([tile[i][j].real_x, -tile[i][j].real_y], [next[0].real_x, -next[0].real_y])

    def draw_all_wire(self, wire_list: List[Wire], dxf: Modelspace, line=False):
        if line is False:
            # draw wire
            for i in range(len(wire_list)):
                if i == 0:
                    self.draw_path(None, wire_list[i], wire_list[i+1], self.mini_width, self.mini_tan_offset, self.mini_dia_offset, dxf)
                elif i == len(wire_list) - 1:
                    self.draw_path(wire_list[i-1], wire_list[i], None, self.regular_width, self.regular_tan_offset, self.regular_dia_offset, dxf)
                elif i < 3:
                    self.draw_path(wire_list[i-1], wire_list[i], wire_list[i+1], self.mini_width, self.mini_tan_offset, self.mini_dia_offset, dxf)
                else:
                    self.draw_path(wire_list[i-1], wire_list[i], wire_list[i+1], self.regular_width,
                                   self.regular_tan_offset, self.regular_dia_offset, dxf)
        else:
            # draw line
            for wire in wire_list:
                dxf.add_line([wire.start_x, -wire.start_y], [wire.end_x, -wire.end_y])
