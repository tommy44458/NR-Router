from concurrent.futures import ThreadPoolExecutor, as_completed
from math import atan2, degrees
from operator import attrgetter, itemgetter
from typing import Any, Callable, Dict, List, NoReturn, Optional, Tuple, Union

from ezdxf.addons import r12writer

from degree import Degree, dia, direct_table
from draw import Draw
from electrode import Electrode
from grid import Grid, GridType
from hub import Hub
from model_mesh import ModelMesh
from pseudo_node import PseudoNode
from tile import Tile
from wire import Wire, WireDirect


class RoutingWire():
    def __init__(self, pseudo_node: PseudoNode, grid_array: List[List[Grid]], electrode_list: List[Electrode]):
        self.pseudo_node = pseudo_node
        self.grid_array = grid_array
        self.electrode_list = electrode_list
        self._reduce_times = 0

    def get_grid_by_point(self, point):
        """
            get grid by real point
        """
        grid_point = self.pseudo_node.get_grid_point(point, self.pseudo_node.unit)
        return self.grid_array[grid_point[0]][grid_point[1]]

    def get_grid_list_by_wire(self, start_point, end_point, remove_index) -> List[Grid]:
        """
            get grid list by real point: start to end
        """
        degree_wire = Degree.get_degree(start_point[0], -start_point[1], end_point[0], -end_point[1])
        point = [start_point[0], start_point[1]]
        ret = []
        if direct_table[degree_wire] == WireDirect.UP:
            while point[1] >= end_point[1]:
                ret.append(self.get_grid_by_point(point))
                point[1] -= self.pseudo_node.unit
        elif direct_table[degree_wire] == WireDirect.RIGHT:
            while point[0] <= end_point[0]:
                ret.append(self.get_grid_by_point(point))
                point[0] += self.pseudo_node.unit
        elif direct_table[degree_wire] == WireDirect.DOWN:
            while point[1] <= end_point[1]:
                ret.append(self.get_grid_by_point(point))
                point[1] += self.pseudo_node.unit
        elif direct_table[degree_wire] == WireDirect.LEFT:
            while point[0] >= end_point[0]:
                ret.append(self.get_grid_by_point(point))
                point[0] -= self.pseudo_node.unit
        elif direct_table[degree_wire] == WireDirect.RIGHTUP:
            while point[0] <= end_point[0]:
                ret.append(self.get_grid_by_point(point))
                point[0] += self.pseudo_node.unit
                point[1] -= self.pseudo_node.unit
        elif direct_table[degree_wire] == WireDirect.RIGHTDOWN:
            while point[0] <= end_point[0]:
                ret.append(self.get_grid_by_point(point))
                point[0] += self.pseudo_node.unit
                point[1] += self.pseudo_node.unit
        elif direct_table[degree_wire] == WireDirect.LEFTUP:
            while point[0] >= end_point[0]:
                ret.append(self.get_grid_by_point(point))
                point[0] -= self.pseudo_node.unit
                point[1] -= self.pseudo_node.unit
        elif direct_table[degree_wire] == WireDirect.LEFTDOWN:
            while point[0] >= end_point[0]:
                ret.append(self.get_grid_by_point(point))
                point[0] -= self.pseudo_node.unit
                point[1] += self.pseudo_node.unit

        ret.pop(remove_index)
        return ret

    def check_overlap(self, grid_list: List[Grid]):
        """
            check grid flow > 0 in grid list, means this grid has wire through
        """
        for grid in grid_list:
            if grid.flow == 1:
                return True
        return False

    def add_new_point_between_two_wire(self, new_point: list, wire_1: Wire, wire_2: Wire, grid_list_1: List[Grid], grid_list_2: List[Grid]):
        """
            add a new point between two wire, and set the grid list (new wire through) flow = 0
        """
        wire_1.end_x = new_point[0]
        wire_1.end_y = new_point[1]
        wire_2.start_x = wire_1.end_x
        wire_2.start_y = wire_1.end_y

        wire_1.grid_list.extend(grid_list_1)
        wire_2.grid_list.extend(grid_list_2)

        for grid in wire_1.grid_list:
            grid.flow = 1
        for grid in wire_2.grid_list:
            grid.flow = 1

    def remove_wire(self, wire_list: List[Wire], wire: Wire):
        """
            remove wire and reset grid.flow
        """
        for grid in wire.grid_list:
            grid.flow = 0
        wire_list.remove(wire)

    def reduce_single_wire_turn(self, electrode: Electrode):
        """
            reduce the turn for single wire
        """
        wire_list = electrode.routing_wire
        if len(wire_list) > 5:
            i = 0
            while i < len(wire_list) - 5:
                # get 4 wire
                wire_1 = wire_list[i]
                wire_2 = wire_list[i+1]
                wire_3 = wire_list[i+2]
                wire_4 = wire_list[i+3]

                # this is turn can be removed
                if wire_1.direct == wire_3.direct and wire_2.direct == wire_4.direct:
                    if wire_1.direct == WireDirect.LEFTDOWN:
                        offset = None
                        if wire_2.direct == WireDirect.LEFT:
                            offset = abs(wire_4.start_y - wire_1.end_y)
                        elif wire_2.direct == WireDirect.DOWN:
                            offset = abs(wire_4.start_x - wire_1.end_x)
                        if offset is not None:
                            new_point = [wire_1.end_x - offset, wire_1.end_y + offset]
                            new_wire_grid_list_1 = self.get_grid_list_by_wire([wire_1.end_x, wire_1.end_y], [new_point[0], new_point[1]], 0)
                            new_wire_grid_list_2 = self.get_grid_list_by_wire([new_point[0],  new_point[1]], [wire_4.start_x, wire_4.start_y], -1)
                            if self.check_overlap(new_wire_grid_list_1) is False and self.check_overlap(new_wire_grid_list_2) is False:
                                self.remove_wire(wire_list, wire_2)
                                self.remove_wire(wire_list, wire_3)
                                self.add_new_point_between_two_wire(new_point, wire_1, wire_4, new_wire_grid_list_1, new_wire_grid_list_2)
                                self._reduce_times += 1
                                continue

                    if wire_1.direct == WireDirect.RIGHTDOWN:
                        offset = None
                        if wire_2.direct == WireDirect.RIGHT:
                            offset = abs(wire_4.start_y - wire_1.end_y)
                        elif wire_2.direct == WireDirect.DOWN:
                            offset = abs(wire_4.start_x - wire_1.end_x)
                        if offset is not None:
                            new_point = [wire_1.end_x + offset, wire_1.end_y + offset]
                            new_wire_grid_list_1 = self.get_grid_list_by_wire([wire_1.end_x, wire_1.end_y], [new_point[0], new_point[1]], 0)
                            new_wire_grid_list_2 = self.get_grid_list_by_wire([new_point[0],  new_point[1]], [wire_4.start_x, wire_4.start_y], -1)
                            if self.check_overlap(new_wire_grid_list_1) is False and self.check_overlap(new_wire_grid_list_2) is False:
                                self.remove_wire(wire_list, wire_2)
                                self.remove_wire(wire_list, wire_3)
                                self.add_new_point_between_two_wire(new_point, wire_1, wire_4, new_wire_grid_list_1, new_wire_grid_list_2)
                                self._reduce_times += 1
                                continue

                    if wire_1.direct == WireDirect.LEFTUP:
                        offset = None
                        if wire_2.direct == WireDirect.LEFT:
                            offset = abs(wire_4.start_y - wire_1.end_y)
                        elif wire_2.direct == WireDirect.UP:
                            offset = abs(wire_4.start_x - wire_1.end_x)
                        if offset is not None:
                            new_point = [wire_1.end_x - offset, wire_1.end_y - offset]
                            new_wire_grid_list_1 = self.get_grid_list_by_wire([wire_1.end_x, wire_1.end_y], [new_point[0], new_point[1]], 0)
                            new_wire_grid_list_2 = self.get_grid_list_by_wire([new_point[0],  new_point[1]], [wire_4.start_x, wire_4.start_y], -1)
                            if self.check_overlap(new_wire_grid_list_1) is False and self.check_overlap(new_wire_grid_list_2) is False:
                                self.remove_wire(wire_list, wire_2)
                                self.remove_wire(wire_list, wire_3)
                                self.add_new_point_between_two_wire(new_point, wire_1, wire_4, new_wire_grid_list_1, new_wire_grid_list_2)
                                self._reduce_times += 1
                                continue

                    if wire_1.direct == WireDirect.RIGHTUP:
                        offset = None
                        if wire_2.direct == WireDirect.RIGHT:
                            offset = abs(wire_4.start_y - wire_1.end_y)
                        elif wire_2.direct == WireDirect.UP:
                            offset = abs(wire_4.start_x - wire_1.end_x)
                        if offset is not None:
                            new_point = [wire_1.end_x + offset, wire_1.end_y - offset]
                            new_wire_grid_list_1 = self.get_grid_list_by_wire([wire_1.end_x, wire_1.end_y], [new_point[0], new_point[1]], 0)
                            new_wire_grid_list_2 = self.get_grid_list_by_wire([new_point[0],  new_point[1]], [wire_4.start_x, wire_4.start_y], -1)
                            if self.check_overlap(new_wire_grid_list_1) is False and self.check_overlap(new_wire_grid_list_2) is False:
                                self.remove_wire(wire_list, wire_2)
                                self.remove_wire(wire_list, wire_3)
                                self.add_new_point_between_two_wire(new_point, wire_1, wire_4, new_wire_grid_list_1, new_wire_grid_list_2)
                                self._reduce_times += 1
                                continue

                    i += 1
                else:
                    i += 1

    def reduce_wire_turn(self) -> int:
        """
            reduce the turn for each wire
        """
        self._reduce_times = 0
        # executor = ThreadPoolExecutor(max_workers=8)
        for electrode in self.electrode_list:
            self.reduce_single_wire_turn(electrode)
            # executor.submit(self.reduce_single_wire_turn, electrode)

        # executor.shutdown(wait=True)
        return self._reduce_times

    def divide_start_wire(self):
        for electrode in self.electrode_list:
            wire_list = electrode.routing_wire
            divide_num = 0
            wire_index = 0
            unit_length = self.pseudo_node.unit
            while divide_num < 3 and wire_index < len(electrode.routing_wire):
                wire = wire_list[wire_index]
                _unit_length = unit_length / dia
                if wire.length() > _unit_length * 1.5:
                    if wire.direct == WireDirect.UP:
                        new_point = [wire.start_x, wire.start_y - unit_length]
                    elif wire.direct == WireDirect.RIGHT:
                        new_point = [wire.start_x + unit_length, wire.start_y]
                    elif wire.direct == WireDirect.DOWN:
                        new_point = [wire.start_x, wire.start_y + unit_length]
                    elif wire.direct == WireDirect.LEFT:
                        new_point = [wire.start_x - unit_length, wire.start_y]
                    elif wire.direct == WireDirect.RIGHTUP:
                        new_point = [wire.start_x + unit_length, wire.start_y - unit_length]
                    elif wire.direct == WireDirect.RIGHTDOWN:
                        new_point = [wire.start_x + unit_length, wire.start_y + unit_length]
                    elif wire.direct == WireDirect.LEFTUP:
                        new_point = [wire.start_x - unit_length, wire.start_y - unit_length]
                    elif wire.direct == WireDirect.LEFTDOWN:
                        new_point = [wire.start_x - unit_length, wire.start_y + unit_length]
                    new_wire_1 = Wire(wire.start_x, wire.start_y, new_point[0], new_point[1], wire.direct, wire.grid_list)
                    new_wire_2 = Wire(new_point[0], new_point[1], wire.end_x, wire.end_y, wire.direct, wire.grid_list)
                    wire_list.remove(wire)
                    wire_list.insert(wire_index, new_wire_2)
                    wire_list.insert(wire_index, new_wire_1)
                    divide_num += 1
                wire_index += 1

            # remove right angle
            for i in range(len(electrode.routing_wire) - 1):
                wire_1 = electrode.routing_wire[i]
                wire_2 = electrode.routing_wire[i+1]
                if wire_1.direct in (WireDirect.LEFT, WireDirect.RIGHT):
                    if wire_1.direct == WireDirect.LEFT and wire_2.direct == WireDirect.UP:
                        new_point_1 = [(wire_1.end_x + self.pseudo_node.unit / 2), wire_1.end_y]
                        new_point_2 = [wire_2.start_x, wire_2.start_y - self.pseudo_node.unit / 2]

                        wire_1.end_x = new_point_1[0]
                        wire_2.start_y = new_point_2[1]
                        new_wire = Wire(wire_1.end_x, wire_1.end_y, wire_2.start_x, wire_2.start_y, WireDirect.LEFTUP, wire_1.grid_list)
                        electrode.routing_wire.insert(i + 1, new_wire)
                    elif wire_1.direct == WireDirect.LEFT and wire_2.direct == WireDirect.DOWN:
                        new_point_1 = [(wire_1.end_x + self.pseudo_node.unit / 2), wire_1.end_y]
                        new_point_2 = [(wire_2.start_x), wire_2.start_y + self.pseudo_node.unit / 2]

                        wire_1.end_x = new_point_1[0]
                        wire_2.start_y = new_point_2[1]
                        new_wire = Wire(wire_1.end_x, wire_1.end_y, wire_2.start_x, wire_2.start_y, WireDirect.LEFTDOWN, wire_1.grid_list)
                        electrode.routing_wire.insert(i + 1, new_wire)
                    elif wire_1.direct == WireDirect.RIGHT and wire_2.direct == WireDirect.DOWN:
                        new_point_1 = [(wire_1.end_x - self.pseudo_node.unit / 2), wire_1.end_y]
                        new_point_2 = [(wire_2.start_x), wire_2.start_y + self.pseudo_node.unit / 2]

                        wire_1.end_x = new_point_1[0]
                        wire_2.start_y = new_point_2[1]
                        new_wire = Wire(wire_1.end_x, wire_1.end_y, wire_2.start_x, wire_2.start_y, WireDirect.RIGHTDOWN, wire_1.grid_list)
                        electrode.routing_wire.insert(i + 1, new_wire)
                    elif wire_1.direct == WireDirect.RIGHT and wire_2.direct == WireDirect.UP:
                        new_point_1 = [(wire_1.end_x - self.pseudo_node.unit / 2), wire_1.end_y]
                        new_point_2 = [(wire_2.start_x), wire_2.start_y - self.pseudo_node.unit / 2]

                        wire_1.end_x = new_point_1[0]
                        wire_2.start_y = new_point_2[1]
                        new_wire = Wire(wire_1.end_x, wire_1.end_y, wire_2.start_x, wire_2.start_y, WireDirect.RIGHTUP, wire_1.grid_list)
                        electrode.routing_wire.insert(i + 1, new_wire)
