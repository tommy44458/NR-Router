import numpy as np
import math
import sys
import os
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

class Flow():

    def __init__(self, mesh):
        self.mesh = mesh
        self.flownodes = []
        self.special_index = []
        self.node_index = 0
        self.global_t = Tile()

    def create_grid_flownode(self, grids_length, grids):
        for i in range(grids_length[0]):
            for j in range(grids_length[1]):
                grids[i, j].index = self.node_index
                self.node_index += 1
                self.flownodes.append(grids[i, j])
                #add connect pad end node
                if grids[i, j].type == -1:
                    self.global_t.contact_pads.append(grids[i, j])
                elif grids[i, j].type==0:
                    self.node_index += 1
                    self.flownodes.append(0)

    def create_tile_flownode(self, tiles_length, tiles):
        for i in range(tiles_length[0]):
            for j in range(tiles_length[1]):
                tiles[i, j].index = self.node_index
                self.node_index += 1
                self.flownodes.append(tiles[i, j])
                self.node_index += 1
                self.flownodes.append(0)

    def create_hub_flownode(self, hubs, hubs_length):
        for i in range(hubs_length):
            hubs[i].index = self.node_index
            self.node_index += 1
            self.flownodes.append(hubs[i])

    def create_electrode_flownode(self, electrode_list: list):
        for electrode in electrode_list:
            electrode.index = self.node_index
            self.node_index += 1
            self.flownodes.append(electrode)

    def create_all_flownode(self):
        self.create_grid_flownode(self.mesh.grids1_length, self.mesh.grids1)
        self.create_grid_flownode(self.mesh.grids2_length, self.mesh.grids2)
        self.create_grid_flownode(self.mesh.grids3_length, self.mesh.grids3)
        self.create_tile_flownode(self.mesh.tiles1_length, self.mesh.tiles1)
        self.create_tile_flownode(self.mesh.tiles3_length, self.mesh.tiles3)
        self.create_hub_flownode(self.mesh.hubs1, self.mesh.hubs1_length)
        self.create_hub_flownode(self.mesh.hubs3, self.mesh.hubs3_length)
        self.create_electrode_flownode(self.mesh.electrodes)

        self.global_t.index = self.node_index
        self.flownodes.append(self.global_t)
        self.node_index += 1

    def create_tiles_path(self, tile_length, tiles, hubs, start, end, shift, all_path):
        for i in range(tile_length[0]):
            for j in range(start,end,shift):
                for c_node in  tiles[i,j].corner_in:
                    if c_node.real_x<tiles[i,j].real_x:
                        if tiles[i,j].flow[0]==1:
                            all_path.append(Wire(int(hubs[i*3+1].real_x),int(tiles[i,j].real_y),int(c_node.real_x),int(c_node.real_y)))
                            tiles[i,j].flow[0]=0
                        elif tiles[i,j].flow[1]==1:
                            all_path.append(Wire(int(hubs[i*3+2].real_x),int(tiles[i,j].real_y),int(c_node.real_x),int(c_node.real_y)))
                            tiles[i,j].flow[1]=0
                    else:
                        if tiles[i,j].flow[1]==1:
                            all_path.append(Wire(int(hubs[i*3+2].real_x),int(tiles[i,j].real_y),int(c_node.real_x),int(c_node.real_y)))
                            tiles[i,j].flow[1]=0
                        elif tiles[i,j].flow[0]==1:
                            all_path.append(Wire(int(hubs[i*3+1].real_x),int(tiles[i,j].real_y),int(c_node.real_x),int(c_node.real_y)))
                            tiles[i,j].flow[0]=0
                if len(tiles[i,j].vertical_path)!=0:		
                    if tiles[i,j].flow[0]==1:
                        all_path.append(Wire(int(hubs[i*3+1].real_x),int(tiles[i,j].real_y),int(hubs[i*3+1].real_x),int(tiles[i,j].vertical_path[0].real_y)))
                        tiles[i,j].vertical_path[0].flow[0]=1
                    if tiles[i,j].flow[1]==1:
                        all_path.append(Wire(int(hubs[i*3+2].real_x),int(tiles[i,j].real_y),int(hubs[i*3+2].real_x),int(tiles[i,j].vertical_path[0].real_y)))
                        tiles[i,j].vertical_path[0].flow[1]=1
    
