from typing import Any, Optional, Tuple, Union, List, Dict, Callable, NoReturn
from shapely.geometry import Polygon, Point, LinearRing
from ortools.graph import pywrapgraph
from degree import Degree

from grid import Grid, GridType
from tile import Tile
from hub import Hub
from electrode import Electrode
from wire import Wire
from model_mesh import ModelMesh
from model_flow import ModelFlow


class ModelMinCostFlow():

    def __init__(self, mesh: ModelMesh, flow: ModelFlow):
        self.mesh = mesh
        self.flow = flow
        self.start_nodes: List[Union[Grid, Tile, Hub, Electrode]] = []
        self.end_nodes: List[Union[Grid, Tile, Hub, Electrode]] = []
        self.capacities: List[Union[Grid, Tile, Hub, Electrode]] = []
        self.unit_costs: List[Union[Grid, Tile, Hub, Electrode]] = []
        self.supplies = [0 for i in range(len(self.flow.flownodes))]
        self.num_supply = 0

        self.mim_cost_solver = None
        self.min_cost_flow = None

        self.all_path: List[Wire] = []
        self.electrode_routing_table: Dict[Tuple, int] = {}

    def init_structure(self):
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
                    self.end_nodes.append(nb_node[0].index+1)
                    self.capacities.append(int(nb_node[1]))
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
                        if type(nb_node[0]) == Grid:
                            self.end_nodes.append(nb_node[0].index+1)
                        elif type(nb_node[0]) == Hub:
                            self.end_nodes.append(nb_node[0].index)
                        self.capacities.append(int(nb_node[1]))
                        self.unit_costs.append(int(nb_node[2]))
                elif node.type == GridType.PSEUDONODE:
                    for nb_node in node.neighbor:
                        self.start_nodes.append(node.index)
                        self.end_nodes.append(nb_node[0].index+1)
                        self.capacities.append(int(nb_node[1]))
                        self.unit_costs.append(int(nb_node[2]))

                    # add edge from electrode to PSEUDONODE
                    self.start_nodes.append(self.mesh.electrodes[node.electrode_index].index)
                    self.end_nodes.append(node.index)
                    self.capacities.append(1)
                    self.unit_costs.append(0)
                self.supplies[node.index] = 0
            elif type(node) == Hub:
                for nb_node in node.neighbor:
                    self.start_nodes.append(node.index)
                    self.end_nodes.append(nb_node[0].index)
                    self.capacities.append(int(nb_node[1]))
                    self.unit_costs.append(int(nb_node[2]))
                self.supplies[node.index] = 0
            elif type(node) == Electrode:
                self.supplies[node.index] = 1
                self.num_supply += 1

        try:
            self.supplies[self.flow.global_t.index] = -self.num_supply
        except:
            print(len(self.supplies), self.flow.global_t.index)

    def solver(self):
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

        self.mim_cost_solver = self.min_cost_flow.Solve()  # SolveMaxFlowWithMinCost()

    def get_close_point_with_poly(self, _poly, _point) -> list:
        poly = Polygon(_poly)
        point = Point(_point[0], _point[1])

        pol_ext = LinearRing(poly.exterior.coords)
        d = pol_ext.project(point)
        p = pol_ext.interpolate(d)
        closest_point_coords = list(p.coords)[0]
        return closest_point_coords

    def register_wire_into_electrode_roting(self, start_point, end_point, grid_list: List[Grid] = []):
        electrode_index = self.electrode_routing_table.get(start_point, None)
        if electrode_index is not None:
            wire = Wire(start_point[0], start_point[1], end_point[0], end_point[1], grid_list)
            if len(self.mesh.electrodes[electrode_index].routing_wire) > 0:
                last_wire = self.mesh.electrodes[electrode_index].routing_wire[-1]
                wire_degree = Degree.getdegree(wire.start_x, wire.start_y, wire.end_x, wire.end_y)
                last_wire_degree = Degree.getdegree(last_wire.start_x, last_wire.start_y, last_wire.end_x, last_wire.end_y)
                if wire_degree == last_wire_degree:
                    last_wire.end_x, last_wire.end_y = (wire.end_x, wire.end_y)
                    last_wire.grid_list.extend(wire.grid_list)
                else:
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
        """
            trace all min_cost_solver Arcs to get each wire
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
            head = self.min_cost_flow.Tail(i)
            tail = self.min_cost_flow.Head(i)
            if self.flow.flownodes[tail] == 0:
                tail -= 1

            if type(self.flow.flownodes[head]) == Electrode:
                if type(self.flow.flownodes[tail]) == Grid:
                    self.electrode_routing_table[(int(self.flow.flownodes[tail].real_x), int(self.flow.flownodes[tail].real_y))
                                                 ] = self.flow.flownodes[head].index
                    remove_list.append(i)

        # iterate to register all path to electeode routing wire
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
                        # if self.flow.flownodes[head].type == GridType.PSEUDONODE:
                        #     electrode = self.mesh.electrodes[self.flow.flownodes[head].electrode_index]
                        #     close_point = self.get_close_point_with_poly(
                        #         electrode.poly, [self.flow.flownodes[tail].real_x, self.flow.flownodes[tail].real_y])
                        #     start_x, start_y = (close_point[0], close_point[1])
                        register_success = self.register_wire_into_electrode_roting(
                            (start_x, start_y), (end_x, end_y), [self.flow.flownodes[head], self.flow.flownodes[tail]])
                        self.flow.flownodes[head].flow = 1
                        self.flow.flownodes[tail].flow = 1
                    elif type(self.flow.flownodes[tail]) == Hub:
                        start_x, start_y = (int(self.flow.flownodes[head].real_x), int(self.flow.flownodes[head].real_y))
                        end_x, end_y = (int(self.flow.flownodes[tail].real_x), int(self.flow.flownodes[tail].real_y))
                        register_success = self.register_wire_into_electrode_roting((start_x, start_y), (end_x, end_y))
                elif type(self.flow.flownodes[head]) == Hub:
                    if type(self.flow.flownodes[tail]) == Grid:
                        start_x, start_y = (int(self.flow.flownodes[head].real_x), int(self.flow.flownodes[head].real_y))
                        end_x, end_y = (int(self.flow.flownodes[tail].real_x), int(self.flow.flownodes[tail].real_y))
                        register_success = self.register_wire_into_electrode_roting((start_x, start_y), (end_x, end_y))
                    elif type(self.flow.flownodes[tail]) == Tile:
                        start_x, start_y = (int(self.flow.flownodes[head].real_x), int(self.flow.flownodes[head].real_y))
                        end_x, end_y = (int(self.flow.flownodes[head].real_x), int(self.flow.flownodes[tail].real_y))
                        register_success = self.register_wire_into_electrode_roting((start_x, start_y), (end_x, end_y))
                        if register_success and self.flow.flownodes[head].hub_index % 5 > 0:
                            self.flow.flownodes[tail].flow.append((self.flow.flownodes[head].hub_index %
                                                                  5 - 1, int(self.flow.flownodes[head].real_x)))
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

                if register_success:
                    remove_list.append(i)

        # tile flow collocation
        self.create_contact_pad_path(self.mesh.top_section.tile, 'top')
        self.create_contact_pad_path(self.mesh.down_section.tile, 'down')

        # for electrode in self.mesh.electrodes:
        #     print(len(electrode.routing_wire))

    def create_contact_pad_path(self, tile_array: List[List[Tile]], section: str = 'top'):
        """
            add wire from tile to contactpad, and consider flow collocation
        """
        for tile_col in tile_array:
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
                    self.register_wire_into_electrode_roting((start_x, start_y), (end_x, end_y))
                if tile.right_pad is not None:
                    _flow = tile.flow.pop()
                    start_x, start_y = (int(_flow[1]), int(tile.real_y))
                    end_x, end_y = (int(tile.right_pad.real_x), int(tile.right_pad.real_y))
                    self.register_wire_into_electrode_roting((start_x, start_y), (end_x, end_y))

                while tile.next_vertical is not None:
                    for _flow in tile.flow:
                        start_x, start_y = (int(_flow[1]), int(tile.real_y))
                        end_x, end_y = (int(_flow[1]), int(tile.next_vertical.real_y))
                        self.register_wire_into_electrode_roting((start_x, start_y), (end_x, end_y))

                    if tile.next_vertical.left_pad is not None:
                        _flow = tile.flow.pop(0)
                        start_x, start_y = (int(_flow[1]), int(tile.next_vertical.real_y))
                        end_x, end_y = (int(tile.next_vertical.left_pad.real_x), int(tile.next_vertical.left_pad.real_y))
                        self.register_wire_into_electrode_roting((start_x, start_y), (end_x, end_y))
                    if tile.next_vertical.right_pad is not None:
                        _flow = tile.flow.pop()
                        start_x, start_y = (int(_flow[1]), int(tile.next_vertical.real_y))
                        end_x, end_y = (int(tile.next_vertical.right_pad.real_x), int(tile.next_vertical.right_pad.real_y))
                        self.register_wire_into_electrode_roting((start_x, start_y), (end_x, end_y))
                    tile.next_vertical.flow = tile.flow
                    tile = tile.next_vertical
