import numpy as np
import math
import sys
import os
from shapely.geometry import Polygon, Point, LinearRing
from ezdxf.addons import r12writer
from operator import itemgetter, attrgetter
from math import atan2,degrees
from ortools.graph import pywrapgraph

from degree import Degree
from grid import Grid
from tile import Tile
from hub import Hub
from electrode import Electrode
from wire import Wire
from draw import Draw

class MCMF():

    def __init__(self, mesh, flow):
        self.mesh = mesh
        self.flow = flow
        self.start_nodes = []
        self.end_nodes = []
        self.capacities = []
        self.unit_costs = []
        self.supplies = [0 for i in range(len(self.flow.flownodes))]
        self.num_supply = 0

        self.MaxFlowWithMinCost = None
        self.min_cost_flow = None

        self.all_path = []
        self.electrode_wire=[[] for _ in range(len(mesh.electrodes))]

    def init_structure(self):
        for node in self.flow.flownodes:
            if type(node) == Tile and node.index != self.flow.global_t.index:
                #pseudo two layer
                self.start_nodes.append(node.index+1)
                self.end_nodes.append(node.index)
                self.capacities.append(int(node.capacity))
                self.unit_costs.append(0)
                # add neighbor tiles
                for nb_node in node.neighbor:
                    self.start_nodes.append(node.index)
                    self.end_nodes.append(nb_node[0].index+1)
                    self.capacities.append(int(nb_node[1]))
                    self.unit_costs.append(int(self.mesh.control_pad_unit))
                # add contact pads
                for cp_node in node.contact_pads:
                    self.start_nodes.append(node.index)
                    self.end_nodes.append(cp_node.index)
                    self.capacities.append(1)
                    self.unit_costs.append(1)
                self.supplies[node.index] = 0
            elif type(node) == Tile and node.index==self.flow.global_t.index:
                for cp_node in node.contact_pads:
                    self.start_nodes.append(cp_node.index)
                    self.end_nodes.append(node.index)
                    self.capacities.append(1)
                    self.unit_costs.append(-1)
                self.supplies[node.index] = 0
            elif type(node) == Grid:
                if node.type==0:
                    self.start_nodes.append(node.index+1)
                    self.end_nodes.append(node.index)
                    self.capacities.append(1)
                    self.unit_costs.append(0)
                    for nb_node in node.neighbor:
                        self.start_nodes.append(node.index)
                        if type(nb_node[0])==Grid:
                            self.end_nodes.append(nb_node[0].index+1)
                        else:
                            self.end_nodes.append(nb_node[0].index)
                        self.capacities.append(int(nb_node[1]))
                        self.unit_costs.append(int(nb_node[2]))
                    if len(node.neighbor_electrode) > 0:
                        for ne_node in node.neighbor_electrode:
                            self.start_nodes.append(self.mesh.electrodes[ne_node[0]].index)
                            self.end_nodes.append(node.index+1)
                            self.capacities.append(1)
                            self.unit_costs.append(ne_node[-1])
                            # if ne_node[1]==1 or ne_node[1]==6:
                            #     self.unit_costs.append(node.cost)
                            # else:
                            #     self.unit_costs.append(ne_node[-1])
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
                self.num_supply+=1
                
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

        self.MaxFlowWithMinCost = self.min_cost_flow.SolveMaxFlowWithMinCost()

    def get_close_point_with_poly(self, _poly, _point):
        poly = Polygon(_poly)
        point = Point(_point[0], _point[1])

        pol_ext = LinearRing(poly.exterior.coords)
        d = pol_ext.project(point)
        p = pol_ext.interpolate(d)
        closest_point_coords = list(p.coords)[0]
        return closest_point_coords

    def get_path(self):
        #Find the minimum cost flow between node 0 and node 4.
        if self.MaxFlowWithMinCost == self.min_cost_flow.OPTIMAL and len(self.electrode_wire) > 0:
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
                        close_point = self.get_close_point_with_poly(self.flow.flownodes[head].poly, [self.flow.flownodes[tail].real_x, self.flow.flownodes[tail].real_y])
                        index_list = []
                        tmp_x = self.flow.flownodes[tail].grid_x
                        tmp_y = self.flow.flownodes[tail].grid_y
                        for en_node in self.flow.flownodes[tail].neighbor_electrode:
                            if en_node[0] == self.flow.flownodes[head].electrode_index:
                                index_list.append([en_node[1],en_node[2],en_node[3], en_node[4]])
                        self.all_path.append(Wire(int(close_point[0]), int(close_point[1]),int(self.flow.flownodes[tail].real_x), int(self.flow.flownodes[tail].real_y)))
                        # R_x = self.mesh.grids2[tmp_x+index_list[0][1],tmp_y+index_list[0][2]].real_x
                        # R_y = self.mesh.grids2[tmp_x+index_list[0][1],tmp_y+index_list[0][2]].real_y
                        # E_x = self.mesh.grids2[tmp_x+index_list[0][1],tmp_y+index_list[0][2]].electrode_x
                        # E_y = self.mesh.grids2[tmp_x+index_list[0][1],tmp_y+index_list[0][2]].electrode_y
                        # if index_list[0][3] is True: ## only belong to ONE Electrode
                        # Shift_x = E_x - self.mesh.grids2[tmp_x+index_list[0][1],tmp_y+index_list[0][2]].real_x
                        # Shift_y = E_y - self.mesh.grids2[tmp_x+index_list[0][1],tmp_y+index_list[0][2]].real_y
                        # #self.all_path.append(Wire(int(self.mesh.grids2[tmp_x+index_list[0][1],tmp_y+index_list[0][2]].real_x),int(self.mesh.grids2[tmp_x+index_list[0][1],tmp_y+index_list[0][2]].real_y),int(self.flow.flownodes[tail].real_x),int(self.flow.flownodes[tail].real_y)))
                        # self.all_path.append(Wire(int(E_x),int(E_y),int(self.flow.flownodes[tail].real_x+Shift_x),int(self.flow.flownodes[tail].real_y+Shift_y)))
                        # self.all_path.append(Wire(int(self.flow.flownodes[tail].real_x+Shift_x),int(self.flow.flownodes[tail].real_y+Shift_y),int(self.flow.flownodes[tail].real_x),int(self.flow.flownodes[tail].real_y)))
                        # else:
                        #     tmp_x = self.flow.flownodes[tail].grid_x
                        #     tmp_y = self.flow.flownodes[tail].grid_y
                        #     # if self.mesh.grids2[tmp_x+index_list[0][1],tmp_y+index_list[0][2]].inner_grid != None:
                        #     #     R_x = self.mesh.grids2[tmp_x+index_list[0][1],tmp_y+index_list[0][2]].inner_grid.real_x
                        #     #     R_y = self.mesh.grids2[tmp_x+index_list[0][1],tmp_y+index_list[0][2]].inner_grid.real_y
                        #     #     E_x = self.mesh.grids2[tmp_x+index_list[0][1],tmp_y+index_list[0][2]].inner_grid.electrode_x
                        #     #     E_y = self.mesh.grids2[tmp_x+index_list[0][1],tmp_y+index_list[0][2]].inner_grid.electrode_y
                        #     # else:
                        #     R_x = self.mesh.grids2[tmp_x+index_list[0][1],tmp_y+index_list[0][2]].real_x
                        #     R_y = self.mesh.grids2[tmp_x+index_list[0][1],tmp_y+index_list[0][2]].real_y
                        #     E_x = self.mesh.grids2[tmp_x+index_list[0][1],tmp_y+index_list[0][2]].electrode_x
                        #     E_y = self.mesh.grids2[tmp_x+index_list[0][1],tmp_y+index_list[0][2]].electrode_y
                        #     self.all_path.append(Wire(int(E_x),int(E_y),int(R_x),int(R_y)))
                        #     self.all_path.append(Wire(int(R_x),int(R_y),int(self.flow.flownodes[tail].real_x),int(self.flow.flownodes[tail].real_y)))
                        #     for nb_list in index_list:
                        #         if nb_list[0] == 1 or nb_list[0] == 6: ## dir of electrode left-top & right-top only have ONE E
                        #             # if self.mesh.grids2[tmp_x+nb_list[1],tmp_y+nb_list[2]].electrode_y2!=0:
                        #             #     self.mesh.grids2[tmp_x+nb_list[1],tmp_y+nb_list[2]].electrode_y=self.mesh.grids2[tmp_x+nb_list[1],tmp_y+nb_list[2]].electrode_y2
                        #             self.all_path.append(Wire(int(self.mesh.grids2[tmp_x+nb_list[1],tmp_y+nb_list[2]].electrode_x),int(self.mesh.grids2[tmp_x+nb_list[1],tmp_y+nb_list[2]].electrode_y),int(self.flow.flownodes[tail].real_x),int(self.flow.flownodes[tail].real_y)))
                        #         if nb_list[0] == 3 or nb_list[0] == 4:
                        #             self.all_path.append(Wire(int(self.mesh.grids2[tmp_x+nb_list[1],tmp_y+nb_list[2]].electrode_x),int(self.mesh.grids2[tmp_x+nb_list[1],tmp_y+nb_list[2]].electrode_y),int(self.flow.flownodes[tail].real_x),int(self.flow.flownodes[tail].real_y)))
                    # if type(self.flow.flownodes[head]) == Electrode and type(self.flow.flownodes[tail]) == Grid:
                    #     index_list = []
                    #     tmp_x = self.flow.flownodes[tail].grid_x
                    #     tmp_y = self.flow.flownodes[tail].grid_y
                    #     for en_node in self.flow.flownodes[tail].neighbor_electrode:
                    #         if en_node[0] == self.flow.flownodes[head].electrode_index:
                    #             index_list.append([en_node[1],en_node[2],en_node[3]])
                    #     if self.mesh.grids2[tmp_x+index_list[0][1],tmp_y+index_list[0][2]].inner_grid != None:
                    #         R_x = self.mesh.grids2[tmp_x+index_list[0][1],tmp_y+index_list[0][2]].inner_grid.real_x
                    #         R_y = self.mesh.grids2[tmp_x+index_list[0][1],tmp_y+index_list[0][2]].inner_grid.real_y
                    #         E_x = self.mesh.grids2[tmp_x+index_list[0][1],tmp_y+index_list[0][2]].inner_grid.electrode_x
                    #         E_y = self.mesh.grids2[tmp_x+index_list[0][1],tmp_y+index_list[0][2]].inner_grid.electrode_y
                    #     else:
                    #         R_x = self.mesh.grids2[tmp_x+index_list[0][1],tmp_y+index_list[0][2]].real_x
                    #         R_y = self.mesh.grids2[tmp_x+index_list[0][1],tmp_y+index_list[0][2]].real_y
                    #         E_x = self.mesh.grids2[tmp_x+index_list[0][1],tmp_y+index_list[0][2]].electrode_x
                    #         E_y = self.mesh.grids2[tmp_x+index_list[0][1],tmp_y+index_list[0][2]].electrode_y
                        # self.all_path.append(Wire(int(E_x),int(E_y),int(R_x),int(R_y)))
                        # self.all_path.append(Wire(int(R_x),int(R_y),int(self.flow.flownodes[tail].real_x),int(self.flow.flownodes[tail].real_y)))
                    elif type(self.flow.flownodes[head]) == Grid and type(self.flow.flownodes[tail]) == Grid:
                        self.all_path.append(Wire(int(self.flow.flownodes[head].real_x),int(self.flow.flownodes[head].real_y),int(self.flow.flownodes[tail].real_x),int(self.flow.flownodes[tail].real_y)))
                        self.flow.flownodes[head].flow=1
                        self.flow.flownodes[tail].flow=1
                    elif type(self.flow.flownodes[head]) == Grid and type(self.flow.flownodes[tail]) == Hub:
                        self.all_path.append(Wire(int(self.flow.flownodes[head].real_x),int(self.flow.flownodes[head].real_y),int(self.flow.flownodes[tail].real_x),int(self.flow.flownodes[tail].real_y)))
                    elif type(self.flow.flownodes[head]) == Hub and type(self.flow.flownodes[tail]) == Grid:
                        self.all_path.append(Wire(int(self.flow.flownodes[head].real_x),int(self.flow.flownodes[head].real_y),int(self.flow.flownodes[tail].real_x),int(self.flow.flownodes[tail].real_y)))
                    elif type(self.flow.flownodes[head]) == Hub and type(self.flow.flownodes[tail]) == Tile:
                        self.all_path.append(Wire(int(self.flow.flownodes[head].real_x),int(self.flow.flownodes[head].real_y),int(self.flow.flownodes[head].real_x),int(self.flow.flownodes[tail].real_y)))
                        if self.flow.flownodes[head].hub_index%3 == 1:
                            self.flow.flownodes[tail].flow[0]=1
                        elif self.flow.flownodes[head].hub_index%3 == 2:
                            self.flow.flownodes[tail].flow[1]=1
                    elif type(self.flow.flownodes[head]) == Tile and type(self.flow.flownodes[tail]) == Tile:
                        self.flow.flownodes[head].total_flow+=self.min_cost_flow.Flow(i)
                        if self.flow.flownodes[head].tile_x == self.flow.flownodes[tail].tile_x:
                            self.flow.flownodes[head].vertical_path.append(self.flow.flownodes[tail])
                        elif self.flow.flownodes[head].tile_y == self.flow.flownodes[tail].tile_y:
                            self.flow.flownodes[head].horizontal_path.append(self.flow.flownodes[tail])
                    elif type(self.flow.flownodes[head]) == Tile and type(self.flow.flownodes[tail]) == Grid:
                        self.flow.flownodes[head].corner_in.append(self.flow.flownodes[tail])
            
            # -------------------
            self.flow.create_tiles_path(self.mesh.tiles1_length,self.mesh.tiles1,self.mesh.hubs1,self.mesh.tiles1_length[1]-1,-1,-1,self.all_path)
            self.flow.create_tiles_path(self.mesh.tiles3_length,self.mesh.tiles3,self.mesh.hubs3,0,self.mesh.tiles1_length[1],1,self.all_path)
            #print("self.all_path = ",len(self.all_path))

            # -------------------
            for i in range(len(self.all_path)):
                for j in range(len(self.all_path)):
                    if self.all_path[j].start_x == self.all_path[i].end_x and self.all_path[j].start_y == self.all_path[i].end_y:
                        self.all_path[i].next = self.all_path[j]
                        self.all_path[j].head = 0 ## 0 or 1 
                        break
            
            # set paths to each electrode
            j=0

            for i in range(len(self.all_path)):
                if self.all_path[i].head == 1 and j < len(self.electrode_wire):
                    #print(self.all_path[i].start_x,self.all_path[i].start_y,self.all_path[i].end_x,self.all_path[i].end_y)
                    #dxf.add_circle(center=(self.all_path[i].start_x, -self.all_path[i].start_y), radius = 750.0)
                    self.electrode_wire[j].append(self.all_path[i])
                    tmp_next = self.all_path[i].next
                    while tmp_next != None:
                        #print(tmp_next.start_x,tmp_next.start_y,tmp_next.end_x,tmp_next.end_y)
                        if tmp_next.start_x==tmp_next.end_x and tmp_next.start_y==tmp_next.end_y:
                            break
                        self.electrode_wire[j].append(tmp_next)
                        tmp_next = tmp_next.next
                    j+=1