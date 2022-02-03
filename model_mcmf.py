from typing import Any, Optional, Tuple, Union, List, Dict, Callable, NoReturn
from shapely.geometry import Polygon, Point, LinearRing
from ortools.graph import pywrapgraph

from grid import Grid, GridType
from tile import Tile
from hub import Hub
from electrode import Electrode
from wire import Wire
from draw import Draw
from model_mesh import ModelMesh
from model_flow import ModelFlow


class ModelMCMF():

    def __init__(self, mesh: ModelMesh, flow: ModelFlow):
        self.mesh = mesh
        self.flow = flow
        self.start_nodes: List[Union[Grid, Tile, Hub, Electrode]] = []
        self.end_nodes: List[Union[Grid, Tile, Hub, Electrode]] = []
        self.capacities: List[Union[Grid, Tile, Hub, Electrode]] = []
        self.unit_costs: List[Union[Grid, Tile, Hub, Electrode]] = []
        self.supplies = [0 for i in range(len(self.flow.flownodes))]
        self.num_supply = 0

        self.mim_cost_max_flow_solver = None
        self.min_cost_flow = None

        self.all_path: List[Wire] = []

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
                    # self.start_nodes.append(node.index+1)
                    # self.end_nodes.append(node.index)
                    # self.capacities.append(1)
                    # self.unit_costs.append(0)
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

        self.supplies[self.flow.global_t.index] = -self.num_supply

    def solver(self):
        self.min_cost_flow = pywrapgraph.SimpleMinCostFlow()
        # print("start min_cost_flow")

        # Add each arc.
        for i in range(0, len(self.start_nodes)):
            self.min_cost_flow.AddArcWithCapacityAndUnitCost(self.start_nodes[i], self.end_nodes[i],
                                                             self.capacities[i], self.unit_costs[i])
        # print("Add each arc")

        # Add node supplies.
        sum = 0
        for i in range(0, len(self.supplies)):
            self.min_cost_flow.SetNodeSupply(i, self.supplies[i])
            sum += self.supplies[i]
        # print("Add node supplies")

        self.mim_cost_max_flow_solver = self.min_cost_flow.SolveMaxFlowWithMinCost()

    def get_close_point_with_poly(self, _poly, _point):
        poly = Polygon(_poly)
        point = Point(_point[0], _point[1])

        pol_ext = LinearRing(poly.exterior.coords)
        d = pol_ext.project(point)
        p = pol_ext.interpolate(d)
        closest_point_coords = list(p.coords)[0]
        return closest_point_coords

    def get_path(self):
        # Find the minimum cost flow between node 0 and node 4.
        if self.mim_cost_max_flow_solver == self.min_cost_flow.OPTIMAL:
            #print('Minimum cost:', self.min_cost_flow.OptimalCost())
            for i in range(self.min_cost_flow.NumArcs()):
                if self.min_cost_flow.Flow(i) != 0:
                    head = self.min_cost_flow.Tail(i)
                    tail = self.min_cost_flow.Head(i)
                    if self.flow.flownodes[head] == 0:
                        pass
                    if self.flow.flownodes[tail] == 0:
                        tail -= 1

                    if type(self.flow.flownodes[head]) == Electrode and type(self.flow.flownodes[tail]) == Grid:
                        close_point = self.get_close_point_with_poly(self.flow.flownodes[head].poly, [
                                                                     self.flow.flownodes[tail].real_x, self.flow.flownodes[tail].real_y])
                        # index_list = []
                        # for en_node in self.flow.flownodes[tail].neighbor_electrode:
                        #     if en_node[0] == self.flow.flownodes[head].electrode_index:
                        #         index_list.append([en_node[1], en_node[2], en_node[3], en_node[4]])
                        self.all_path.append(Wire(self.flow.flownodes[head].real_x, self.flow.flownodes[head].real_y, int(
                            self.flow.flownodes[tail].real_x), int(self.flow.flownodes[tail].real_y)))
                        # self.all_path.append(Wire(int(close_point[0]), int(close_point[1]), int(
                        #     self.flow.flownodes[tail].real_x), int(self.flow.flownodes[tail].real_y)))
                    elif type(self.flow.flownodes[head]) == Grid and type(self.flow.flownodes[tail]) == Grid:
                        self.all_path.append(Wire(int(self.flow.flownodes[head].real_x), int(self.flow.flownodes[head].real_y), int(
                            self.flow.flownodes[tail].real_x), int(self.flow.flownodes[tail].real_y)))
                        self.flow.flownodes[head].flow = 1
                        self.flow.flownodes[tail].flow = 1
                    elif type(self.flow.flownodes[head]) == Grid and type(self.flow.flownodes[tail]) == Hub:
                        self.all_path.append(Wire(int(self.flow.flownodes[head].real_x), int(self.flow.flownodes[head].real_y), int(
                            self.flow.flownodes[tail].real_x), int(self.flow.flownodes[tail].real_y)))
                    elif type(self.flow.flownodes[head]) == Hub and type(self.flow.flownodes[tail]) == Grid:
                        self.all_path.append(Wire(int(self.flow.flownodes[head].real_x), int(self.flow.flownodes[head].real_y), int(
                            self.flow.flownodes[tail].real_x), int(self.flow.flownodes[tail].real_y)))
                    elif type(self.flow.flownodes[head]) == Hub and type(self.flow.flownodes[tail]) == Tile:
                        self.all_path.append(Wire(int(self.flow.flownodes[head].real_x), int(self.flow.flownodes[head].real_y), int(
                            self.flow.flownodes[head].real_x), int(self.flow.flownodes[tail].real_y)))
                        if self.flow.flownodes[head].hub_index % 3 == 1:
                            self.flow.flownodes[tail].flow[0] = 1
                        elif self.flow.flownodes[head].hub_index % 3 == 2:
                            self.flow.flownodes[tail].flow[1] = 1
                    elif type(self.flow.flownodes[head]) == Tile and type(self.flow.flownodes[tail]) == Tile:
                        self.flow.flownodes[head].total_flow += self.min_cost_flow.Flow(i)
                        if self.flow.flownodes[head].tile_x == self.flow.flownodes[tail].tile_x:
                            self.flow.flownodes[head].vertical_path.append(self.flow.flownodes[tail])
                        elif self.flow.flownodes[head].tile_y == self.flow.flownodes[tail].tile_y:
                            self.flow.flownodes[head].horizontal_path.append(self.flow.flownodes[tail])
                    elif type(self.flow.flownodes[head]) == Tile and type(self.flow.flownodes[tail]) == Grid:
                        # tile connect to contactpad
                        self.flow.flownodes[head].corner_in.append(self.flow.flownodes[tail])

            # -------------------
            self.flow.create_tile_path(self.mesh.top_section.tile, self.mesh.top_section.hub,
                                       len(self.mesh.top_section.tile[0])-1, -1, -1, self.all_path)
            self.flow.create_tile_path(self.mesh.down_section.tile, self.mesh.down_section.hub,
                                       0, len(self.mesh.top_section.tile[0]), 1, self.all_path)
            #print("self.all_path = ",len(self.all_path))

            # -------------------
            for i in range(len(self.all_path)):
                for j in range(len(self.all_path)):
                    if self.all_path[j].start_x == self.all_path[i].end_x and self.all_path[j].start_y == self.all_path[i].end_y:
                        self.all_path[i].next = self.all_path[j]
                        self.all_path[j].head = 0  # 0 or 1
                        break

            # print('1')
            # # print(self.all_path)
            # set paths to each electrode
            electrode_index = 0
            for path in self.all_path:
                if path.head == 1 and electrode_index < len(self.mesh.electrodes):
                    # print(self.all_path[i].start_x,self.all_path[i].start_y,self.all_path[i].end_x,self.all_path[i].end_y)
                    #dxf.add_circle(center=(self.all_path[i].start_x, -self.all_path[i].start_y), radius = 750.0)
                    self.mesh.electrodes[electrode_index].routing_wire.append(path)
                    tmp_next: Wire = path.next
                    while tmp_next != None:
                        if tmp_next.start_x == tmp_next.end_x and tmp_next.start_y == tmp_next.end_y:
                            break
                        self.mesh.electrodes[electrode_index].routing_wire.append(tmp_next)
                        tmp_next = tmp_next.next
                    electrode_index += 1

            # print('2')
            # for electrode in self.mesh.electrodes:
            #     print(len(electrode.routing_wire))
