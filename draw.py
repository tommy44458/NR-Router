import numpy as np
from typing import Any, Optional, Tuple, Union, List, Dict, Callable, NoReturn
from ortools.graph.pywrapgraph import SimpleMinCostFlow
from ezdxf.addons.r12writer import R12FastStreamWriter
from ezdxf.document import Modelspace
from ezdxf.entities import BoundaryPaths
from ezdxf.path import from_hatch_boundary_path
from math import atan2, degrees

from wire import Wire
from grid import Grid, GridType
from hub import Hub
from tile import Tile

from degree import Degree, wire_offset_table
from electrode import Electrode


class Draw():
    def __init__(self, mim_cost_max_flow_solver: SimpleMinCostFlow.SolveMaxFlowWithMinCost, min_cost_flow: SimpleMinCostFlow,
                 top_block_shift: list, mid_block_shift: list, down_block_shift: list, tile_unit: int,
                 contactpad_unit: int, routing_wire: List[List[Wire]], wire_width: float, mini_wire_width: float):
        # mcmf
        self.mim_cost_max_flow_solver = mim_cost_max_flow_solver
        self.min_cost_flow = min_cost_flow

        # routing path from electrode to contact pad
        self.routing_wire = routing_wire

        # chip config
        self.top_block_shift = top_block_shift
        self.mid_block_shift = mid_block_shift
        self.down_block_shift = down_block_shift
        self.tile_unit = tile_unit
        self.contactpad_unit = contactpad_unit
        self.mini_width = mini_wire_width
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

    def draw_path(self, previous_wire: Wire, wire: Wire, next_wire: Wire, width: float, dxf: Modelspace):
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
            # align to hub axis (contact pad section)
            if abs(wire.end_y - next_wire.end_y) < abs(wire.end_x - next_wire.end_x):
                next_point[1] = end_point[1]
            elif abs(wire.end_y - next_wire.end_y) > abs(wire.end_x - next_wire.end_x):
                next_point[0] = end_point[0]
            degree_end_next = Degree.getdegree(end_point[0], end_point[1], next_point[0], next_point[1])
        else:
            if abs(wire.end_y - wire.start_y) < abs(wire.end_x - wire.start_x):
                end_point[1] = wire.start_y
            elif abs(wire.end_y - wire.start_y) > abs(wire.end_x - wire.start_x):
                end_point[0] = wire.start_x
            degree_end_next = None

        # no wire need to be drow
        if start_point == end_point:
            return None

        degree_start_end = Degree.getdegree(start_point[0], start_point[1], end_point[0], end_point[1])

        tan = self.regular_tan_offset
        dia_offset = self.regular_dia_offset

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

    def draw_electrodes(self, electrodes: List[list], shape_lib: dict, dxf: Modelspace):
        for elec in electrodes:
            shape = elec[0]
            x = elec[1]
            y = -elec[2]
            vertex_order = []
            for shape_p in shape_lib[shape]:
                vertex_order.append((x + shape_p[0], y - shape_p[1]))
            dxf.add_polyline2d(vertex_order, close=True)

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
        num = 0
        for i in range(len(grids)):
            for j in range(len(grids[i])):
                if grids[i][j].electrode_index >= 0:
                    x = grids[i][j].real_x
                    y = -grids[i][j].real_y
                    if grids[i][j].corner:
                        hatch_path.add_polyline_path([(x, y-mini_width), (x+mini_width, y), (x, y+mini_width), (x-mini_width, y)])
                    else:
                        hatch_path.add_polyline_path([(x, y-width), (x+width, y), (x, y+width), (x-width, y)])
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

    def draw_all_wire(self, wire_list: List[Wire], dxf: Modelspace):
        for wire in wire_list:
            dxf.add_line([wire.start_x, -wire.start_y], [wire.end_x, -wire.end_y])

    def draw_all_path(self, dxf, grids2):
        mim_cost_max_flow_solver = self.mim_cost_max_flow_solver
        min_cost_flow = self.min_cost_flow
        mid_block_shift = self.mid_block_shift
        tile_unit = self.tile_unit
        routing_wire = self.routing_wire

        connect = 0
        if mim_cost_max_flow_solver == min_cost_flow.OPTIMAL:
            for i in range(len(routing_wire)):
                # tune path start
                # reduce change way
                if len(routing_wire[i]) == 0:
                    return False

                # BUG 一些線斷消失
                # # 有起始線
                # abs(routing_wire[i][0].start_x - routing_wire[i][0].end_x) != 0
                # abs(routing_wire[i][0].start_y - routing_wire[i][0].end_y) != 0
                # # 起始線與下一條線有轉彎
                # (np.sign(routing_wire[i][0].start_x - routing_wire[i][0].end_x) != np.sign(routing_wire[i][1].start_x-routing_wire[i][1].end_x))
                # # 起始線下下條線為垂直線
                # (routing_wire[i][2].start_x == routing_wire[i][2].end_x)

                # if abs(routing_wire[i][0].start_x-routing_wire[i][0].end_x)!=0 and abs(routing_wire[i][0].start_y-routing_wire[i][0].end_y)!=0 and (np.sign(routing_wire[i][0].start_x-routing_wire[i][0].end_x)!=np.sign(routing_wire[i][1].start_x-routing_wire[i][1].end_x)) and (routing_wire[i][2].start_x==routing_wire[i][2].end_x):
                #     routing_wire[i][0].end_x = routing_wire[i][2].start_x
                #     routing_wire[i][2].start_y = routing_wire[i][0].start_y + abs(routing_wire[i][2].start_x-routing_wire[i][0].start_x) * np.sign(routing_wire[i][2].start_y-routing_wire[i][0].start_y)
                #     routing_wire[i][0].end_y = routing_wire[i][2].start_y
                #     del routing_wire[i][1]
                # BUG 一些線斷消失

                # if abs(routing_wire[i][1].start_x-routing_wire[i][1].end_x)!=abs(routing_wire[i][1].start_y-routing_wire[i][1].end_y) and abs(routing_wire[i][1].start_x-routing_wire[i][1].end_x)!=0 and abs(routing_wire[i][1].start_y-routing_wire[i][1].end_y)!=0:
                #     if abs(routing_wire[i][2].end_x-routing_wire[i][1].start_x)>abs(routing_wire[i][2].end_y-routing_wire[i][1].start_y):
                #         routing_wire[i][1].end_x = routing_wire[i][1].start_x+abs(routing_wire[i][2].end_y-routing_wire[i][1].start_y)*np.sign(routing_wire[i][2].end_x-routing_wire[i][1].start_x)
                #         routing_wire[i][1].end_y = routing_wire[i][2].end_y
                #         routing_wire[i][2].start_x = routing_wire[i][1].start_x+abs(routing_wire[i][2].end_y-routing_wire[i][1].start_y)*np.sign(routing_wire[i][2].end_x-routing_wire[i][1].start_x)
                #         routing_wire[i][2].start_y = routing_wire[i][2].end_y
                #     else:
                #         routing_wire[i][1].end_x = routing_wire[i][2].end_x
                #         routing_wire[i][1].end_y = routing_wire[i][1].start_y+abs(routing_wire[i][2].end_x-routing_wire[i][1].start_x)*np.sign(routing_wire[i][2].end_y-routing_wire[i][1].start_y)
                #         routing_wire[i][2].start_x = routing_wire[i][2].end_x
                #         routing_wire[i][2].start_y = routing_wire[i][1].start_y+abs(routing_wire[i][2].end_x-routing_wire[i][1].start_x)*np.sign(routing_wire[i][2].end_y-routing_wire[i][1].start_y)

                # for j in range(len(routing_wire[i])-2):
                #     if np.sign(routing_wire[i][j].start_x-routing_wire[i][j].end_x)!=np.sign(routing_wire[i][j+1].start_x-routing_wire[i][j+1].end_x) and (routing_wire[i][j].start_x-routing_wire[i][j].end_x)!=0:
                #         if abs(routing_wire[i][j+1].end_x-routing_wire[i][j].start_x)>abs(routing_wire[i][j+1].end_y-routing_wire[i][j].start_y):
                #             routing_wire[i][j].end_x = routing_wire[i][j].start_x+abs(routing_wire[i][j+1].end_y-routing_wire[i][j].start_y)*np.sign(routing_wire[i][j+1].end_x-routing_wire[i][j].start_x)
                #             routing_wire[i][j].end_y = routing_wire[i][j+1].end_y
                #             routing_wire[i][j+1].start_x = routing_wire[i][j].start_x+abs(routing_wire[i][j+1].end_y-routing_wire[i][j].start_y)*np.sign(routing_wire[i][j+1].end_x-routing_wire[i][j].start_x)
                #             routing_wire[i][j+1].start_y = routing_wire[i][j+1].end_y
                #         else:
                #             routing_wire[i][j].end_x = routing_wire[i][j+1].end_x
                #             routing_wire[i][j].end_y = routing_wire[i][j].start_y+abs(routing_wire[i][j+1].end_x-routing_wire[i][j].start_x)*np.sign(routing_wire[i][j+1].end_y-routing_wire[i][j].start_y)
                #             routing_wire[i][j+1].start_x = routing_wire[i][j+1].end_x
                #             routing_wire[i][j+1].start_y = routing_wire[i][j].start_y+abs(routing_wire[i][j+1].end_x-routing_wire[i][j].start_x)*np.sign(routing_wire[i][j+1].end_y-routing_wire[i][j].start_y)

                # for j in range(len(routing_wire[i])-2):
                #     if abs(routing_wire[i][j].start_x-routing_wire[i][j].end_x) == 0 and abs(routing_wire[i][j+1].start_y-routing_wire[i][j+1].end_y) == 0:
                #         routing_wire[i][j].end_x = routing_wire[i][j].start_x+abs(routing_wire[i][j].end_y-routing_wire[i][j].start_y)*np.sign(routing_wire[i][j+1].end_x-routing_wire[i][j+1].start_x)
                #         routing_wire[i][j+1].start_x = routing_wire[i][j].end_x
                #     if abs(routing_wire[i][j].start_y-routing_wire[i][j].end_y) == 0 and abs(routing_wire[i][j+1].start_x-routing_wire[i][j+1].end_x) == 0:
                #         routing_wire[i][j].end_y = routing_wire[i][j].start_y+abs(routing_wire[i][j].end_x-routing_wire[i][j].start_x)*np.sign(routing_wire[i][j+1].end_y-routing_wire[i][j+1].start_y)
                #         routing_wire[i][j+1].start_y = routing_wire[i][j].end_y

                # for j in range(len(routing_wire[i])):
                #     if (routing_wire[i][j].start_x-routing_wire[i][j].end_x)==0 and abs(routing_wire[i][j].start_y-routing_wire[i][j].end_y)==250:
                #         #dxf.add_circle(center=(routing_wire[i][j].start_x, -routing_wire[i][j].start_y), radius = 250.0)
                #         if np.sign(routing_wire[i][j-1].start_x-routing_wire[i][j-1].end_x)*np.sign(routing_wire[i][j+1].start_x-routing_wire[i][j+1].end_x)==-1:
                #             #dxf.add_circle(center=(routing_wire[i][j].start_x, -routing_wire[i][j].start_y), radius = 250.0)
                #             routing_wire[i][j-1].end_y = routing_wire[i][j].start_y+abs(routing_wire[i][j+1].end_x-routing_wire[i][j].start_x)*np.sign(routing_wire[i][j].start_y-routing_wire[i][j].end_y)
                #             routing_wire[i][j].start_y = routing_wire[i][j-1].end_y
                #             routing_wire[i][j-1].end_x = routing_wire[i][j+1].end_x
                #             routing_wire[i][j].start_x = routing_wire[i][j+1].end_x
                #             routing_wire[i][j].end_x = routing_wire[i][j+1].end_x
                #             routing_wire[i][j+1].start_x = routing_wire[i][j+1].end_x
                #         if routing_wire[i][j-1].start_x!=routing_wire[i][j-1].end_x and routing_wire[i][j+1].start_x!=routing_wire[i][j+1].end_x:
                #             #dxf.add_circle(center=(routing_wire[i][j].start_x, -routing_wire[i][j].start_y), radius = 250.0)
                #             routing_wire[i][j-1].end_x = routing_wire[i][j+1].end_x
                #             routing_wire[i][j-1].end_y = routing_wire[i][j-1].end_y+abs(routing_wire[i][j+1].end_x-routing_wire[i][j+1].start_x)*np.sign(routing_wire[i][j+1].end_y-routing_wire[i][j+1].start_y)
                #             routing_wire[i][j].start_x = routing_wire[i][j-1].end_x
                #             routing_wire[i][j].start_y = routing_wire[i][j-1].end_y
                #             routing_wire[i][j].end_x = routing_wire[i][j+1].end_x
                #             routing_wire[i][j+1].start_x = routing_wire[i][j+1].end_x

                #     if routing_wire[i][j].end_y > mid_block_shift[1] and routing_wire[i][j].end_y < mid_block_shift[1]+46000:
                #         S_grid_x = (routing_wire[i][j].start_x-mid_block_shift[0])//tile_unit
                #         S_grid_y = (routing_wire[i][j].start_y-mid_block_shift[1])//tile_unit
                #         T_grid_x = (routing_wire[i][j].end_x-mid_block_shift[0])//tile_unit
                #         T_grid_y = (routing_wire[i][j].end_y-mid_block_shift[1])//tile_unit
                #         grids2[S_grid_x,S_grid_y].flow=1
                #         grids2[T_grid_x,T_grid_y].flow=1

                # #|      |    j-1        |       \   j+1
                # #\  ->  |    j     or   \  ->    |  j
                # # |      \   j+1         |       |  j-1

                # for j in range(3,len(routing_wire[i])):
                #     if routing_wire[i][j].end_y > mid_block_shift[1]+tile_unit and routing_wire[i][j].end_y < mid_block_shift[1]+46000-tile_unit:
                #         if routing_wire[i][j-1].start_x==routing_wire[i][j-1].end_x and abs(routing_wire[i][j].start_x-routing_wire[i][j].end_x)==abs(routing_wire[i][j].start_y-routing_wire[i][j].end_y):
                #             check_grid_x = (routing_wire[i][j].start_x-mid_block_shift[0])//tile_unit
                #             check_grid_y = (routing_wire[i][j].end_y-mid_block_shift[1])//tile_unit
                #             if grids2[check_grid_x,check_grid_y].flow == 0 and grids2[check_grid_x,check_grid_y].safe_distance==0 and grids2[check_grid_x,check_grid_y].safe_distance2==0:
                #                 k=1
                #                 no_path=0
                #                 while j+k < len(routing_wire[i]) and routing_wire[i][j+k].start_x!=routing_wire[i][j+k].end_x:
                #                     check_grid_x = (routing_wire[i][j+k].start_x-mid_block_shift[0])//tile_unit
                #                     check_grid_y = (routing_wire[i][j+k].end_y-mid_block_shift[1])//tile_unit
                #                     try:
                #                         if grids2[check_grid_x,check_grid_y].flow != 0:
                #                         # or grids2[check_grid_x,check_grid_y].safe_distance2==1 or grids2[check_grid_x,check_grid_y].safe_distance==1:
                #                             no_path=1
                #                         if routing_wire[i][j+k].start_y < mid_block_shift[1]+tile_unit*2 or routing_wire[i][j+k].start_y > mid_block_shift[1]+46000-tile_unit*2:
                #                             no_path=1
                #                     except:
                #                         break
                #                     finally:
                #                         k+=1
                #                 if no_path==0:
                #                     #check_grid_flow=0
                #                     grids2[check_grid_x,check_grid_y].flow=1
                #                     grids2[check_grid_x+np.sign(routing_wire[i][j].end_x-routing_wire[i][j].start_x),check_grid_y].flow=0
                #                     routing_wire[i][j].end_x = routing_wire[i][j].start_x
                #                     k=1
                #                     while j+k < len(routing_wire[i]) and routing_wire[i][j+k].start_x!=routing_wire[i][j+k].end_x:# and check_grid_flow==0:
                #                         check_grid_x = (routing_wire[i][j+k].start_x-mid_block_shift[0])//tile_unit
                #                         check_grid_y = (routing_wire[i][j+k].end_y-mid_block_shift[1])//tile_unit
                #                         grids2[check_grid_x,check_grid_y].flow=1
                #                         grids2[check_grid_x+np.sign(routing_wire[i][j+k].end_x-routing_wire[i][j+k].start_x),check_grid_y].flow=0
                #                         routing_wire[i][j+k].end_x = routing_wire[i][j+k].start_x
                #                         routing_wire[i][j+k].start_x = routing_wire[i][j+k-1].end_x
                #                         k+=1
                #                         if (j+k)>=(len(routing_wire[i])-1):
                #                             break
                #                         if routing_wire[i][j+k].start_y < mid_block_shift[1]+tile_unit*2 or routing_wire[i][j+k].start_y > mid_block_shift[1]+46000-tile_unit*2:
                #                             break
                #                     routing_wire[i][j+k].start_x = routing_wire[i][j+k-1].end_x

                # #|     |    j+1           | 	 |
                # #\  -> |    j      or     /  ->  |
                # # |     \   j-1          | 		/

                # for j in range(len(routing_wire[i])):
                #     if (routing_wire[i][j].start_x-routing_wire[i][j].end_x)==0 and abs(routing_wire[i][j].start_y-routing_wire[i][j].end_y)==250:
                #         if routing_wire[i][j-1].start_x!=routing_wire[i][j-1].end_x and routing_wire[i][j+1].start_x!=routing_wire[i][j+1].end_x and np.sign(routing_wire[i][j-1].end_x-routing_wire[i][j-1].start_x)==np.sign(routing_wire[i][j+1].end_x-routing_wire[i][j+1].start_x):
                #             if grids2[(((routing_wire[i][j].start_x-mid_block_shift[0])//tile_unit)+np.sign(routing_wire[i][j-1].end_x-routing_wire[i][j-1].start_x)), ((routing_wire[i][j].start_y-mid_block_shift[1])//tile_unit)].flow==0:
                #                 #dxf.add_circle(center=(routing_wire[i][j].start_x, -routing_wire[i][j].start_y), radius = 250.0)
                #                 routing_wire[i][j-1].end_x = routing_wire[i][j+1].end_x
                #                 routing_wire[i][j-1].end_y = routing_wire[i][j-1].end_y+abs(routing_wire[i][j+1].end_x-routing_wire[i][j+1].start_x)*np.sign(routing_wire[i][j+1].end_y-routing_wire[i][j+1].start_y)
                #                 routing_wire[i][j].start_x = routing_wire[i][j-1].end_x
                #                 routing_wire[i][j].start_y = routing_wire[i][j-1].end_y
                #                 routing_wire[i][j].end_x = routing_wire[i][j+1].end_x
                #                 routing_wire[i][j+1].start_x = routing_wire[i][j+1].end_x

                # for j in range(len(routing_wire[i])-1):
                #     if (routing_wire[i][j].start_x-routing_wire[i][j].end_x)==0 and abs(routing_wire[i][j].start_y-routing_wire[i][j].end_y)==250:
                #         #dxf.add_circle(center=(routing_wire[i][j].start_x, -routing_wire[i][j].start_y), radius = 250.0)
                #         if np.sign(routing_wire[i][j-1].start_x-routing_wire[i][j-1].end_x)*np.sign(routing_wire[i][j+1].start_x-routing_wire[i][j+1].end_x)==-1:
                #             #dxf.add_circle(center=(routing_wire[i][j].start_x, -routing_wire[i][j].start_y), radius = 250.0)
                #             routing_wire[i][j-1].end_y = routing_wire[i][j].start_y+abs(routing_wire[i][j+1].end_x-routing_wire[i][j].start_x)*np.sign(routing_wire[i][j].start_y-routing_wire[i][j].end_y)
                #             routing_wire[i][j].start_y = routing_wire[i][j-1].end_y
                #             routing_wire[i][j-1].end_x = routing_wire[i][j+1].end_x
                #             routing_wire[i][j].start_x = routing_wire[i][j+1].end_x
                #             routing_wire[i][j].end_x = routing_wire[i][j+1].end_x
                #             routing_wire[i][j+1].start_x = routing_wire[i][j+1].end_x
                #     elif (routing_wire[i][j].start_x-routing_wire[i][j].end_x)!=0 and np.sign(routing_wire[i][j].start_x-routing_wire[i][j].end_x)*np.sign(routing_wire[i][j+1].start_x-routing_wire[i][j+1].end_x)==-1:
                #         routing_wire[i][j].end_x = routing_wire[i][j].start_x
                #         routing_wire[i][j+1].start_x = routing_wire[i][j].end_x

                # contact pad wire fix

                if routing_wire[i][-1].start_x != routing_wire[i][-1].end_x:
                    routing_wire[i][-1].start_y = routing_wire[i][-1].end_y+np.sign(
                        routing_wire[i][-1].start_y-routing_wire[i][-1].end_y)*abs(routing_wire[i][-1].start_x-routing_wire[i][-1].end_x)
                    routing_wire[i][-2].end_y = routing_wire[i][-1].start_y

                for j in range(len(routing_wire[i])-5, len(routing_wire[i])-1):
                    if (routing_wire[i][j].start_x-routing_wire[i][j].end_x) != 0 and (routing_wire[i][j].start_y-routing_wire[i][j].end_y) != 0 and abs(routing_wire[i][j].start_x-routing_wire[i][j].end_x) != abs(routing_wire[i][j].start_y-routing_wire[i][j].end_y):
                        #dxf.add_circle(center=(routing_wire[i][j].start_x, -routing_wire[i][j].start_y), radius = 250.0)
                        routing_wire[i][j].end_y = routing_wire[i][j].start_y+np.sign(
                            routing_wire[i][j].end_y-routing_wire[i][j].start_y)*abs(routing_wire[i][j+1].start_x-routing_wire[i][j].start_x)
                    if j == 1:
                        routing_wire[i][j -
                                        1].end_y = routing_wire[i][j].start_y
                        routing_wire[i][j -
                                        1].end_x = routing_wire[i][j].start_x
                    if j == len(routing_wire[i]) - 2:
                        routing_wire[i][j +
                                        1].start_y = routing_wire[i][j].end_y
                        routing_wire[i][j +
                                        1].start_x = routing_wire[i][j].end_x

                for j in range(len(routing_wire[i])-7, len(routing_wire[i])-2):
                    routing_wire[i][j].end_x = routing_wire[i][j+1].start_x
                    routing_wire[i][j].end_y = routing_wire[i][j+1].start_y

                # contact pad wire fix

                # 讓每條線連接一起
                # for j in range(len(routing_wire[i])-2):
                #     routing_wire[i][j+1].start_x = routing_wire[i][j].end_x
                #     routing_wire[i][j+1].start_y = routing_wire[i][j].end_y

                # for j in range(len(routing_wire[i])-2):
                #     if j <= len(routing_wire[i])-2:
                #         deg1 = Degree.getdegree(routing_wire[i][j].start_x, routing_wire[i][j].start_y, routing_wire[i][j].end_x, routing_wire[i][j].end_y)
                #         deg2 = Degree.getdegree(routing_wire[i][j+1].start_x, routing_wire[i][j+1].start_y, routing_wire[i][j+1].end_x, routing_wire[i][j+1].end_y)
                #         if abs(deg1[0] - deg2[0]) == 1 and abs(deg1[1] - deg2[1]):
                #             routing_wire[i][j+1].start_y = routing_wire[i][j+1].start_y - (routing_wire[i][j+1].end_x - routing_wire[i][j+1].start_x)
                #             routing_wire[i][j].end_y = routing_wire[i][j+1].start_y
                #             routing_wire[i][j].end_x = routing_wire[i][j+1].start_x

                for j in range(1, len(routing_wire[i])-2):
                    deg = Degree.getdegree(routing_wire[i][j].start_x, routing_wire[i]
                                           [j].start_y, routing_wire[i][j].end_x, routing_wire[i][j].end_y)
                    if abs(deg[0] - deg[1]) != 1:
                        if abs(deg[0]) > 0.7072 or abs(deg[1]) > 0.7072:
                            if routing_wire[i][j].end_x < routing_wire[i][j].start_x:
                                c = 1
                                if routing_wire[i][j].end_y > routing_wire[i][j].start_y:
                                    c = -1
                                if j < len(routing_wire[i]) - 2 and j > 1:
                                    dis_x = routing_wire[i][j].end_x - \
                                        routing_wire[i][j].start_x
                                    dis_y = routing_wire[i][j].end_y - \
                                        routing_wire[i][j].start_y
                                    if routing_wire[i][j+1].start_x == routing_wire[i][j+1].end_x:
                                        routing_wire[i][j].end_y = routing_wire[i][j].start_y + (
                                            dis_x * c)
                                        routing_wire[i][j +
                                                        1].start_y = routing_wire[i][j].end_y
                                    else:
                                        routing_wire[i][j].end_x = routing_wire[i][j].start_x + (
                                            dis_y * c)
                                        routing_wire[i][j +
                                                        1].start_x = routing_wire[i][j].end_x

                                if j < len(routing_wire[i]) - 2:
                                    dis_x = routing_wire[i][j].end_x - \
                                        routing_wire[i][j].start_x
                                    dis_y = routing_wire[i][j].end_y - \
                                        routing_wire[i][j].start_y
                                    if abs(dis_x) < abs(dis_y):
                                        routing_wire[i][j].end_y = routing_wire[i][j].start_y + (
                                            dis_x * c)
                                        routing_wire[i][j +
                                                        1].start_y = routing_wire[i][j].end_y
                                    else:
                                        routing_wire[i][j].end_x = routing_wire[i][j].start_x + (
                                            dis_y * c)
                                        routing_wire[i][j +
                                                        1].start_x = routing_wire[i][j].end_x
                            else:
                                c = -1
                                if routing_wire[i][j].end_y > routing_wire[i][j].start_y:
                                    c = 1
                                if j < len(routing_wire[i]) - 2 and j > 1:
                                    dis_x = routing_wire[i][j].end_x - \
                                        routing_wire[i][j].start_x
                                    dis_y = routing_wire[i][j].end_y - \
                                        routing_wire[i][j].start_y
                                    if routing_wire[i][j+1].start_x == routing_wire[i][j+1].end_x:
                                        routing_wire[i][j].end_y = routing_wire[i][j].start_y + (
                                            dis_x * c)
                                        routing_wire[i][j +
                                                        1].start_y = routing_wire[i][j].end_y
                                    else:
                                        routing_wire[i][j].end_x = routing_wire[i][j].start_x + (
                                            dis_y * c)
                                        routing_wire[i][j +
                                                        1].start_x = routing_wire[i][j].end_x

                                if j < len(routing_wire[i]) - 2:
                                    dis_x = routing_wire[i][j].end_x - \
                                        routing_wire[i][j].start_x
                                    dis_y = routing_wire[i][j].end_y - \
                                        routing_wire[i][j].start_y
                                    if abs(dis_x) < abs(dis_y):
                                        routing_wire[i][j].end_y = routing_wire[i][j].start_y + (
                                            dis_x * c)
                                        routing_wire[i][j +
                                                        1].start_y = routing_wire[i][j].end_y
                                    else:
                                        routing_wire[i][j].end_x = routing_wire[i][j].start_x + (
                                            dis_y * c)
                                        routing_wire[i][j +
                                                        1].start_x = routing_wire[i][j].end_x

                # BUG 一直轉彎
                # for j in range(len(routing_wire[i])-1):
                #     if (routing_wire[i][j].start_x-routing_wire[i][j].end_x)!=0 and (routing_wire[i][j].start_y-routing_wire[i][j].end_y)!=0 and abs(routing_wire[i][j].start_x-routing_wire[i][j].end_x)!=abs(routing_wire[i][j].start_y-routing_wire[i][j].end_y):
                #         #dxf.add_circle(center=(routing_wire[i][j].start_x, -routing_wire[i][j].start_y), radius = 250.0)
                #         routing_wire[i][j].end_y = routing_wire[i][j].start_y+np.sign(routing_wire[i][j].end_y-routing_wire[i][j].start_y)*abs(routing_wire[i][j+1].start_x-routing_wire[i][j].start_x)
                #         routing_wire[i][j+1].start_y = routing_wire[i][j].end_y
                # draw path
                draw_second = 0
                for j in range(len(routing_wire[i])):
                    if j == 0:
                        self.draw_path(None, routing_wire[i][j], routing_wire[i][j+1], self.regular_width, dxf)
                        draw_second += 1
                    elif j == len(routing_wire[i])-1:
                        self.draw_path(routing_wire[i][j-1], routing_wire[i][j], None, self.regular_width, dxf)
                    elif draw_second <= 3:
                        self.draw_path(routing_wire[i][j-1], routing_wire[i][j], routing_wire[i][j+1], self.regular_width, dxf)
                        draw_second += 1
                        connect = 1
                    else:
                        self.draw_path(routing_wire[i][j-1], routing_wire[i][j], routing_wire[i][j+1], self.regular_width, dxf)
