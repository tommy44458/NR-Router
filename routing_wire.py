from config import WireDirect
from degree import Degree, dia, direct_table
from electrode import Electrode
from grid import Grid
from pseudo_node import PseudoNode
from wire import Wire


class RoutingWire():
    """Routing wire class.
    """
    def __init__(self, pseudo_node: PseudoNode, grid_list: list[list[Grid]], electrode_list: list[Electrode]):
        self.pseudo_node: PseudoNode = pseudo_node
        self.grid_list: list[list[Grid]] = grid_list
        self.electrode_list: list[Electrode] = electrode_list
        self._reduce_times: int = 0

    def get_grid_by_point(self, point: tuple) -> Grid:
        """Get grid by real point.

        Args:
            point (tuple): real point

        Returns:
            Grid: the grid
        """
        grid_point = self.pseudo_node.get_grid_point(point, self.pseudo_node.unit)
        return self.grid_list[grid_point[0]][grid_point[1]]

    def get_grid_list_by_wire(self, start_point: tuple, end_point: tuple, remove_index: int) -> list[Grid]:
        """Get grid list by wire.

        Args:
            start_point (tuple): start point
            end_point (tuple): end point
            remove_index (int): remove index

        Returns:
            list[Grid]: grid list
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
        elif direct_table[degree_wire] == WireDirect.BOTTOM:
            while point[1] <= end_point[1]:
                ret.append(self.get_grid_by_point(point))
                point[1] += self.pseudo_node.unit
        elif direct_table[degree_wire] == WireDirect.LEFT:
            while point[0] >= end_point[0]:
                ret.append(self.get_grid_by_point(point))
                point[0] -= self.pseudo_node.unit
        elif direct_table[degree_wire] == WireDirect.TOP_RIGHT:
            while point[0] <= end_point[0]:
                ret.append(self.get_grid_by_point(point))
                point[0] += self.pseudo_node.unit
                point[1] -= self.pseudo_node.unit
        elif direct_table[degree_wire] == WireDirect.BOTTOM_RIGHT:
            while point[0] <= end_point[0]:
                ret.append(self.get_grid_by_point(point))
                point[0] += self.pseudo_node.unit
                point[1] += self.pseudo_node.unit
        elif direct_table[degree_wire] == WireDirect.TOP_LEFT:
            while point[0] >= end_point[0]:
                ret.append(self.get_grid_by_point(point))
                point[0] -= self.pseudo_node.unit
                point[1] -= self.pseudo_node.unit
        elif direct_table[degree_wire] == WireDirect.BOTTOM_LEFT:
            while point[0] >= end_point[0]:
                ret.append(self.get_grid_by_point(point))
                point[0] -= self.pseudo_node.unit
                point[1] += self.pseudo_node.unit

        ret.pop(remove_index)
        return ret

    def check_overlap(self, grid_list: list[Grid]) -> bool:
        """Check grid flow > 0 in grid list, means this grid has wire through

        Args:
            grid_list (list[Grid]): grid list

        Returns:
            bool: True if has wire through
        """
        for grid in grid_list:
            if grid.flow == 1:
                return True
        return False

    def add_new_point_between_two_wire(self, new_point: list, wire_1: Wire, wire_2: Wire, grid_list_1: list[Grid], grid_list_2: list[Grid]):
        """Add a new point between two wire, and set the grid list (new wire through) flow = 0

        Args:
            new_point (list): new point
            wire_1 (Wire): wire 1
            wire_2 (Wire): wire 2
            grid_list_1 (list[Grid]): grid list 1
            grid_list_2 (list[Grid]): grid list 2
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

    def remove_wire(self, wire_list: list[Wire], wire: Wire):
        """Remove wire and reset grid.flow

        Args:
            wire_list (list[Wire]): wire list
            wire (Wire): wire
        """
        for grid in wire.grid_list:
            grid.flow = 0
        wire_list.remove(wire)

    def reduce_single_wire_turn(self, electrode: Electrode):
        """Reduce the turn for single wire

        Args:
            electrode (Electrode): electrode
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
                    if wire_1.direct == WireDirect.BOTTOM_LEFT:
                        offset = None
                        if wire_2.direct == WireDirect.LEFT:
                            offset = abs(wire_4.start_y - wire_1.end_y)
                        elif wire_2.direct == WireDirect.BOTTOM:
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

                    if wire_1.direct == WireDirect.BOTTOM_RIGHT:
                        offset = None
                        if wire_2.direct == WireDirect.RIGHT:
                            offset = abs(wire_4.start_y - wire_1.end_y)
                        elif wire_2.direct == WireDirect.BOTTOM:
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

                    if wire_1.direct == WireDirect.TOP_LEFT:
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

                    if wire_1.direct == WireDirect.TOP_RIGHT:
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
        """Reduce the turn for each wire

        Returns:
            int: reduce times
        """
        self._reduce_times = 0
        # executor = ThreadPoolExecutor(max_workers=8)
        for electrode in self.electrode_list:
            self.reduce_single_wire_turn(electrode)
            # executor.submit(self.reduce_single_wire_turn, electrode)

        # executor.shutbottom(wait=True)
        return self._reduce_times

    def divide_start_wire(self):
        """Divide the start wire.
        """
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
                    elif wire.direct == WireDirect.BOTTOM:
                        new_point = [wire.start_x, wire.start_y + unit_length]
                    elif wire.direct == WireDirect.LEFT:
                        new_point = [wire.start_x - unit_length, wire.start_y]
                    elif wire.direct == WireDirect.TOP_RIGHT:
                        new_point = [wire.start_x + unit_length, wire.start_y - unit_length]
                    elif wire.direct == WireDirect.BOTTOM_RIGHT:
                        new_point = [wire.start_x + unit_length, wire.start_y + unit_length]
                    elif wire.direct == WireDirect.TOP_LEFT:
                        new_point = [wire.start_x - unit_length, wire.start_y - unit_length]
                    elif wire.direct == WireDirect.BOTTOM_LEFT:
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
                        new_wire = Wire(wire_1.end_x, wire_1.end_y, wire_2.start_x, wire_2.start_y, WireDirect.TOP_LEFT, wire_1.grid_list)
                        electrode.routing_wire.insert(i + 1, new_wire)
                    elif wire_1.direct == WireDirect.LEFT and wire_2.direct == WireDirect.BOTTOM:
                        new_point_1 = [(wire_1.end_x + self.pseudo_node.unit / 2), wire_1.end_y]
                        new_point_2 = [(wire_2.start_x), wire_2.start_y + self.pseudo_node.unit / 2]

                        wire_1.end_x = new_point_1[0]
                        wire_2.start_y = new_point_2[1]
                        new_wire = Wire(wire_1.end_x, wire_1.end_y, wire_2.start_x, wire_2.start_y, WireDirect.BOTTOM_LEFT, wire_1.grid_list)
                        electrode.routing_wire.insert(i + 1, new_wire)
                    elif wire_1.direct == WireDirect.RIGHT and wire_2.direct == WireDirect.BOTTOM:
                        new_point_1 = [(wire_1.end_x - self.pseudo_node.unit / 2), wire_1.end_y]
                        new_point_2 = [(wire_2.start_x), wire_2.start_y + self.pseudo_node.unit / 2]

                        wire_1.end_x = new_point_1[0]
                        wire_2.start_y = new_point_2[1]
                        new_wire = Wire(wire_1.end_x, wire_1.end_y, wire_2.start_x, wire_2.start_y, WireDirect.BOTTOM_RIGHT, wire_1.grid_list)
                        electrode.routing_wire.insert(i + 1, new_wire)
                    elif wire_1.direct == WireDirect.RIGHT and wire_2.direct == WireDirect.UP:
                        new_point_1 = [(wire_1.end_x - self.pseudo_node.unit / 2), wire_1.end_y]
                        new_point_2 = [(wire_2.start_x), wire_2.start_y - self.pseudo_node.unit / 2]

                        wire_1.end_x = new_point_1[0]
                        wire_2.start_y = new_point_2[1]
                        new_wire = Wire(wire_1.end_x, wire_1.end_y, wire_2.start_x, wire_2.start_y, WireDirect.TOP_RIGHT, wire_1.grid_list)
                        electrode.routing_wire.insert(i + 1, new_wire)
