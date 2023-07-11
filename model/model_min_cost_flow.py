from typing import Union

from ortools.graph import pywrapgraph
from shapely.geometry import LinearRing, Point, Polygon

from config import ROUTER_CONFIG
from model.model_flow import ModelFlow
from model.model_mesh import ModelMesh
from node.electrode import Electrode
from node.grid import Grid, GridType
from node.hub import Hub
from node.tile import Tile
from wire.degree import Degree, direct_table
from wire.wire import Wire


class ModelMinCostFlow():
    """Model min cost flow class.
    """

    def __init__(self, mesh: ModelMesh, flow: ModelFlow):
        self.mesh: ModelMesh = mesh
        self.flow: ModelFlow = flow
        self.start_nodes: list[Union[Grid, Tile, Hub, Electrode]] = []
        self.end_nodes: list[Union[Grid, Tile, Hub, Electrode]] = []
        self.capacities: list[Union[Grid, Tile, Hub, Electrode]] = []
        self.unit_costs: list[Union[Grid, Tile, Hub, Electrode]] = []
        self.supplies: list[int] = [0 for i in range(len(self.flow.flownodes))]
        self.num_supply: int = 0

        self.mim_cost_solver = None
        self.min_cost_flow = None

        self.all_path: list[Wire] = []
        self.electrode_routing_table: dict[tuple, int] = {}

    def init_structure(self):
        """Init structure.
        """
        for node in self.flow.flownodes:
            if type(node) == Tile and node.index != self.flow.global_t.index:
                # pseudo two layer
                self.start_nodes.append(node.index+1)
                self.end_nodes.append(node.index)
                self.capacities.append(int(node.capacity))
                self.unit_costs.append(0)
                # add neighbor tiles
                for nb_node in node.neighbor:
                    self.start_nodes.append(node.index)
                    self.end_nodes.append(nb_node.grid.index+1)
                    self.capacities.append(int(nb_node.capacity))
                    self.unit_costs.append(int(self.mesh.top_section.unit))
                # add contact pads
                for cp_node in node.contact_pads:
                    self.start_nodes.append(node.index)
                    self.end_nodes.append(cp_node.index)
                    self.capacities.append(1)
                    self.unit_costs.append(1)
                self.supplies[node.index] = 0
            elif type(node) == Tile and node.index == self.flow.global_t.index:
                for cp_node in node.contact_pads:
                    self.start_nodes.append(cp_node.index)
                    self.end_nodes.append(node.index)
                    self.capacities.append(1)
                    self.unit_costs.append(-1)
                self.supplies[node.index] = 0
            elif type(node) == Grid:
                if node.type == GridType.GRID:
                    self.start_nodes.append(node.index+1)
                    self.end_nodes.append(node.index)
                    self.capacities.append(1)
                    self.unit_costs.append(0)
                    for nb_node in node.neighbor:
                        self.start_nodes.append(node.index)
                        if type(nb_node.grid) == Grid:
                            self.end_nodes.append(nb_node.grid.index+1)
                        elif type(nb_node.grid) == Hub:
                            self.end_nodes.append(nb_node.grid.index)
                        self.capacities.append(int(nb_node.capacity))
                        self.unit_costs.append(int(nb_node.cost))
                elif node.type == GridType.PSEUDO_NODE:
                    for nb_node in node.neighbor:
                        self.start_nodes.append(node.index)
                        self.end_nodes.append(nb_node.grid.index+1)
                        self.capacities.append(int(nb_node.capacity))
                        self.unit_costs.append(int(nb_node.cost))

                    # add edge from electrode to PSEUDO_NODE
                    self.start_nodes.append(self.mesh.electrodes[node.electrode_index].index)
                    self.end_nodes.append(node.index)
                    self.capacities.append(1)
                    self.unit_costs.append(0)
                self.supplies[node.index] = 0
            elif type(node) == Hub:
                for nb_node in node.neighbor:
                    self.start_nodes.append(node.index)
                    self.end_nodes.append(nb_node.grid.index)
                    self.capacities.append(int(nb_node.capacity))
                    self.unit_costs.append(int(nb_node.cost))
                self.supplies[node.index] = 0
            elif type(node) == Electrode:
                self.supplies[node.index] = 1
                self.num_supply += 1

        try:
            self.supplies[self.flow.global_t.index] = -self.num_supply
        except:
            print(len(self.supplies), self.flow.global_t.index)

    def solver(self):
        """Solver.
        """
        self.min_cost_flow = pywrapgraph.SimpleMinCostFlow()
        # print("start min_cost_flow")

        # Add each arc.
        for arc in zip(self.start_nodes, self.end_nodes, self.capacities, self.unit_costs):
            self.min_cost_flow.AddArcWithCapacityAndUnitCost(arc[0], arc[1], arc[2], arc[3])
        # print("Add each arc")

        # Add node supplies.
        for count, supply in enumerate(self.supplies):
            self.min_cost_flow.SetNodeSupply(count, supply)

        # print("Add node supplies")

        self.mim_cost_solver = self.min_cost_flow.SolveMaxFlowWithMinCost()

    def get_closed_point_with_poly(self, _poly: list[tuple], _point: tuple) -> list:
        """Get close point with poly.

        Args:
            _poly (list[tuple]): list[tuple]
            _point (tuple): point

        Returns:
            list: closed point
        """
        poly = Polygon(_poly)
        point = Point(_point[0], _point[1])

        pol_ext = LinearRing(poly.exterior.coords)
        d = pol_ext.project(point)
        p = pol_ext.interpolate(d)
        closest_point_coords = list(p.coords)[0]
        return closest_point_coords

    def register_wire_into_electrode_routing(self, start_point: tuple, end_point: tuple, grid_list: list[Grid] = []):
        """Register wire into electrode routing.

        Args:
            start_point (tuple): start point
            end_point (tuple): end point
            grid_list (list[Grid], optional): grid list. Defaults to [].
        """
        electrode_index = self.electrode_routing_table.get(start_point, None)
        if electrode_index is not None:
            wire_degree = Degree.get_degree(start_point[0], -start_point[1], end_point[0], -end_point[1])

            try:
                _direct = direct_table[wire_degree]
            except:
                _direct = None
            wire = Wire(start_point[0], start_point[1], end_point[0], end_point[1], _direct, grid_list)

            if len(self.mesh.electrodes[electrode_index].routing_wire) > 0:
                no_need_to_add = False
                last_wire = self.mesh.electrodes[electrode_index].routing_wire[-1]
                last_wire_degree = Degree.get_degree(last_wire.start_x, -last_wire.start_y, last_wire.end_x, -last_wire.end_y)
                if wire_degree == last_wire_degree:
                    last_wire.end_x, last_wire.end_y = (wire.end_x, wire.end_y)
                    last_wire.grid_list.extend(wire.grid_list)
                    no_need_to_add = True
                elif last_wire.end_x == last_wire.start_x and wire.end_x == wire.start_x and last_wire.end_x == wire.end_x:
                    # top
                    if last_wire.start_y > last_wire.end_y:
                        # the wire overlap
                        if wire.end_y > last_wire.end_y:
                            last_wire.end_y = wire.end_y
                            last_wire.grid_list.extend(wire.grid_list)
                            no_need_to_add = True
                    # bottom
                    else:
                        if wire.end_y < last_wire.end_y:
                            last_wire.end_y = wire.end_y
                            last_wire.grid_list.extend(wire.grid_list)
                            no_need_to_add = True

                if not no_need_to_add:
                    self.mesh.electrodes[electrode_index].routing_wire.append(wire)
                    self.all_path.append(wire)
            else:
                self.mesh.electrodes[electrode_index].routing_wire.append(wire)
                self.all_path.append(wire)

            del self.electrode_routing_table[start_point]
            self.electrode_routing_table[end_point] = electrode_index
            return True
        return False

    def get_path(self):
        """Trace all min_cost_solver Arcs to get each wire
        """
        # Find the minimum cost flow between node 0 and node 4.

        # remove paths without flow
        non_zero_flow_list = []
        for i in range(self.min_cost_flow.NumArcs()):
            if self.min_cost_flow.Flow(i) != 0:
                non_zero_flow_list.append(i)

        # register each electrode first path
        remove_list = []
        for i in non_zero_flow_list:
            head: int = self.min_cost_flow.Tail(i)
            tail: int = self.min_cost_flow.Head(i)
            if self.flow.flownodes[tail] == 0:
                tail -= 1

            if type(self.flow.flownodes[head]) == Electrode:
                if type(self.flow.flownodes[tail]) == Grid:
                    self.electrode_routing_table[
                        (
                            int(self.flow.flownodes[tail].real_x),
                            int(self.flow.flownodes[tail].real_y)
                        )
                    ] = self.flow.flownodes[head].index
                    remove_list.append(i)

        # iterate to register all path to electrode routing wire
        while len(remove_list) > 0:
            non_zero_flow_list[:] = [x for x in non_zero_flow_list if x not in remove_list]

            remove_list = []

            for i in non_zero_flow_list:
                register_success = False
                head = self.min_cost_flow.Tail(i)
                tail = self.min_cost_flow.Head(i)
                if self.flow.flownodes[tail] == 0:
                    tail -= 1

                if type(self.flow.flownodes[head]) == Grid:
                    if type(self.flow.flownodes[tail]) == Grid:
                        start_x, start_y = (int(self.flow.flownodes[head].real_x), int(self.flow.flownodes[head].real_y))
                        end_x, end_y = (int(self.flow.flownodes[tail].real_x), int(self.flow.flownodes[tail].real_y))
                        # if self.flow.flownodes[head].type == GridType.PSEUDO_NODE:
                        #     electrode = self.mesh.electrodes[self.flow.flownodes[head].electrode_index]
                        #     close_point = self.get_close_point_with_poly(
                        #         electrode.poly, [self.flow.flownodes[tail].real_x, self.flow.flownodes[tail].real_y])
                        #     start_x, start_y = (close_point[0], close_point[1])
                        register_success = self.register_wire_into_electrode_routing(
                            (start_x, start_y), (end_x, end_y), [self.flow.flownodes[head], self.flow.flownodes[tail]])
                        self.flow.flownodes[head].flow = 1
                        self.flow.flownodes[tail].flow = 1
                    elif type(self.flow.flownodes[tail]) == Hub:
                        # from grid to hub: divide to 3 wire
                        # first: grid x, some y
                        start_x, start_y = (int(self.flow.flownodes[head].real_x), int(self.flow.flownodes[head].real_y))
                        end_x, end_y = (int(self.flow.flownodes[head].real_x), int(self.flow.flownodes[tail].real_y))
                        offset = abs(start_x - int(self.flow.flownodes[tail].real_x))
                        # top section
                        if start_y >= end_y:
                            end_y = end_y + offset
                        # down section
                        else:
                            end_y = end_y - offset
                        register_success = self.register_wire_into_electrode_routing((start_x, start_y), (end_x, end_y))

                        # final: to hub point
                        start_x, start_y = (end_x, end_y)
                        end_x, end_y = (int(self.flow.flownodes[tail].real_x), int(self.flow.flownodes[tail].real_y))
                        register_success = self.register_wire_into_electrode_routing((start_x, start_y), (end_x, end_y))
                elif type(self.flow.flownodes[head]) == Hub:
                    if type(self.flow.flownodes[tail]) == Grid:
                        start_x, start_y = (int(self.flow.flownodes[head].real_x), int(self.flow.flownodes[head].real_y))
                        end_x, end_y = (int(self.flow.flownodes[tail].real_x), int(self.flow.flownodes[tail].real_y))
                        register_success = self.register_wire_into_electrode_routing((start_x, start_y), (end_x, end_y))
                        self.flow.flownodes[tail].covered = True
                    elif type(self.flow.flownodes[tail]) == Tile:
                        start_x, start_y = (int(self.flow.flownodes[head].real_x), int(self.flow.flownodes[head].real_y))
                        end_x, end_y = (int(self.flow.flownodes[head].real_x), int(self.flow.flownodes[tail].real_y))
                        register_success = self.register_wire_into_electrode_routing((start_x, start_y), (end_x, end_y))
                        if register_success and self.flow.flownodes[head].hub_index % ROUTER_CONFIG.HUB_NUM > 0:
                            self.flow.flownodes[tail].flow.append(
                                (
                                    self.flow.flownodes[head].hub_index % ROUTER_CONFIG.HUB_NUM - 1,
                                    int(self.flow.flownodes[head].real_x)
                                )
                            )
                elif type(self.flow.flownodes[head]) == Tile:
                    if type(self.flow.flownodes[tail]) == Tile:
                        self.flow.flownodes[head].total_flow += self.min_cost_flow.Flow(i)
                        # tile in same vertical line
                        if self.flow.flownodes[head].tile_x == self.flow.flownodes[tail].tile_x:
                            self.flow.flownodes[head].next_vertical = self.flow.flownodes[tail]
                            self.flow.flownodes[tail].flow = self.flow.flownodes[head].flow
                        register_success = True
                    elif type(self.flow.flownodes[tail]) == Grid:
                        if self.flow.flownodes[tail].real_x > self.flow.flownodes[head].real_x:
                            self.flow.flownodes[head].right_pad = self.flow.flownodes[tail]
                        else:
                            self.flow.flownodes[head].left_pad = self.flow.flownodes[tail]
                        register_success = True
                        self.flow.flownodes[tail].covered = True

                if register_success:
                    remove_list.append(i)

        # tile flow collocation
        self.create_contact_pad_path(self.mesh.top_section.tile, 'top')
        self.create_contact_pad_path(self.mesh.bottom_section.tile, 'bottom')

        # for electrode in self.mesh.electrodes:
        #     print(len(electrode.routing_wire))

    def create_contact_pad_path(self, tile_list: list[list[Tile]], section: str = 'top'):
        """Add wire from tile to contact pad, and consider flow collocation

        Args:
            tile_list (list[list[Tile]]): tile array
            section (str, optional): section. Defaults to 'top'.
        """
        for tile_col in tile_list:
            if section == 'top':
                tile = tile_col[-1]
            else:
                tile = tile_col[0]

            if len(tile.flow) > 0:
                tile.flow = sorted(tile.flow, key=lambda s: s[0])

                if tile.left_pad is not None:
                    _flow = tile.flow.pop(0)
                    start_x, start_y = (int(_flow[1]), int(tile.real_y))
                    end_x, end_y = (int(tile.left_pad.real_x), int(tile.left_pad.real_y))
                    offset = abs(start_x - end_x)
                    if start_y > end_y:
                        end_y = start_y - offset
                    else:
                        end_y = start_y + offset
                    self.register_wire_into_electrode_routing((start_x, start_y), (end_x, end_y))
                if tile.right_pad is not None:
                    _flow = tile.flow.pop()
                    start_x, start_y = (int(_flow[1]), int(tile.real_y))
                    end_x, end_y = (int(tile.right_pad.real_x), int(tile.right_pad.real_y))
                    offset = abs(start_x - end_x)
                    if start_y > end_y:
                        end_y = start_y - offset
                    else:
                        end_y = start_y + offset
                    self.register_wire_into_electrode_routing((start_x, start_y), (end_x, end_y))

                while tile.next_vertical is not None:
                    for _flow in tile.flow:
                        start_x, start_y = (int(_flow[1]), int(tile.real_y))
                        end_x, end_y = (int(_flow[1]), int(tile.next_vertical.real_y))
                        self.register_wire_into_electrode_routing((start_x, start_y), (end_x, end_y))

                    if tile.next_vertical.left_pad is not None:
                        _flow = tile.flow.pop(0)
                        start_x, start_y = (int(_flow[1]), int(tile.next_vertical.real_y))
                        end_x, end_y = (int(tile.next_vertical.left_pad.real_x), int(tile.next_vertical.left_pad.real_y))
                        offset = abs(start_x - end_x)
                        if start_y > end_y:
                            end_y = start_y - offset
                        else:
                            end_y = start_y + offset
                        self.register_wire_into_electrode_routing((start_x, start_y), (end_x, end_y))
                    if tile.next_vertical.right_pad is not None:
                        _flow = tile.flow.pop()
                        start_x, start_y = (int(_flow[1]), int(tile.next_vertical.real_y))
                        end_x, end_y = (int(tile.next_vertical.right_pad.real_x), int(tile.next_vertical.right_pad.real_y))
                        offset = abs(start_x - end_x)
                        if start_y > end_y:
                            end_y = start_y - offset
                        else:
                            end_y = start_y + offset
                        self.register_wire_into_electrode_routing((start_x, start_y), (end_x, end_y))
                    tile.next_vertical.flow = tile.flow
                    tile = tile.next_vertical
