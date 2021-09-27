import numpy as np
import math
import sys
import os
from ezdxf.r12writer import r12writer
from operator import itemgetter, attrgetter
from math import atan2,degrees

from degree import Degree
from grid import Grid
from tile import Tile
from hub import Hub
from electrode import Electrode
from wire import Wire
from draw import Draw

class Mesh():

    def __init__(self, Control_pad_unit, Tile_Unit, 
                    block1_shift, block2_shift, block3_shift,
                    grids1_length, grids2_length, grids3_length,
                    tiles1_length, tiles2_length, tiles3_length,
                    hubs1_length, hubs1_y, hubs3_length, hubs3_y):

        self.Control_pad_unit = Control_pad_unit
        self.Tile_Unit = Tile_Unit
        self.block1_shift = block1_shift
        self.block2_shift = block2_shift
        self.block3_shift = block3_shift
        self.grids1_length = grids1_length
        self.grids2_length = grids2_length
        self.grids3_length = grids3_length
        self.tiles1_length = tiles1_length
        self.tiles2_length = tiles2_length
        self.tiles3_length = tiles3_length
        self.hubs1_length = hubs1_length
        self.hubs1_y = hubs1_y
        self.hubs3_length = hubs3_length
        self.hubs3_y = hubs3_y

        # Grid
        self.grids1 = np.empty((grids1_length[0],grids1_length[1]), dtype = Grid)
        self.grids2 = np.empty((grids2_length[0],grids2_length[1]), dtype = Grid)
        self.grids3 = np.empty((grids3_length[0],grids3_length[1]), dtype = Grid)

        # internal
        self.grids4 = np.empty((grids2_length[0],grids2_length[1]), dtype = Grid)

        # Tile
        self.tiles1 = np.empty((tiles1_length[0],tiles1_length[1]), dtype = Tile)
        self.tiles3 = np.empty((tiles3_length[0],tiles3_length[1]), dtype = Tile)

        # Hub
        self.hubs1 = np.empty((hubs1_length), dtype = Hub)
        self.hubs3 = np.empty((hubs3_length), dtype = Hub)

        self.num_electrode = 0
        self.list_electrodes = []

        self.electrodes = []
        self.contactpads = []
        self.contact_line_width = 100
        self.contact_line_width_gap = 20.7

    def point_distance_line(self, _point, _line_point1, _line_point2):
        point = np.array(_point)
        line_point1 = np.array(_line_point1)
        line_point2 = np.array(_line_point2)
        vec1 = line_point1 - point
        vec2 = line_point2 - point
        distance = np.abs(np.cross(vec1,vec2)) / np.linalg.norm(line_point1-line_point2)
        return distance

    def get_points_lines(self, x1, y1, x2, y2, d):
        d_full = ( (x2 - x1)**2 + (y2 - y1)**2 )**0.5
        s = d / d_full
        points = []
        # start at s so we don't duplicate (x1, y1)
        a = s
        while a < 1 - s/2:
            x = (1 - a) * x1 + a * x2
            y = (1 - a) * y1 + a * y2
            points.append( (int(x), int(y)) )
            a += s
        return points

    def get_short_point(self, _point, _line_point1, _line_point2):
        m = (_line_point1[1]-_line_point2[1])/(_line_point1[0]-_line_point2[0]) 
        b = (_line_point1[0]*_line_point1[1] - _line_point2[0]*_line_point1[1])/(_line_point1[0]-_line_point2[0]) 
        x1 = (m*_point[1]+_point[0]-m*b)/((m**2)+1)
        y1 = ((m**2)*_point[1]+m*_point[0]+b)/((m**2)+1)
        return [x1, y1]

    def clockwise_angle(self, v1, v2):
        x1,y1 = v1
        x2,y2 = v2
        dot = x1*x2+y1*y2
        det = x1*y2-y1*x2
        theta = np.arctan2(det, dot)
        theta = theta if theta>0 else 2*np.pi+theta
        return (theta*180/np.pi)

    def create_block(self, x, y, grids, tiles, block_shift, UNIT_LENGTH):
        for i in range(x):
            for j in range(y):
                if grids[i, j] == None:
                    grids[i, j] = Grid(i*UNIT_LENGTH+block_shift[0], j*UNIT_LENGTH+block_shift[1], i, j, 0)
                if i != x-1 and j != y-1:
                    tiles[i, j] = Tile()
                    tiles[i, j].tile_x = i
                    tiles[i, j].tile_y = j
                    tiles[i, j].real_x = i*UNIT_LENGTH+block_shift[0]+UNIT_LENGTH/2
                    tiles[i, j].real_y = j*UNIT_LENGTH+block_shift[1]+UNIT_LENGTH/2

    def create_grid_electrode(self):
        for i in range (self.grids2_length[0]):
            for j in range(self.grids2_length[1]):
                self.grids2[i][j] = Grid(i * self.Tile_Unit + self.block2_shift[0], j * self.Tile_Unit + self.block2_shift[1], i, j, 0)
                self.grids4[i][j] = Grid(i * self.Tile_Unit + self.block2_shift[0], j * self.Tile_Unit + self.block2_shift[1], i, j, 0)

    def create_grid_pad(self):
        self.create_block(self.grids1_length[0], self.grids1_length[1], self.grids1, self.tiles1, self.block1_shift, self.Control_pad_unit)
        self.create_block(self.grids3_length[0], self.grids3_length[1], self.grids3, self.tiles3, self.block3_shift, self.Control_pad_unit)
        #pogo pins
        # self.grids1[7,-1].special=True # need lock
        # self.grids1[15,-1].special=True
        # self.grids1[23,-1].special=True
        # self.grids1[31,-1].special=True
        # self.grids3[14,0].special=True
        # self.grids3[22,0].special=True
        # self.grids3[30,0].special=True
        # self.grids3[38,0].special=True

    def create_hub (self):
        for i in range(self.hubs1_length):
            if i % 3 == 0:
                self.hubs1[i] = Hub(real_x=self.grids1[i//3, self.grids1_length[1]-1].real_x, real_y=self.hubs1_y, type=0, hub_index=i)
                self.hubs3[i] = Hub(real_x=self.grids3[i//3, 0].real_x, real_y=self.hubs3_y, type=0, hub_index=i)
            elif i%3==1:
                thub_real_x1=self.block1_shift[0]+(i//3)*2540+1160+(i%3-1)*220
                thub_real_x2=self.block1_shift[0]+(i//3)*2540+1160+((i+1)%3-1)*220
                thub_grid_x1=(thub_real_x1-self.block2_shift[0])//self.Tile_Unit
                thub_grid_x2=(thub_real_x2-self.block2_shift[0])//self.Tile_Unit
                thub_tile_x1=(thub_real_x1-self.block1_shift[0])//self.Control_pad_unit#(thub_x1*self.Tile_Unit+self.block2_shift[0])//Control_pad_unit
                thub_tile_x2=(thub_real_x1-self.block1_shift[0])//self.Control_pad_unit+1
                #print(thub_real_x1,thub_grid_x1,thub_tile_x1)
                #print((thub_grid_x1*self.Tile_Unit+self.block2_shift[0]),(thub_tile_x1*Control_pad_unit+block1_shift[0]),abs((thub_grid_x1*self.Tile_Unit+self.block2_shift[0])-(thub_tile_x1*Control_pad_unit+block1_shift[0])))
                if thub_grid_x1!=thub_grid_x2:
                    if abs((thub_grid_x1*self.Tile_Unit+self.block2_shift[0])-(thub_tile_x1*self.Control_pad_unit+self.block1_shift[0]))<950:# and abs(thub_real_x1-(thub_tile_x1*Control_pad_unit+block1_shift[0]))<abs(thub_real_x2-(thub_tile_x2*Control_pad_unit+block1_shift[0])):
                        thub_grid_x1+=1
                        thub_grid_x2+=1
                        #dxf.add_circle(center=(thub_grid_x1*self.Tile_Unit+self.block2_shift[0], -hubs1_y), radius = 350.0)
                        #dxf.add_circle(center=(thub_grid_x1*self.Tile_Unit+self.block2_shift[0], -hubs3_y), radius = 350.0)
                    elif abs((thub_grid_x2*self.Tile_Unit+self.block2_shift[0])-(thub_tile_x2*self.Control_pad_unit+self.block1_shift[0]))<950:
                        thub_grid_x1-=1
                        thub_grid_x2-=1
                #print((thub_grid_x1*self.Tile_Unit+self.block2_shift[0]),(thub_tile_x1*Control_pad_unit+block1_shift[0]),((thub_grid_x1+1)*self.Tile_Unit+self.block2_shift[0]),((thub_tile_x1+1)*Control_pad_unit+block1_shift[0]))
                if abs((thub_grid_x1*self.Tile_Unit+self.block2_shift[0])-(thub_tile_x1*self.Control_pad_unit+self.block1_shift[0]))<1000 or abs(((thub_grid_x1+1)*self.Tile_Unit+self.block2_shift[0])-((thub_tile_x1+1)*self.Control_pad_unit+self.block1_shift[0]))<1000:
                    #print(i)
                    #dxf.add_circle(center=(block1_shift[0]+(i//3)*2540+1160+(i%3-1)*220, -hubs1_y), radius = 350.0)
                    #dxf.add_circle(center=(block1_shift[0]+(i//3)*2540+1160+(i%3-1)*220, -hubs3_y), radius = 350.0)
                    self.hubs1[i] = Hub(real_x=self.block1_shift[0]+(i//3)*2540+1160+(i%3-1)*220, real_y=self.hubs1_y, type=1, hub_index=i)
                    self.hubs3[i] = Hub(real_x=self.block1_shift[0]+(i//3)*2540+1160+(i%3-1)*220, real_y=self.hubs3_y, type=1, hub_index=i)
                    i+=1
                    self.hubs1[i] = Hub(real_x=self.block1_shift[0]+(i//3)*2540+1160+(i%3-1)*220, real_y=self.hubs1_y, type=1, hub_index=i)
                    self.hubs3[i] = Hub(real_x=self.block1_shift[0]+(i//3)*2540+1160+(i%3-1)*220, real_y=self.hubs3_y, type=1, hub_index=i)
                else:
                    self.hubs1[i] = Hub(real_x=thub_grid_x1*self.Tile_Unit+self.block2_shift[0], real_y=self.hubs1_y, type=1, hub_index=i)
                    self.hubs3[i] = Hub(real_x=thub_grid_x1*self.Tile_Unit+self.block2_shift[0], real_y=self.hubs3_y, type=1, hub_index=i)
                    i+=1
                    self.hubs1[i] = Hub(real_x=(thub_grid_x1+1)*self.Tile_Unit+self.block2_shift[0], real_y=self.hubs1_y, type=1, hub_index=i)
                    self.hubs3[i] = Hub(real_x=(thub_grid_x1+1)*self.Tile_Unit+self.block2_shift[0], real_y=self.hubs3_y, type=1, hub_index=i)
                
    def _create_neighbor_electrodes(self, i, j, dir): 
        if dir[0]==1 and self.grids2[i-1][j-1].type>0:   #012
                                                    #3 4
                                                    #567
            self.grids2[i][j].neighbor_electrode.append([self.grids2[i-1][j-1].electrode_index,0,-1,-1]) # index dir self.grids2[i-1][j-1]
        if dir[1]==1 and self.grids2[i][j-1].type>0:
            #avoid wire over boundary
            if self.grids2[i][j].real_x < self.electrodes[self.grids2[i][j-1].electrode_index].boundary_L + 150 or self.grids2[i][j].real_x > self.electrodes[self.grids2[i][j-1].electrode_index].boundary_R - 150:
                pass
            else:
                self.grids2[i][j].neighbor_electrode.append([self.grids2[i][j-1].electrode_index,1,0,-1])
        if dir[2]==1 and self.grids2[i+1][j-1].type>0:
            self.grids2[i][j].neighbor_electrode.append([self.grids2[i+1][j-1].electrode_index,2,1,-1])
        if dir[3]==1 and self.grids2[i-1][j].type>0:
            self.grids2[i][j].neighbor_electrode.append([self.grids2[i-1][j].electrode_index,3,-1,0])
        if dir[4]==1 and self.grids2[i+1][j].type>0:
            self.grids2[i][j].neighbor_electrode.append([self.grids2[i+1][j].electrode_index,4,1,0])
        if dir[5]==1 and self.grids2[i-1][j+1].type>0:
            self.grids2[i][j].neighbor_electrode.append([self.grids2[i-1][j+1].electrode_index,5,-1,1])
        if dir[6]==1 and self.grids2[i][j+1].type>0:
            #avoid wire over boundary
            if self.grids2[i][j].real_x < self.electrodes[self.grids2[i][j+1].electrode_index].boundary_L + 150 or self.grids2[i][j].real_x > self.electrodes[self.grids2[i][j+1].electrode_index].boundary_R - 150:
                pass
            else:
                self.grids2[i][j].neighbor_electrode.append([self.grids2[i][j+1].electrode_index,6,0,1])
        if dir[7]==1 and self.grids2[i+1][j+1].type>0:
            self.grids2[i][j].neighbor_electrode.append([self.grids2[i+1][j+1].electrode_index,7,1,1])

    def create_neighbor_electrodes(self):
        for i in range(self.grids2_length[0]):
            lock = False
            for j in range(self.grids2_length[1]):
                if lock==False and self.grids2[i,j].type>0 and self.grids2[i,j+1].type==0 and self.grids2[i,j-1].electrode_index!=self.grids2[i,j].electrode_index :
                    lock = True
                elif lock==True and self.grids2[i,j].type>0 and self.grids2[i,j-1].type==0 and self.grids2[i,j+1].electrode_index!=self.grids2[i,j].electrode_index :
                    lock = False
                elif lock==True and self.grids2[i,j].type>0 and self.grids2[i,j+1].type==0 and self.next_electrode_index(i,j,self.grids2,self.grids2_length[1])!=self.grids2[i,j].electrode_index :
                    lock = False
                dir = [0,0,0,0,0,0,0,0]
                if self.grids2[i,j].type==0 and lock==False:
                    #check 9 directions
                    if i == 0:
                        if j == 0:						# O *
                            dir = [0,0,0,0,1,0,1,1]		# * *

                        elif j == self.grids2_length[1]-1:	# * *
                            dir = [0,1,1,0,1,0,0,0]		# O *

                        else:							# * *
                            dir = [0,1,1,0,1,0,1,1]		# O *
                                                        # * *
                    elif i == self.grids2_length[0]-1:
                        if j == 0:						# * O
                            dir = [0,0,0,1,0,1,1,0]		# * *

                        elif j == self.grids2_length[1]-1:	# * *
                            dir = [1,1,0,1,0,0,0,0]		# * O	

                        else:							# * *
                            dir = [1,1,0,1,0,1,1,0]		# * O
                                                        # * *
                    else:
                        if j == 0:						# * O *
                            dir = [0,0,0,1,1,1,1,1]		# * * *

                        elif j == self.grids2_length[1]-1:	# * * *
                            dir = [1,1,1,1,1,0,0,0]		# * O *

                        else:							# * * *
                            dir = [1,1,1,1,1,1,1,1]		# * O *
                                                        # * * *
                    self._create_neighbor_electrodes(i,j,dir)
            
    def next_electrode_index(self, x,y,grids,length):
        for i in range(y+1,length):
            if grids[x,i].type>0:
                return grids[x,i].electrode_index
        return -1

    def set_safe_distance(self):
        for i in range (self.grids2_length[0]):
            for j in range(self.grids2_length[1]):
                if len(self.grids2[i][j].neighbor_electrode)>0:
                    if i!=0 and len(self.grids2[i-1][j].neighbor_electrode)==0:
                        self.grids2[i-1][j].safe_distance=1
                        #dxf.add_circle(center=(grids2[i-1][j].real_x, -grids2[i][j].real_y), radius = 200.0)
                    if i!=self.grids2_length[0]-1 and len(self.grids2[i+1][j].neighbor_electrode)==0:
                        self.grids2[i+1][j].safe_distance=1
                        #dxf.add_circle(center=(grids2[i+1][j].real_x, -grids2[i][j].real_y), radius = 200.0)

                    #dxf.add_circle(center=(grids2[i][j].real_x, -grids2[i][j].real_y), radius = 50.0)

                #if grids2[i][j].type>0:#check electrode
                #	dxf.add_circle(center=(grids2[i][j].real_x, -grids2[i][j].real_y), radius = 100.0)
            
        for i in range (self.grids2_length[0]):
            for j in range(self.grids2_length[1]):
                if self.grids2[i][j].safe_distance==1:
                    if i!=0 and len(self.grids2[i-1][j].neighbor_electrode)==0 and self.grids2[i-1][j].safe_distance==0:
                        self.grids2[i-1][j].safe_distance2=1
                        #dxf.add_circle(center=(grids2[i-1][j].real_x, -grids2[i][j].real_y), radius = 200.0)
                    if i!=self.grids2_length[0]-1 and len(self.grids2[i+1][j].neighbor_electrode)==0 and self.grids2[i+1][j].safe_distance==0:
                        self.grids2[i+1][j].safe_distance2=1
                        #dxf.add_circle(center=(grids2[i+1][j].real_x, -grids2[i][j].real_y), radius = 200.0)

    #create grids connection
    def _create_grids_connection(self, grids,x,y,dir):
        if dir[0]==1:
            if grids[x-1][y-1].type==0 and len(grids[x-1][y-1].neighbor_electrode)==0 and grids[x-1][y-1].safe_distance==0 and grids[x-1][y-1].safe_distance2==0 or (len(grids[x][y].neighbor_electrode)>0 and grids[x-1][y-1].safe_distance==1) or (grids[x-1][y-1].safe_distance2==1 and grids[x][y].safe_distance==1):
                grids[x][y].neighbor.append([grids[x-1][y-1], 1, self.Tile_Unit*math.sqrt(2)-50])
        if dir[1]==1:
            if grids[x][y-1].type==0 and len(grids[x][y-1].neighbor_electrode)==0 and grids[x][y-1].safe_distance==0 and grids[x][y-1].safe_distance2==0 or (len(grids[x][y].neighbor_electrode)>0 and grids[x][y-1].safe_distance==1) or (grids[x][y-1].safe_distance2==1 and grids[x][y].safe_distance==1):
                grids[x][y].neighbor.append([grids[x][y-1], 1, self.Tile_Unit-100])# max(0,self.Tile_Unit-grids[x][y-1].cost*500)])
        if dir[2]==1:
            if grids[x+1][y-1].type==0 and len(grids[x+1][y-1].neighbor_electrode)==0 and grids[x+1][y-1].safe_distance==0 and grids[x+1][y-1].safe_distance2==0 or (len(grids[x][y].neighbor_electrode)>0 and grids[x+1][y-1].safe_distance==1) or (grids[x+1][y-1].safe_distance2==1 and grids[x][y].safe_distance==1):
                grids[x][y].neighbor.append([grids[x+1][y-1], 1, self.Tile_Unit*math.sqrt(2)-50])
        if dir[3]==1:
            if grids[x-1][y].type==0 and len(grids[x-1][y].neighbor_electrode)==0 and grids[x-1][y].safe_distance==0 and grids[x-1][y].safe_distance2==0 or (len(grids[x][y].neighbor_electrode)>0 and grids[x-1][y].safe_distance==1) or (grids[x-1][y].safe_distance2==1 and grids[x][y].safe_distance==1):
                grids[x][y].neighbor.append([grids[x-1][y], 1, self.Tile_Unit])
        if dir[4]==1:
            if grids[x+1][y].type==0 and len(grids[x+1][y].neighbor_electrode)==0 and grids[x+1][y].safe_distance==0 and grids[x+1][y].safe_distance2==0 or (len(grids[x][y].neighbor_electrode)>0 and grids[x+1][y].safe_distance==1) or (grids[x+1][y].safe_distance2==1 and grids[x][y].safe_distance==1):
                grids[x][y].neighbor.append([grids[x+1][y], 1, self.Tile_Unit])
        if dir[5]==1:
            if grids[x-1][y+1].type==0 and len(grids[x-1][y+1].neighbor_electrode)==0 and grids[x-1][y+1].safe_distance==0 and grids[x-1][y+1].safe_distance2==0 or (len(grids[x][y].neighbor_electrode)>0 and grids[x-1][y+1].safe_distance==1) or (grids[x-1][y+1].safe_distance2==1 and grids[x][y].safe_distance==1):
                grids[x][y].neighbor.append([grids[x-1][y+1], 1, self.Tile_Unit*math.sqrt(2)-50])
        if dir[6]==1:
            if grids[x][y+1].type==0 and len(grids[x][y+1].neighbor_electrode)==0 and grids[x][y+1].safe_distance==0 and grids[x][y+1].safe_distance2==0 or (len(grids[x][y].neighbor_electrode)>0 and grids[x][y+1].safe_distance==1) or (grids[x][y+1].safe_distance2==1 and grids[x][y].safe_distance==1):
                grids[x][y].neighbor.append([grids[x][y+1], 1, self.Tile_Unit-100])# max(0,self.Tile_Unit-grids[x][y+1].cost*500)])
        if dir[7]==1:
            if grids[x+1][y+1].type==0 and len(grids[x+1][y+1].neighbor_electrode)==0 and grids[x+1][y+1].safe_distance==0  and grids[x+1][y+1].safe_distance2==0 or (len(grids[x][y].neighbor_electrode)>0 and grids[x+1][y+1].safe_distance==1) or (grids[x+1][y+1].safe_distance2==1 and grids[x][y].safe_distance==1):
                grids[x][y].neighbor.append([grids[x+1][y+1], 1, self.Tile_Unit*math.sqrt(2)-50])
    
    def create_grids_connection(self):
        for i in range (self.grids2_length[0]):
            for j in range(self.grids2_length[1]):
                dir = [0,0,0,0,0,0,0,0]
                if self.grids2[i,j].type==0:
                    #check 9 directions
                    if i == 0:
                        if j == 0:						# O *
                            dir = [0,0,0,0,1,0,1,1]		# * *

                        elif j == self.grids2_length[1]-1:	# * *
                            dir = [0,1,1,0,1,0,0,0]		# O *

                        else:							# * *
                            dir = [0,1,1,0,1,0,1,1]		# O *
                                                        # * *
                    elif i == self.grids2_length[0]-1:
                        if j == 0:						# * O
                            dir = [0,0,0,1,0,1,1,0]		# * *

                        elif j == self.grids2_length[1]-1:	# * *
                            dir = [1,1,0,1,0,0,0,0]		# * O	

                        else:							# * *
                            dir = [1,1,0,1,0,1,1,0]		# * O
                                                        # * *
                    else:
                        if j == 0:						# * O *
                            dir = [0,0,0,1,1,1,1,1]		# * * *

                        elif j == self.grids2_length[1]-1:	# * * *
                            dir = [1,1,1,1,1,0,0,0]		# * O *

                        else:							# * * *
                            dir = [1,1,1,1,1,1,1,1]		# * O *
                                                        # * * *
                    self._create_grids_connection(self.grids2, i, j, dir) 
                
    def create_tiles_connection(self, tile_length, grids, tiles, block):
        for i in range(tile_length[0]):
            for j in range(tile_length[1]):
                # add corner
                capacity = [8,8,8,8] # u, l, d, r
                for k in (i, i+1):
                    for l in (j, j+1):
                        #contact pads
                        if grids[k, l].type == -1:
                            if grids[k, l].special == False:
                                if block==1 and l==tile_length[1]:
                                    pass
                                elif block==3 and l==0:
                                    pass
                                else:
                                    tiles[i, j].contact_pads.append(grids[k, l])
                            if k == i and l == j:
                                capacity = [2, 2, 2, 2]
                            elif k == i and l == j+1:
                                capacity[3] = 2
                            elif k == i+1 and l == j:
                                capacity[2] = 2
                if i != 0:
                    tiles[i, j].neighbor.append([tiles[i-1, j], capacity[0]])#left
                if i != tile_length[0]-1:
                    tiles[i, j].neighbor.append([tiles[i+1, j], capacity[2]])#right
                if j != 0:
                    tiles[i, j].neighbor.append([tiles[i, j-1], capacity[1]])#top
                if j != tile_length[1]-1:
                    tiles[i, j].neighbor.append([tiles[i, j+1], capacity[3]])#down
                    
    def create_hubs_connection(self, hubs, hubs_length, block2_n, tile_n, grids, tiles):
        for i in range(hubs_length):
            left = int((hubs[i].real_x-self.block1_shift[0]) // self.Tile_Unit)
            right = int((hubs[i].real_x-self.block1_shift[0]) // self.Tile_Unit+1)
            if i%3==0:
                if (hubs[i].real_x - self.grids2[left][block2_n].real_x) > (self.Tile_Unit/2):
                    near = right
                else:
                    near = left
                if grids[i//3][tile_n].special==False:
                    self.grids2[near][block2_n].neighbor.append([hubs[i], 1, 1944])
                    hubs[i].neighbor.append([grids[i//3][tile_n], 1, 1944])
            elif i%3==1:
                if (self.grids2[right][block2_n].real_x - hubs[i].real_x) > (250/2):
                    self.grids2[left][block2_n].neighbor.append([hubs[i], 1, 1944])
                else:
                    self.grids2[right][block2_n].neighbor.append([hubs[i], 1, 1944])
                hubs[i].neighbor.append([tiles[i//3][tile_n], 1, 2694])
            else:
                if (hubs[i].real_x - self.grids2[left][block2_n].real_x) > (250/2):
                    self.grids2[right][block2_n].neighbor.append([hubs[i], 1, 1944])
                else:
                    self.grids2[left][block2_n].neighbor.append([hubs[i], 1, 1944])
                hubs[i].neighbor.append([tiles[i//3][tile_n], 1, 2694])

    def grid_is_available(self, grid, x, y, index):
        # print(x, y)
        # print(self.grids4[x, y].electrode_index)
        if self.grids4[x, y].electrode_index < 0 or self.grids4[x, y].electrode_index == index:
            if grid[x, y].electrode_index < 0 or grid[x, y].electrode_index == index:
                if grid[x, y].conflict == False:
                    return True
        return None

    def grid_conflict(self, grid, x, y):
        if grid[x, y].conflict is False:
            if grid[x, y].inner_grid is not None:
                self.grid_set_electrode(grid, grid[x, y].inner_grid.grid_x, grid[x, y].inner_grid.grid_y, grid[x, y].inner_grid.electrode_index, grid[x, y].inner_grid.electrode_x, grid[x, y].inner_grid.electrode_y)
        grid[x, y].conflict = True
        grid[x, y].electrode_index = -1
        grid[x, y].type = 0
        grid[x, y].electrode_x = 0
        grid[x, y].electrode_y = 0
        # grid[x, y].cost = -1
        return False

    def grid_set_electrode(self, grid, x, y, num_electrode, p1, p2):
        grid[x, y].electrode_index = num_electrode
        grid[x, y].type += 1
        grid[x, y].electrode_x = p1
        grid[x, y].electrode_y = p2

                
    def set_grid_by_electrode_edge(self, shape, shape_scope):
        for electrode in self.list_electrodes:
            for i in range (len(shape)):
                if electrode[2] == shape[i]:
                    true_x = electrode[1]
                    true_y = electrode[0]
                    new_electrode = Electrode(true_x, true_y, i, self.num_electrode)
                    # print(new_electrode.to_dict())
                    self.electrodes.append(new_electrode)
                    boundary_U=true_y
                    boundary_D=true_y
                    boundary_L=true_x
                    boundary_R=true_x
                    electrode_shape_path = shape_scope[i]
                    for j in range(len(electrode_shape_path)-1):
                        x1 = true_x+electrode_shape_path[j][0]
                        y1 = true_y+electrode_shape_path[j][1]
                        x2 = true_x+electrode_shape_path[j+1][0]
                        y2 = true_y+electrode_shape_path[j+1][1]
                        E_grid_x1 = (x1-self.block2_shift[0]) // self.Tile_Unit
                        E_grid_x2 = (x2-self.block2_shift[0]) // self.Tile_Unit
                        E_grid_y1 = (y1-self.block2_shift[1]) // self.Tile_Unit
                        E_grid_y2 = (y2-self.block2_shift[1]) // self.Tile_Unit

                        # print('grid:', E_grid_x1, E_grid_y1, E_grid_x2, E_grid_y2)
                        # print('addr:', x1, y1, x2, y2)
                        if x1>boundary_R:
                            boundary_R=x1
                        if x1<boundary_L:
                            boundary_L=x1
                        if y1<boundary_U:
                            boundary_U=y1
                        if y1>boundary_D:
                            boundary_D=y1


                        ang = self.clockwise_angle([0, -1], [x2-x1, y2-y1])
                        deg = Degree.getdegree(x2, y2, x1, y1)
                        # print(ang, deg)

                        ######### 有角度
                        if ang % 90 != 0:
                            if x1>x2:
                                # |
                                #  \ _
                                if y1>y2:
                                    points = self.get_points_lines(x1, y1, x2, y2, (self.contact_line_width/2) + self.contact_line_width_gap)
                                    # print('point = ', [x1, y1], [x2, y2], 'contact points = ', points)
                                    for p in points:
                                        if points.index(p) == 0:
                                            E_grid_x = (x1-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y1-self.block2_shift[1]) // self.Tile_Unit
                                            _grid = self.grids2[E_grid_x, E_grid_y+1]
                                            _grid.electrode_index=self.num_electrode
                                            _grid.type+=1
                                            _grid.electrode_x = p[0]
                                            _grid.electrode_y = p[1]
                                        if points.index(p) == len(points) - 1:
                                            E_grid_x = (x2-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y2-self.block2_shift[1]) // self.Tile_Unit
                                            _grid = self.grids2[E_grid_x, E_grid_y+1]
                                            _grid.electrode_index=self.num_electrode
                                            _grid.type+=1
                                            _grid.electrode_x = p[0]
                                            _grid.electrode_y = p[1]
                                        E_grid_x = (p[0]-self.block2_shift[0]) // self.Tile_Unit
                                        E_grid_y = (p[1]-self.block2_shift[1]) // self.Tile_Unit
                                        _grid = self.grids2[E_grid_x, E_grid_y+1]
                                        _grid.electrode_index=self.num_electrode
                                        _grid.type+=1
                                        _grid.electrode_x = p[0]
                                        _grid.electrode_y = p[1]

                                #  |
                                # /
                                else:
                                    points = self.get_points_lines(x1, y1, x2, y2, (self.contact_line_width/2) + self.contact_line_width_gap)
                                    # print('point = ', [x1, y1], [x2, y2], 'contact points = ', points)
                                    for p in points:
                                        if points.index(p) == 0:
                                            E_grid_x = (x1-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y1-self.block2_shift[1]) // self.Tile_Unit
                                            _grid = self.grids2[E_grid_x+1, E_grid_y+1]
                                            _grid.electrode_index=self.num_electrode
                                            _grid.type+=1
                                            _grid.electrode_x = p[0]
                                            _grid.electrode_y = p[1]
                                        if points.index(p) == len(points) - 1:
                                            E_grid_x = (x2-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y2-self.block2_shift[1]) // self.Tile_Unit
                                            _grid = self.grids2[E_grid_x+1, E_grid_y+1]
                                            _grid.electrode_index=self.num_electrode
                                            _grid.type+=1
                                            _grid.electrode_x = p[0]
                                            _grid.electrode_y = p[1]
                                        E_grid_x = (p[0]-self.block2_shift[0]) // self.Tile_Unit
                                        E_grid_y = (p[1]-self.block2_shift[1]) // self.Tile_Unit
                                        _grid = self.grids2[E_grid_x+1, E_grid_y+1]
                                        _grid.electrode_index=self.num_electrode
                                        _grid.type+=1
                                        _grid.electrode_x = p[0]
                                        _grid.electrode_y = p[1]

                            elif x1<x2:
                                # \
                                #  |
                                if y1<y2:
                                    points = self.get_points_lines(x1, y1, x2, y2, (self.contact_line_width/2) + self.contact_line_width_gap)
                                    # print('point = ', [x1, y1], [x2, y2], 'contact points = ', points)
                                    for p in points:
                                        if points.index(p) == 0:
                                            E_grid_x = (x1-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y1-self.block2_shift[1]) // self.Tile_Unit
                                            _grid = self.grids2[E_grid_x+1, E_grid_y]
                                            _grid.electrode_index=self.num_electrode
                                            _grid.type+=1
                                            _grid.electrode_x = p[0]
                                            _grid.electrode_y = p[1]
                                        if points.index(p) == len(points) - 1:
                                            E_grid_x = (x2-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y2-self.block2_shift[1]) // self.Tile_Unit
                                            _grid = self.grids2[E_grid_x+1, E_grid_y]
                                            _grid.electrode_index=self.num_electrode
                                            _grid.type+=1
                                            _grid.electrode_x = p[0]
                                            _grid.electrode_y = p[1]
                                        E_grid_x = (p[0]-self.block2_shift[0]) // self.Tile_Unit
                                        E_grid_y = (p[1]-self.block2_shift[1]) // self.Tile_Unit
                                        _grid = self.grids2[E_grid_x+1, E_grid_y]
                                        _grid.electrode_index=self.num_electrode
                                        _grid.type+=1
                                        _grid.electrode_x = p[0]
                                        _grid.electrode_y = p[1]

                                #  /
                                # |
                                else:
                                    points = self.get_points_lines(x1, y1, x2, y2, (self.contact_line_width/2) + self.contact_line_width_gap)
                                    # print('point = ', [x1, y1], [x2, y2], 'contact points = ', points)
                                    for p in points:
                                        if points.index(p) == 0:
                                            E_grid_x = (x1-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y1-self.block2_shift[1]) // self.Tile_Unit
                                            _grid = self.grids2[E_grid_x, E_grid_y]
                                            _grid.electrode_index=self.num_electrode
                                            _grid.type+=1
                                            _grid.electrode_x = p[0]
                                            _grid.electrode_y = p[1]
                                        if points.index(p) == len(points) - 1:
                                            E_grid_x = (x2-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y2-self.block2_shift[1]) // self.Tile_Unit
                                            _grid = self.grids2[E_grid_x, E_grid_y]
                                            _grid.electrode_index=self.num_electrode
                                            _grid.type+=1
                                            _grid.electrode_x = p[0]
                                            _grid.electrode_y = p[1]
                                        E_grid_x = (p[0]-self.block2_shift[0]) // self.Tile_Unit
                                        E_grid_y = (p[1]-self.block2_shift[1]) // self.Tile_Unit
                                        _grid = self.grids2[E_grid_x, E_grid_y]
                                        _grid.electrode_index=self.num_electrode
                                        _grid.type+=1
                                        _grid.electrode_x = p[0]
                                        _grid.electrode_y = p[1]

                        # check_corner=0
                        ######### 直線
                        else:
                            ## ->
                            if ang == 90:
                                for k in range(E_grid_x2 - (E_grid_x1 + 1) + 1):
                                    _gird = self.grids2[E_grid_x1+1+k][E_grid_y1]
                                    _gird.electrode_index=self.num_electrode
                                    _gird.type+=1
                                    _gird.electrode_x = _gird.real_x
                                    _gird.electrode_y = y1
                            ## | down
                            elif ang == 180:
                                for k in range(E_grid_y2 - (E_grid_y1 + 1) + 1):
                                    _grid = self.grids2[E_grid_x1+1][E_grid_y1+1+k]
                                    _grid.electrode_index=self.num_electrode #elector into grid
                                    _grid.type+=1
                                    _grid.electrode_x = x1 
                                    _grid.electrode_y = _grid.real_y
                            ## <-
                            elif ang == 270:
                                for k in range(E_grid_x1 - E_grid_x2):
                                    _grid = self.grids2[E_grid_x1-k][E_grid_y1+1]
                                    _grid.electrode_index=self.num_electrode
                                    _grid.type+=1
                                    _grid.electrode_x = _grid.real_x
                                    _grid.electrode_y = y1
                            ## | up
                            elif ang == 360:
                                for k in range(E_grid_y1 - (E_grid_y2 + 1) + 1):
                                    _grid = self.grids2[E_grid_x1][E_grid_y1-k]
                                    _grid.electrode_index=self.num_electrode
                                    _grid.type+=1
                                    _grid.electrode_x = x1 
                                    _grid.electrode_y = _grid.real_y                    
                    self.electrodes[-1].boundary_U=boundary_U
                    self.electrodes[-1].boundary_D=boundary_D
                    self.electrodes[-1].boundary_L=boundary_L
                    self.electrodes[-1].boundary_R=boundary_R
            self.num_electrode+=1

    def set_grid_by_electrode_edge_internal(self, shape, shape_scope):
        num_electrode = 0
        for electrode in self.list_electrodes:
            for i in range (len(shape)):
                if electrode[2] == shape[i]:
                    true_x = electrode[1]
                    true_y = electrode[0]
                    new_electrode = Electrode(true_x, true_y, i, num_electrode)
                    electrode_shape_path = shape_scope[i]
                    for j in range(len(electrode_shape_path)-1):
                        x1 = true_x+electrode_shape_path[j][0]
                        y1 = true_y+electrode_shape_path[j][1]
                        x2 = true_x+electrode_shape_path[j+1][0]
                        y2 = true_y+electrode_shape_path[j+1][1]
                        E_grid_x1 = (x1-self.block2_shift[0]) // self.Tile_Unit
                        E_grid_x2 = (x2-self.block2_shift[0]) // self.Tile_Unit
                        E_grid_y1 = (y1-self.block2_shift[1]) // self.Tile_Unit
                        E_grid_y2 = (y2-self.block2_shift[1]) // self.Tile_Unit

                        ang = self.clockwise_angle([0, -1], [x2-x1, y2-y1])
                        deg = Degree.getdegree(x2, y2, x1, y1)

                        ######### 直線
                        if ang % 90 == 0:
                            ## ->
                            if ang == 90:
                                for k in range(E_grid_x2 - (E_grid_x1 + 1) + 1):
                                    self.grids4[E_grid_x1+1+k][E_grid_y1+1].electrode_index=num_electrode
                                    self.grids4[E_grid_x1+1+k][E_grid_y1+1].type+=1
                                    self.grids4[E_grid_x1+1+k][E_grid_y1+1].electrode_x = self.grids4[E_grid_x1+k][E_grid_y1].real_x
                                    self.grids4[E_grid_x1+1+k][E_grid_y1+1].electrode_y = y1
                                    self.grids4[E_grid_x1+1+k][E_grid_y1+1].cost = 0
                            #     # self.grids4[E_grid_x2][E_grid_y2+1].electrode_index=num_electrode
                            #     # self.grids4[E_grid_x2][E_grid_y2+1].type+=1
                            #     # self.grids4[E_grid_x2][E_grid_y2+1].electrode_x = self.grids4[E_grid_x1+k][E_grid_y1].real_x
                            #     # self.grids4[E_grid_x2][E_grid_y2+1].electrode_y = y1
                            #     # self.grids4[E_grid_x2][E_grid_y2+1].cost = 0
                            # ## | down
                            if ang == 180:
                                for k in range(E_grid_y2 - (E_grid_y1 + 1) + 1):
                                    self.grids4[E_grid_x1][E_grid_y1+1+k].electrode_index=num_electrode #elector into grid
                                    self.grids4[E_grid_x1][E_grid_y1+1+k].type+=1
                                    self.grids4[E_grid_x1][E_grid_y1+1+k].electrode_x = x1 
                                    self.grids4[E_grid_x1][E_grid_y1+1+k].electrode_y = self.grids4[E_grid_x1][E_grid_y1+k].real_y
                                    self.grids4[E_grid_x1+1+k][E_grid_y1+1].cost = 0
                            ## <-
                            elif ang == 270:
                                for k in range(E_grid_x1 - E_grid_x2):
                                    self.grids4[E_grid_x1-k][E_grid_y1].electrode_index=num_electrode
                                    self.grids4[E_grid_x1-k][E_grid_y1].type+=1
                                    self.grids4[E_grid_x1-k][E_grid_y1].electrode_x = self.grids4[E_grid_x1-k][E_grid_y1].real_x
                                    self.grids4[E_grid_x1-k][E_grid_y1].electrode_y = y1
                                    self.grids4[E_grid_x1+1+k][E_grid_y1+1].cost = 0
                            ## | up
                            elif ang == 360:
                                for k in range(E_grid_y1 - (E_grid_y2 + 1) + 1):
                                    self.grids4[E_grid_x1+1][E_grid_y1-k].electrode_index=num_electrode
                                    self.grids4[E_grid_x1+1][E_grid_y1-k].type+=1
                                    self.grids4[E_grid_x1+1][E_grid_y1-k].electrode_x = x1 
                                    self.grids4[E_grid_x1+1][E_grid_y1-k].electrode_y = self.grids4[E_grid_x1][E_grid_y1-k].real_y
                                    self.grids4[E_grid_x1+1+k][E_grid_y1+1].cost = 0

                    for j in range(len(electrode_shape_path)-1):
                        x1 = true_x+electrode_shape_path[j][0]
                        y1 = true_y+electrode_shape_path[j][1]
                        x2 = true_x+electrode_shape_path[j+1][0]
                        y2 = true_y+electrode_shape_path[j+1][1]
                        E_grid_x1 = (x1-self.block2_shift[0]) // self.Tile_Unit
                        E_grid_x2 = (x2-self.block2_shift[0]) // self.Tile_Unit
                        E_grid_y1 = (y1-self.block2_shift[1]) // self.Tile_Unit
                        E_grid_y2 = (y2-self.block2_shift[1]) // self.Tile_Unit

                        ang = self.clockwise_angle([0, -1], [x2-x1, y2-y1])
                        deg = Degree.getdegree(x2, y2, x1, y1)

                        ######### 有角度
                        if ang % 90 != 0:
                            if x1>x2:
                                # |
                                #  \ _
                                if y1>y2:
                                    points = self.get_points_lines(x1, y1, x2, y2, (self.contact_line_width/2) + self.contact_line_width_gap)
                                    for p in points:
                                        if points.index(p) == 0:
                                            E_grid_x = (x1-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y1-self.block2_shift[1]) // self.Tile_Unit
                                            _grid = self.grids4[E_grid_x+1, E_grid_y]
                                            _grid.electrode_index=num_electrode
                                            _grid.type+=1
                                            _grid.electrode_x = p[0]
                                            _grid.electrode_y = p[1]
                                            _grid.cost = 0
                                        if points.index(p) == len(points) - 1:
                                            E_grid_x = (x2-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y2-self.block2_shift[1]) // self.Tile_Unit
                                            _grid = self.grids4[E_grid_x+1, E_grid_y]
                                            _grid.electrode_index=num_electrode
                                            _grid.type+=1
                                            _grid.electrode_x = p[0]
                                            _grid.electrode_y = p[1]
                                            _grid.cost = 0
                                        E_grid_x = (p[0]-self.block2_shift[0]) // self.Tile_Unit
                                        E_grid_y = (p[1]-self.block2_shift[1]) // self.Tile_Unit
                                        _grid = self.grids4[E_grid_x+1, E_grid_y]
                                        _grid.electrode_index=num_electrode
                                        _grid.type+=1
                                        _grid.electrode_x = p[0]
                                        _grid.electrode_y = p[1]
                                        _grid.cost = 0
                                #  |
                                # /
                                else:
                                    points = self.get_points_lines(x1, y1, x2, y2, (self.contact_line_width/2) + self.contact_line_width_gap)
                                    for p in points:
                                        if points.index(p) == 0:
                                            E_grid_x = (x1-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y1-self.block2_shift[1]) // self.Tile_Unit
                                            _grid = self.grids4[E_grid_x, E_grid_y]
                                            # if _grid.real_x < x1 and _grid.real_y < y1:
                                            _grid.electrode_index=num_electrode
                                            _grid.type+=1
                                            _grid.electrode_x = p[0]
                                            _grid.electrode_y = p[1]
                                            _grid.cost = 0
                                        if points.index(p) == len(points) - 1:
                                            E_grid_x = (x2-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y2-self.block2_shift[1]) // self.Tile_Unit
                                            # if _grid.real_x < x2 and _grid.real_y < y2:
                                            _grid = self.grids4[E_grid_x, E_grid_y]
                                            _grid.electrode_index=num_electrode
                                            _grid.type+=1
                                            _grid.electrode_x = p[0]
                                            _grid.electrode_y = p[1]
                                            _grid.cost = 0
                                        E_grid_x = (p[0]-self.block2_shift[0]) // self.Tile_Unit
                                        E_grid_y = (p[1]-self.block2_shift[1]) // self.Tile_Unit
                                        # if _grid.real_x < p[0] and _grid.real_y < p[1]:
                                        _grid = self.grids4[E_grid_x, E_grid_y]
                                        _grid.electrode_index=num_electrode
                                        _grid.type+=1
                                        _grid.electrode_x = p[0]
                                        _grid.electrode_y = p[1]
                                        _grid.cost = 0

                            elif x1<x2:
                                # \
                                #  |
                                if y1<y2:
                                    points = self.get_points_lines(x1, y1, x2, y2, (self.contact_line_width/2) + self.contact_line_width_gap)
                                    for p in points:
                                        if points.index(p) == 0:
                                            E_grid_x = (x1-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y1-self.block2_shift[1]) // self.Tile_Unit
                                            _grid = self.grids4[E_grid_x, E_grid_y+1]
                                            _grid.electrode_index=num_electrode
                                            _grid.type+=1
                                            _grid.electrode_x = p[0]
                                            _grid.electrode_y = p[1]
                                            _grid.cost = 0
                                        if points.index(p) == len(points) - 1:
                                            E_grid_x = (x2-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y2-self.block2_shift[1]) // self.Tile_Unit
                                            _grid = self.grids4[E_grid_x, E_grid_y+1]
                                            _grid.electrode_index=num_electrode
                                            _grid.type+=1
                                            _grid.electrode_x = p[0]
                                            _grid.electrode_y = p[1]
                                            _grid.cost = 0
                                        E_grid_x = (p[0]-self.block2_shift[0]) // self.Tile_Unit
                                        E_grid_y = (p[1]-self.block2_shift[1]) // self.Tile_Unit
                                        _grid = self.grids4[E_grid_x, E_grid_y+1]
                                        _grid.electrode_index=num_electrode
                                        _grid.type+=1
                                        _grid.electrode_x = p[0]
                                        _grid.electrode_y = p[1]
                                        _grid.cost = 0

                                #  /
                                # |
                                else:
                                    points = self.get_points_lines(x1, y1, x2, y2, (self.contact_line_width/2) + self.contact_line_width_gap)
                                    for p in points:
                                        if points.index(p) == 0:
                                            E_grid_x = (x1-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y1-self.block2_shift[1]) // self.Tile_Unit
                                            _grid = self.grids4[E_grid_x+1, E_grid_y+1]
                                            _grid.electrode_index=num_electrode
                                            _grid.type+=1
                                            _grid.electrode_x = p[0]
                                            _grid.electrode_y = p[1]
                                            _grid.cost = 0
                                        if points.index(p) == len(points) - 1:
                                            E_grid_x = (x2-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y2-self.block2_shift[1]) // self.Tile_Unit
                                            _grid = self.grids4[E_grid_x+1, E_grid_y+1]
                                            _grid.electrode_index=num_electrode
                                            _grid.type+=1
                                            _grid.electrode_x = p[0]
                                            _grid.electrode_y = p[1]
                                            _grid.cost = 0
                                        E_grid_x = (p[0]-self.block2_shift[0]) // self.Tile_Unit
                                        E_grid_y = (p[1]-self.block2_shift[1]) // self.Tile_Unit
                                        _grid = self.grids4[E_grid_x+1, E_grid_y+1]
                                        _grid.electrode_index=num_electrode
                                        _grid.type+=1
                                        _grid.electrode_x = p[0]
                                        _grid.electrode_y = p[1]
                                        _grid.cost = 0
            num_electrode+=1

    def set_grid_by_electrode_edge_not_internal(self, shape, shape_scope):
        for electrode in self.list_electrodes:
            for i in range (len(shape)):
                if electrode[2] == shape[i]:
                    true_x = electrode[1]
                    true_y = electrode[0]
                    new_electrode = Electrode(true_x, true_y, i, self.num_electrode)
                    # print(new_electrode.to_dict())
                    self.electrodes.append(new_electrode)
                    boundary_U=true_y
                    boundary_D=true_y
                    boundary_L=true_x
                    boundary_R=true_x
                    electrode_shape_path = shape_scope[i]
                    for j in range(len(electrode_shape_path)-1):
                        x1 = true_x+electrode_shape_path[j][0]
                        y1 = true_y+electrode_shape_path[j][1]
                        x2 = true_x+electrode_shape_path[j+1][0]
                        y2 = true_y+electrode_shape_path[j+1][1]
                        E_grid_x1 = (x1-self.block2_shift[0]) // self.Tile_Unit
                        E_grid_x2 = (x2-self.block2_shift[0]) // self.Tile_Unit
                        E_grid_y1 = (y1-self.block2_shift[1]) // self.Tile_Unit
                        E_grid_y2 = (y2-self.block2_shift[1]) // self.Tile_Unit

                        # print('grid:', E_grid_x1, E_grid_y1, E_grid_x2, E_grid_y2)
                        # print('addr:', x1, y1, x2, y2)
                        if x1>boundary_R:
                            boundary_R=x1
                        if x1<boundary_L:
                            boundary_L=x1
                        if y1<boundary_U:
                            boundary_U=y1
                        if y1>boundary_D:
                            boundary_D=y1


                        ang = self.clockwise_angle([0, -1], [x2-x1, y2-y1])
                        deg = Degree.getdegree(x2, y2, x1, y1)
                        # print(ang, deg)

                        ######### 有角度
                        if ang % 90 != 0:
                            if x1>x2:
                                # |
                                #  \ _
                                if y1>y2:
                                    points = self.get_points_lines(x1, y1, x2, y2, (self.contact_line_width/2) + self.contact_line_width_gap)
                                    # print('point = ', [x1, y1], [x2, y2], 'contact points = ', points)
                                    for p in points:
                                        if points.index(p) == 0:
                                            E_grid_x = (x1-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y1-self.block2_shift[1]) // self.Tile_Unit
                                            if self.grids4[E_grid_x][E_grid_y].electrode_index < 0:
                                                _grid = self.grids2[E_grid_x, E_grid_y+1]
                                                _grid.electrode_index=self.num_electrode
                                                _grid.type+=1
                                                _grid.electrode_x = p[0]
                                                _grid.electrode_y = p[1]
                                        if points.index(p) == len(points) - 1:
                                            E_grid_x = (x2-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y2-self.block2_shift[1]) // self.Tile_Unit
                                            if self.grids4[E_grid_x][E_grid_y].electrode_index < 0:
                                                _grid = self.grids2[E_grid_x, E_grid_y+1]
                                                _grid.electrode_index=self.num_electrode
                                                _grid.type+=1
                                                _grid.electrode_x = p[0]
                                                _grid.electrode_y = p[1]
                                        E_grid_x = (p[0]-self.block2_shift[0]) // self.Tile_Unit
                                        E_grid_y = (p[1]-self.block2_shift[1]) // self.Tile_Unit
                                        if self.grids4[E_grid_x][E_grid_y].electrode_index < 0:
                                            _grid = self.grids2[E_grid_x, E_grid_y+1]
                                            _grid.electrode_index=self.num_electrode
                                            _grid.type+=1
                                            _grid.electrode_x = p[0]
                                            _grid.electrode_y = p[1]

                                #  |
                                # /
                                else:
                                    points = self.get_points_lines(x1, y1, x2, y2, (self.contact_line_width/2) + self.contact_line_width_gap)
                                    # print('point = ', [x1, y1], [x2, y2], 'contact points = ', points)
                                    for p in points:
                                        if points.index(p) == 0:
                                            E_grid_x = (x1-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y1-self.block2_shift[1]) // self.Tile_Unit
                                            if self.grids4[E_grid_x][E_grid_y].electrode_index < 0:
                                                _grid = self.grids2[E_grid_x+1, E_grid_y+1]
                                                _grid.electrode_index=self.num_electrode
                                                _grid.type+=1
                                                _grid.electrode_x = p[0]
                                                _grid.electrode_y = p[1]
                                        if points.index(p) == len(points) - 1:
                                            E_grid_x = (x2-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y2-self.block2_shift[1]) // self.Tile_Unit
                                            if self.grids4[E_grid_x][E_grid_y].electrode_index < 0:
                                                _grid = self.grids2[E_grid_x+1, E_grid_y+1]
                                                _grid.electrode_index=self.num_electrode
                                                _grid.type+=1
                                                _grid.electrode_x = p[0]
                                                _grid.electrode_y = p[1]
                                        E_grid_x = (p[0]-self.block2_shift[0]) // self.Tile_Unit
                                        E_grid_y = (p[1]-self.block2_shift[1]) // self.Tile_Unit
                                        if self.grids4[E_grid_x][E_grid_y].electrode_index < 0:
                                            _grid = self.grids2[E_grid_x+1, E_grid_y+1]
                                            _grid.electrode_index=self.num_electrode
                                            _grid.type+=1
                                            _grid.electrode_x = p[0]
                                            _grid.electrode_y = p[1]

                            elif x1<x2:
                                # \
                                #  |
                                if y1<y2:
                                    points = self.get_points_lines(x1, y1, x2, y2, (self.contact_line_width/2) + self.contact_line_width_gap)
                                    # print('point = ', [x1, y1], [x2, y2], 'contact points = ', points)
                                    for p in points:
                                        if points.index(p) == 0:
                                            E_grid_x = (x1-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y1-self.block2_shift[1]) // self.Tile_Unit
                                            if self.grids4[E_grid_x][E_grid_y].electrode_index < 0:
                                                _grid = self.grids2[E_grid_x+1, E_grid_y]
                                                _grid.electrode_index=self.num_electrode
                                                _grid.type+=1
                                                _grid.electrode_x = p[0]
                                                _grid.electrode_y = p[1]
                                        if points.index(p) == len(points) - 1:
                                            E_grid_x = (x2-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y2-self.block2_shift[1]) // self.Tile_Unit
                                            if self.grids4[E_grid_x][E_grid_y].electrode_index < 0:
                                                _grid = self.grids2[E_grid_x+1, E_grid_y]
                                                _grid.electrode_index=self.num_electrode
                                                _grid.type+=1
                                                _grid.electrode_x = p[0]
                                                _grid.electrode_y = p[1]
                                        E_grid_x = (p[0]-self.block2_shift[0]) // self.Tile_Unit
                                        E_grid_y = (p[1]-self.block2_shift[1]) // self.Tile_Unit
                                        if self.grids4[E_grid_x][E_grid_y].electrode_index < 0:
                                            _grid = self.grids2[E_grid_x+1, E_grid_y]
                                            _grid.electrode_index=self.num_electrode
                                            _grid.type+=1
                                            _grid.electrode_x = p[0]
                                            _grid.electrode_y = p[1]

                                #  /
                                # |
                                else:
                                    points = self.get_points_lines(x1, y1, x2, y2, (self.contact_line_width/2) + self.contact_line_width_gap)
                                    # print('point = ', [x1, y1], [x2, y2], 'contact points = ', points)
                                    for p in points:
                                        if points.index(p) == 0:
                                            E_grid_x = (x1-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y1-self.block2_shift[1]) // self.Tile_Unit
                                            if self.grids4[E_grid_x][E_grid_y].electrode_index < 0:
                                                _grid = self.grids2[E_grid_x, E_grid_y]
                                                _grid.electrode_index=self.num_electrode
                                                _grid.type+=1
                                                _grid.electrode_x = p[0]
                                                _grid.electrode_y = p[1]
                                        if points.index(p) == len(points) - 1:
                                            E_grid_x = (x2-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y2-self.block2_shift[1]) // self.Tile_Unit
                                            if self.grids4[E_grid_x][E_grid_y].electrode_index < 0:
                                                _grid = self.grids2[E_grid_x, E_grid_y]
                                                _grid.electrode_index=self.num_electrode
                                                _grid.type+=1
                                                _grid.electrode_x = p[0]
                                                _grid.electrode_y = p[1]
                                        E_grid_x = (p[0]-self.block2_shift[0]) // self.Tile_Unit
                                        E_grid_y = (p[1]-self.block2_shift[1]) // self.Tile_Unit
                                        if self.grids4[E_grid_x][E_grid_y].electrode_index < 0:
                                            _grid = self.grids2[E_grid_x, E_grid_y]
                                            _grid.electrode_index=self.num_electrode
                                            _grid.type+=1
                                            _grid.electrode_x = p[0]
                                            _grid.electrode_y = p[1]

                        # check_corner=0
                        ######### 直線
                        else:
                            ## ->
                            if ang == 90:
                                for k in range(E_grid_x2 - (E_grid_x1 + 1) + 1):
                                    if self.grids4[E_grid_x1+1+k][E_grid_y1].electrode_index < 0:
                                        _gird = self.grids2[E_grid_x1+1+k][E_grid_y1]
                                        _gird.electrode_index=self.num_electrode
                                        _gird.type+=1
                                        _gird.electrode_x = _gird.real_x
                                        _gird.electrode_y = y1
                            ## | down
                            elif ang == 180:
                                for k in range(E_grid_y2 - (E_grid_y1 + 1) + 1):
                                    if self.grids4[E_grid_x1+1][E_grid_y1+1+k].electrode_index < 0:
                                        _grid = self.grids2[E_grid_x1+1][E_grid_y1+1+k]
                                        _grid.electrode_index=self.num_electrode #elector into grid
                                        _grid.type+=1
                                        _grid.electrode_x = x1 
                                        _grid.electrode_y = _grid.real_y
                            ## <-
                            elif ang == 270:
                                for k in range(E_grid_x1 - E_grid_x2):
                                    if self.grids4[E_grid_x1-k][E_grid_y1+1].electrode_index < 0:
                                        _grid = self.grids2[E_grid_x1-k][E_grid_y1+1]
                                        _grid.electrode_index=self.num_electrode
                                        _grid.type+=1
                                        _grid.electrode_x = _grid.real_x
                                        _grid.electrode_y = y1
                            ## | up
                            elif ang == 360:
                                for k in range(E_grid_y1 - (E_grid_y2 + 1) + 1):
                                    if self.grids4[E_grid_x1][E_grid_y1-k].electrode_index < 0:
                                        _grid = self.grids2[E_grid_x1][E_grid_y1-k]
                                        _grid.electrode_index=self.num_electrode
                                        _grid.type+=1
                                        _grid.electrode_x = x1 
                                        _grid.electrode_y = _grid.real_y
                    self.electrodes[-1].boundary_U=boundary_U
                    self.electrodes[-1].boundary_D=boundary_D
                    self.electrodes[-1].boundary_L=boundary_L
                    self.electrodes[-1].boundary_R=boundary_R
            self.num_electrode+=1

    def set_grid_by_electrode_edge_opt(self, shape, shape_scope):
        for electrode in self.list_electrodes:
            for i in range (len(shape)):
                if electrode[2] == shape[i]:
                    true_x = electrode[1]
                    true_y = electrode[0]
                    new_electrode = Electrode(true_x, true_y, i, self.num_electrode)
                    # print(new_electrode.to_dict())
                    self.electrodes.append(new_electrode)
                    boundary_U=true_y
                    boundary_D=true_y
                    boundary_L=true_x
                    boundary_R=true_x
                    electrode_shape_path = shape_scope[i]
                    for j in range(len(electrode_shape_path)-1):
                        x1 = true_x+electrode_shape_path[j][0]
                        y1 = true_y+electrode_shape_path[j][1]
                        x2 = true_x+electrode_shape_path[j+1][0]
                        y2 = true_y+electrode_shape_path[j+1][1]
                        E_grid_x1 = (x1-self.block2_shift[0]) // self.Tile_Unit
                        E_grid_x2 = (x2-self.block2_shift[0]) // self.Tile_Unit
                        E_grid_y1 = (y1-self.block2_shift[1]) // self.Tile_Unit
                        E_grid_y2 = (y2-self.block2_shift[1]) // self.Tile_Unit

                        # print('grid:', E_grid_x1, E_grid_y1, E_grid_x2, E_grid_y2)
                        # print('addr:', x1, y1, x2, y2)
                        if x1>boundary_R:
                            boundary_R=x1
                        if x1<boundary_L:
                            boundary_L=x1
                        if y1<boundary_U:
                            boundary_U=y1
                        if y1>boundary_D:
                            boundary_D=y1


                        ang = self.clockwise_angle([0, -1], [x2-x1, y2-y1])
                        deg = Degree.getdegree(x2, y2, x1, y1)
                        # print(ang, deg)

                        ######### 有角度
                        if ang % 90 != 0:
                            if x1>x2:
                                # |
                                #  \ _
                                if y1>y2:
                                    points = self.get_points_lines(x1, y1, x2, y2, (self.contact_line_width/2) + self.contact_line_width_gap)
                                    # print('point = ', [x1, y1], [x2, y2], 'contact points = ', points)
                                    for p in points:
                                        if points.index(p) == 0:
                                            E_grid_x = (x1-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y1-self.block2_shift[1]) // self.Tile_Unit
                                            if self.grid_is_available(self.grids2, E_grid_x, E_grid_y+1, self.num_electrode):
                                                self.grid_set_electrode(self.grids2, E_grid_x, E_grid_y+1, self.num_electrode, p[0], p[1])
                                            # internal 1,0
                                            else:
                                                self.grid_conflict(self.grids2, E_grid_x, E_grid_y+1)
                                                self.grids2[E_grid_x+1][E_grid_y] = self.grids4[E_grid_x+1][E_grid_y]
                                                # self.grid_set_electrode(self.grids2, E_grid_x+1, E_grid_y, self.num_electrode, p[0], p[1])
                                        if points.index(p) == len(points) - 1:
                                            E_grid_x = (x2-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y2-self.block2_shift[1]) // self.Tile_Unit
                                            if self.grid_is_available(self.grids2, E_grid_x, E_grid_y+1, self.num_electrode):
                                                self.grid_set_electrode(self.grids2, E_grid_x, E_grid_y+1, self.num_electrode, p[0], p[1])
                                            # internal 1,0
                                            else:
                                                self.grid_conflict(self.grids2, E_grid_x, E_grid_y+1)
                                                self.grids2[E_grid_x+1][E_grid_y] = self.grids4[E_grid_x+1][E_grid_y]
                                                # self.grid_set_electrode(self.grids2, E_grid_x+1, E_grid_y, self.num_electrode, p[0], p[1])
                                        E_grid_x = (p[0]-self.block2_shift[0]) // self.Tile_Unit
                                        E_grid_y = (p[1]-self.block2_shift[1]) // self.Tile_Unit
                                        if self.grid_is_available(self.grids2, E_grid_x, E_grid_y+1, self.num_electrode):
                                            self.grid_set_electrode(self.grids2, E_grid_x, E_grid_y+1, self.num_electrode, p[0], p[1])
                                        # internal 1,0
                                        else:
                                            self.grid_conflict(self.grids2, E_grid_x, E_grid_y+1)
                                            self.grids2[E_grid_x+1][E_grid_y] = self.grids4[E_grid_x+1][E_grid_y]
                                            # self.grid_set_electrode(self.grids2, E_grid_x+1, E_grid_y, self.num_electrode, p[0], p[1])

                                #  |
                                # /
                                else:
                                    points = self.get_points_lines(x1, y1, x2, y2, (self.contact_line_width/2) + self.contact_line_width_gap)
                                    # print('point = ', [x1, y1], [x2, y2], 'contact points = ', points)
                                    for p in points:
                                        if points.index(p) == 0:
                                            E_grid_x = (x1-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y1-self.block2_shift[1]) // self.Tile_Unit
                                            if self.grid_is_available(self.grids2, E_grid_x+1, E_grid_y+1, self.num_electrode):
                                                self.grid_set_electrode(self.grids2, E_grid_x+1, E_grid_y+1, self.num_electrode, p[0], p[1])
                                            # internal 0,0
                                            else:
                                                self.grid_conflict(self.grids2, E_grid_x+1, E_grid_y+1)
                                                self.grids2[E_grid_x][E_grid_y] = self.grids4[E_grid_x][E_grid_y]
                                                # self.grid_set_electrode(self.grids2, E_grid_x, E_grid_y, self.num_electrode, p[0], p[1])
                                        if points.index(p) == len(points) - 1:
                                            E_grid_x = (x2-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y2-self.block2_shift[1]) // self.Tile_Unit
                                            if self.grid_is_available(self.grids2, E_grid_x+1, E_grid_y+1, self.num_electrode):
                                                self.grid_set_electrode(self.grids2, E_grid_x+1, E_grid_y+1, self.num_electrode, p[0], p[1])
                                            # internal 0,0
                                            else:
                                                self.grid_conflict(self.grids2, E_grid_x+1, E_grid_y+1)
                                                self.grids2[E_grid_x][E_grid_y] = self.grids4[E_grid_x][E_grid_y]
                                                # self.grid_set_electrode(self.grids2, E_grid_x, E_grid_y, self.num_electrode, p[0], p[1])
                                        E_grid_x = (p[0]-self.block2_shift[0]) // self.Tile_Unit
                                        E_grid_y = (p[1]-self.block2_shift[1]) // self.Tile_Unit
                                        if self.grid_is_available(self.grids2, E_grid_x+1, E_grid_y+1, self.num_electrode):
                                            self.grid_set_electrode(self.grids2, E_grid_x+1, E_grid_y+1, self.num_electrode, p[0], p[1])
                                        # internal 0,0
                                        else:
                                            self.grid_conflict(self.grids2, E_grid_x+1, E_grid_y+1)
                                            self.grids2[E_grid_x+1][E_grid_y] = self.grids4[E_grid_x+1][E_grid_y]
                                            # self.grid_set_electrode(self.grids2, E_grid_x, E_grid_y, self.num_electrode, p[0], p[1])

                            elif x1<x2:
                                # \
                                #  |
                                if y1<y2:
                                    points = self.get_points_lines(x1, y1, x2, y2, (self.contact_line_width/2) + self.contact_line_width_gap)
                                    # print('point = ', [x1, y1], [x2, y2], 'contact points = ', points)
                                    for p in points:
                                        if points.index(p) == 0:
                                            E_grid_x = (x1-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y1-self.block2_shift[1]) // self.Tile_Unit
                                            if self.grid_is_available(self.grids2, E_grid_x+1, E_grid_y, self.num_electrode):
                                                self.grid_set_electrode(self.grids2, E_grid_x+1, E_grid_y, self.num_electrode, p[0], p[1])
                                            # internal 0,1
                                            else:
                                                self.grid_conflict(self.grids2, E_grid_x+1, E_grid_y)
                                                self.grids2[E_grid_x, E_grid_y+1] = self.grids4[E_grid_x, E_grid_y+1]
                                                # self.grid_set_electrode(self.grids2, E_grid_x, E_grid_y+1, self.num_electrode, p[0], p[1])
                                        if points.index(p) == len(points) - 1:
                                            E_grid_x = (x2-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y2-self.block2_shift[1]) // self.Tile_Unit
                                            if self.grid_is_available(self.grids2, E_grid_x+1, E_grid_y, self.num_electrode):
                                                self.grid_set_electrode(self.grids2, E_grid_x+1, E_grid_y, self.num_electrode, p[0], p[1])
                                            # internal 0,1
                                            else:
                                                self.grid_conflict(self.grids2, E_grid_x+1, E_grid_y)
                                                self.grids2[E_grid_x, E_grid_y+1] = self.grids4[E_grid_x, E_grid_y+1]
                                                # self.grid_set_electrode(self.grids2, E_grid_x, E_grid_y+1, self.num_electrode, p[0], p[1])
                                        E_grid_x = (p[0]-self.block2_shift[0]) // self.Tile_Unit
                                        E_grid_y = (p[1]-self.block2_shift[1]) // self.Tile_Unit
                                        if self.grid_is_available(self.grids2, E_grid_x+1, E_grid_y, self.num_electrode):
                                            self.grid_set_electrode(self.grids2, E_grid_x+1, E_grid_y, self.num_electrode, p[0], p[1])
                                        # internal 0,1
                                        else:
                                            self.grid_conflict(self.grids2, E_grid_x+1, E_grid_y)
                                            self.grids2[E_grid_x, E_grid_y+1] = self.grids4[E_grid_x, E_grid_y+1]
                                            # self.grid_set_electrode(self.grids2, E_grid_x, E_grid_y+1, self.num_electrode, p[0], p[1])
                                #  /
                                # |
                                else:
                                    points = self.get_points_lines(x1, y1, x2, y2, (self.contact_line_width/2) + self.contact_line_width_gap)
                                    # print('point = ', [x1, y1], [x2, y2], 'contact points = ', points)
                                    for p in points:
                                        if points.index(p) == 0:
                                            E_grid_x = (x1-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y1-self.block2_shift[1]) // self.Tile_Unit
                                            if self.grid_is_available(self.grids2, E_grid_x, E_grid_y, self.num_electrode):
                                                self.grid_set_electrode(self.grids2, E_grid_x, E_grid_y, self.num_electrode, p[0], p[1])
                                                # print(self.grids2[E_grid_x, E_grid_y].to_dict())
                                            # internal 1,1
                                            else:
                                                self.grid_conflict(self.grids2, E_grid_x, E_grid_y)
                                                self.grids2[E_grid_x+1, E_grid_y+1] = self.grids4[E_grid_x+1, E_grid_y+1]
                                                # print(self.grids2[E_grid_x, E_grid_y].to_dict())
                                                # self.grid_set_electrode(self.grids2, E_grid_x+1, E_grid_y+1, self.num_electrode, p[0], p[1])
                                        if points.index(p) == len(points) - 1:
                                            E_grid_x = (x2-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y2-self.block2_shift[1]) // self.Tile_Unit
                                            if self.grid_is_available(self.grids2, E_grid_x, E_grid_y, self.num_electrode):
                                                self.grid_set_electrode(self.grids2, E_grid_x, E_grid_y, self.num_electrode, p[0], p[1])
                                            # internal 1,1
                                            else:
                                                self.grid_conflict(self.grids2, E_grid_x, E_grid_y)
                                                self.grids2[E_grid_x+1, E_grid_y+1] = self.grids4[E_grid_x+1, E_grid_y+1]
                                                # self.grid_set_electrode(self.grids2, E_grid_x+1, E_grid_y+1, self.num_electrode, p[0], p[1])
                                        E_grid_x = (p[0]-self.block2_shift[0]) // self.Tile_Unit
                                        E_grid_y = (p[1]-self.block2_shift[1]) // self.Tile_Unit
                                        if self.grid_is_available(self.grids2, E_grid_x, E_grid_y, self.num_electrode):
                                            self.grid_set_electrode(self.grids2, E_grid_x, E_grid_y, self.num_electrode, p[0], p[1])
                                        # internal 1,1
                                        else:
                                            self.grid_conflict(self.grids2, E_grid_x, E_grid_y)
                                            self.grids2[E_grid_x+1, E_grid_y+1] = self.grids4[E_grid_x+1, E_grid_y+1]
                                            # self.grid_set_electrode(self.grids2, E_grid_x+1, E_grid_y+1, self.num_electrode, p[0], p[1])
                        # check_corner=0
                        ######### 直線
                        else:
                            ## ->
                            if ang == 90:
                                for k in range(E_grid_x2 - (E_grid_x1) + 1):
                                    # if self.grids4[E_grid_x1+1+k][E_grid_y1].electrode_index < 0:
                                    if self.grid_is_available(self.grids2, E_grid_x1+1+k, E_grid_y1, self.num_electrode):
                                            # if self.grids2[E_grid_x1+1+k][E_grid_y1+1].electrode_index < 0:
                                        self.grid_set_electrode(self.grids2, E_grid_x1+1+k, E_grid_y1, self.num_electrode, self.grids2[E_grid_x1+1+k][E_grid_y1].real_x, y1)
                                    # internal 1,1
                                    else:
                                        self.grid_conflict(self.grids2, E_grid_x1+1+k, E_grid_y1)
                                        # self.grid_set_electrode(self.grids2, E_grid_x1+1+k, E_grid_y1+1, self.num_electrode, self.grids2[E_grid_x1+1+k][E_grid_y1+1].real_x, y1)
                            ## | down
                            elif ang == 180:
                                for k in range(E_grid_y2 - (E_grid_y1 + 1) + 1):
                                    if self.grid_is_available(self.grids2, E_grid_x1+1, E_grid_y1+1+k, self.num_electrode):
                                        # if self.grids2[E_grid_x1, E_grid_y1+1+k].electrode_index < 0:
                                        self.grid_set_electrode(self.grids2, E_grid_x1+1, E_grid_y1+1+k, self.num_electrode, x1, self.grids2[E_grid_x1+1][E_grid_y1+1+k].real_y)
                                    # internal 0,1
                                    else:
                                        self.grid_conflict(self.grids2, E_grid_x1+1, E_grid_y1+1+k)
                                        # self.grid_set_electrode(self.grids2, E_grid_x1, E_grid_y1+1+k, self.num_electrode, x1, self.grids2[E_grid_x1][E_grid_y1+1+k].real_y)
                            ## <-
                            elif ang == 270:
                                for k in range(E_grid_x1 - E_grid_x2):
                                    if self.grid_is_available(self.grids2, E_grid_x1-k, E_grid_y1+1, self.num_electrode):
                                        # if self.grids2[E_grid_x1-k, E_grid_y1].electrode_index < 0:
                                        self.grid_set_electrode(self.grids2, E_grid_x1-k, E_grid_y1+1, self.num_electrode, self.grids2[E_grid_x1-k][E_grid_y1+1].real_x, y1)
                                    # internal 0,0
                                    else:
                                        self.grid_conflict(self.grids2, E_grid_x1-k, E_grid_y1+1)
                                        # self.grid_set_electrode(self.grids2, E_grid_x1-k, E_grid_y1, self.num_electrode, self.grids2[E_grid_x1-k][E_grid_y1].real_x, y1)
                            ## | up
                            elif ang == 360:
                                for k in range(E_grid_y1 - (E_grid_y2 + 1) + 1):
                                    if self.grid_is_available(self.grids2, E_grid_x1, E_grid_y1-k, self.num_electrode):
                                        # if self.grids2[E_grid_x1+1, E_grid_y1-k].electrode_index < 0:
                                        self.grid_set_electrode(self.grids2, E_grid_x1, E_grid_y1-k, self.num_electrode, x1, self.grids2[E_grid_x1][E_grid_y1-k].real_y)
                                    # internal 1,0
                                    else:
                                        self.grid_conflict(self.grids2, E_grid_x1, E_grid_y1-k)
                                            # self.grid_set_electrode(self.grids2, E_grid_x1+1, E_grid_y1-k, self.num_electrode, x1, self.grids2[E_grid_x1+1][E_grid_y1-k].real_y)
                    self.electrodes[-1].boundary_U=boundary_U
                    self.electrodes[-1].boundary_D=boundary_D
                    self.electrodes[-1].boundary_L=boundary_L
                    self.electrodes[-1].boundary_R=boundary_R
            self.num_electrode+=1

    def set_grid_by_electrode_edge_internal2(self, shape, shape_scope):
        num_electrode = 0
        for electrode in self.list_electrodes:
            for i in range (len(shape)):
                if electrode[2] == shape[i]:
                    true_x = electrode[1]
                    true_y = electrode[0]
                    # new_electrode = Electrode(true_x, true_y, i, num_electrode)
                    electrode_shape_path = shape_scope[i]
                    for j in range(len(electrode_shape_path)-1):
                        x1 = true_x+electrode_shape_path[j][0]
                        y1 = true_y+electrode_shape_path[j][1]
                        x2 = true_x+electrode_shape_path[j+1][0]
                        y2 = true_y+electrode_shape_path[j+1][1]
                        E_grid_x1 = (x1-self.block2_shift[0]) // self.Tile_Unit
                        E_grid_x2 = (x2-self.block2_shift[0]) // self.Tile_Unit
                        E_grid_y1 = (y1-self.block2_shift[1]) // self.Tile_Unit
                        E_grid_y2 = (y2-self.block2_shift[1]) // self.Tile_Unit

                        ang = self.clockwise_angle([0, -1], [x2-x1, y2-y1])

                        ######### 直線
                        if ang % 90 == 0:
                            ## ->
                            if ang == 90:
                                for k in range(E_grid_x2 - (E_grid_x1 + 1) + 1):
                                    self.grid_set_electrode(self.grids4, E_grid_x1+1+k, E_grid_y1+1, num_electrode, self.grids4[E_grid_x1+k][E_grid_y1].real_x, y1)
                            # ## | down
                            if ang == 180:
                                for k in range(E_grid_y2 - (E_grid_y1 + 1) + 1):
                                    self.grid_set_electrode(self.grids4, E_grid_x1, E_grid_y1+1+k, num_electrode, x1, self.grids4[E_grid_x1][E_grid_y1+k].real_y)
                            ## <-
                            elif ang == 270:
                                for k in range(E_grid_x1 - E_grid_x2):
                                    self.grid_set_electrode(self.grids4, E_grid_x1-k, E_grid_y1, num_electrode, self.grids4[E_grid_x1-k][E_grid_y1].real_x, y1)
                            ## | up
                            elif ang == 360:
                                for k in range(E_grid_y1 - (E_grid_y2 + 1) + 1):
                                    self.grid_set_electrode(self.grids4, E_grid_x1+1, E_grid_y1-k, num_electrode, x1, self.grids4[E_grid_x1][E_grid_y1-k].real_y)
                    for j in range(len(electrode_shape_path)-1):
                        x1 = true_x+electrode_shape_path[j][0]
                        y1 = true_y+electrode_shape_path[j][1]
                        x2 = true_x+electrode_shape_path[j+1][0]
                        y2 = true_y+electrode_shape_path[j+1][1]
                        E_grid_x1 = (x1-self.block2_shift[0]) // self.Tile_Unit
                        E_grid_x2 = (x2-self.block2_shift[0]) // self.Tile_Unit
                        E_grid_y1 = (y1-self.block2_shift[1]) // self.Tile_Unit
                        E_grid_y2 = (y2-self.block2_shift[1]) // self.Tile_Unit

                        ang = self.clockwise_angle([0, -1], [x2-x1, y2-y1])
                        if ang % 90 != 0:
                            if x1>x2:
                                # |
                                #  \ _
                                if y1>y2:
                                    point = [(x1 + x2) / 2, (y1 + y2) / 2]
                                    E_grid_x = (point[0] - self.block2_shift[0]) // self.Tile_Unit
                                    E_grid_y = (point[1] - self.block2_shift[1]) // self.Tile_Unit
                                    in_x = int(E_grid_x+1)
                                    in_y = int(E_grid_y)
                                    self.grid_set_electrode(self.grids4, in_x, in_y, self.num_electrode, point[0], point[1])
                                #  |
                                # /
                                else:
                                    point = [(x1 + x2) / 2, (y1 + y2) / 2]
                                    E_grid_x = (point[0] - self.block2_shift[0]) // self.Tile_Unit
                                    E_grid_y = (point[1] - self.block2_shift[1]) // self.Tile_Unit
                                    in_x = int(E_grid_x)
                                    in_y = int(E_grid_y)
                                    self.grid_set_electrode(self.grids4, in_x, in_y, self.num_electrode, point[0], point[1])
                            elif x1<x2:
                                # \
                                #  |
                                if y1<y2:
                                    point = [(x1 + x2) / 2, (y1 + y2) / 2]
                                    E_grid_x = (point[0] - self.block2_shift[0]) // self.Tile_Unit
                                    E_grid_y = (point[1] - self.block2_shift[1]) // self.Tile_Unit
                                    in_x = int(E_grid_x)
                                    in_y = int(E_grid_y+1)
                                    self.grid_set_electrode(self.grids4, in_x, in_y, self.num_electrode, point[0], point[1])
                                #  /
                                # |
                                else:
                                    point = [(x1 + x2) / 2, (y1 + y2) / 2]
                                    E_grid_x = (point[0] - self.block2_shift[0]) // self.Tile_Unit
                                    E_grid_y = (point[1] - self.block2_shift[1]) // self.Tile_Unit
                                    in_x = int(E_grid_x+1)
                                    in_y = int(E_grid_y+1)
                                    self.grid_set_electrode(self.grids4, in_x, in_y, self.num_electrode, point[0], point[1])
            num_electrode+=1

    def set_grid_by_electrode_edge_opt2(self, shape, shape_scope):
        for electrode in self.list_electrodes:
            for i in range (len(shape)):
                if electrode[2] == shape[i]:
                    true_x = electrode[1]
                    true_y = electrode[0]
                    new_electrode = Electrode(true_x, true_y, i, self.num_electrode)
                    # print(new_electrode.to_dict())
                    self.electrodes.append(new_electrode)
                    boundary_U=true_y
                    boundary_D=true_y
                    boundary_L=true_x
                    boundary_R=true_x
                    electrode_shape_path = shape_scope[i]
                    for j in range(len(electrode_shape_path)-1):
                        x1 = true_x+electrode_shape_path[j][0]
                        y1 = true_y+electrode_shape_path[j][1]
                        x2 = true_x+electrode_shape_path[j+1][0]
                        y2 = true_y+electrode_shape_path[j+1][1]
                        E_grid_x1 = (x1-self.block2_shift[0]) // self.Tile_Unit
                        E_grid_x2 = (x2-self.block2_shift[0]) // self.Tile_Unit
                        E_grid_y1 = (y1-self.block2_shift[1]) // self.Tile_Unit
                        E_grid_y2 = (y2-self.block2_shift[1]) // self.Tile_Unit

                        # print('grid:', E_grid_x1, E_grid_y1, E_grid_x2, E_grid_y2)
                        # print('addr:', x1, y1, x2, y2)
                        if x1>boundary_R:
                            boundary_R=x1
                        if x1<boundary_L:
                            boundary_L=x1
                        if y1<boundary_U:
                            boundary_U=y1
                        if y1>boundary_D:
                            boundary_D=y1


                        ang = self.clockwise_angle([0, -1], [x2-x1, y2-y1])
                        deg = Degree.getdegree(x2, y2, x1, y1)
                        # print(ang, deg)

                        ######### 有角度
                        if ang % 90 != 0:
                            if x1>x2:
                                # |
                                #  \ _
                                if y1>y2:
                                    point = [(x1 + x2) / 2, (y1 + y2) / 2]
                                    E_grid_x = (point[0] - self.block2_shift[0]) // self.Tile_Unit
                                    E_grid_y = (point[1] - self.block2_shift[1]) // self.Tile_Unit
                                    ex_x = int(E_grid_x)
                                    ex_y = int(E_grid_y+1)
                                    in_x = int(E_grid_x+1)
                                    in_y = int(E_grid_y)
                                    if self.grid_is_available(self.grids2, ex_x, ex_y, self.num_electrode):
                                        self.grid_set_electrode(self.grids2, ex_x, ex_y, self.num_electrode, point[0], point[1])
                                        self.grids2[ex_x][ex_y].inner_grid = self.grids4[in_x][in_y]
                                    # internal 1,0
                                    else:
                                        self.grid_conflict(self.grids2, ex_x, ex_y)
                                        self.grids2[in_x][in_y] = self.grids4[in_x][in_y]
                                        self.grid_set_electrode(self.grids2, in_x, in_y, self.num_electrode, self.grids4[in_x][in_y].electrode_x, self.grids4[in_x][in_y].electrode_y)
                                #  |
                                # /
                                else:
                                    point = [(x1 + x2) / 2, (y1 + y2) / 2]
                                    E_grid_x = (point[0] - self.block2_shift[0]) // self.Tile_Unit
                                    E_grid_y = (point[1] - self.block2_shift[1]) // self.Tile_Unit
                                    ex_x = int(E_grid_x+1)
                                    ex_y = int(E_grid_y+1)
                                    in_x = int(E_grid_x)
                                    in_y = int(E_grid_y)
                                    if self.grid_is_available(self.grids2, ex_x, ex_y, self.num_electrode):
                                        self.grid_set_electrode(self.grids2, ex_x, ex_y, self.num_electrode, point[0], point[1])
                                        self.grids2[ex_x][ex_y].inner_grid = self.grids4[in_x][in_y]
                                    else:
                                        self.grid_conflict(self.grids2, ex_x, ex_y)
                                        self.grid_set_electrode(self.grids2, in_x, in_y, self.num_electrode, self.grids4[in_x][in_y].electrode_x, self.grids4[in_x][in_y].electrode_y)
                            elif x1<x2:
                                # \
                                #  |
                                if y1<y2:
                                    point = [(x1 + x2) / 2, (y1 + y2) / 2]
                                    E_grid_x = (point[0] - self.block2_shift[0]) // self.Tile_Unit
                                    E_grid_y = (point[1] - self.block2_shift[1]) // self.Tile_Unit
                                    ex_x = int(E_grid_x+1)
                                    ex_y = int(E_grid_y)
                                    in_x = int(E_grid_x)
                                    in_y = int(E_grid_y+1)
                                    if self.grid_is_available(self.grids2, ex_x, ex_y, self.num_electrode):
                                        self.grid_set_electrode(self.grids2, ex_x, ex_y, self.num_electrode, point[0], point[1])
                                        self.grids2[ex_x][ex_y].inner_grid = self.grids4[in_x][in_y]
                                    else:
                                        self.grid_conflict(self.grids2, ex_x, ex_y)
                                        self.grid_set_electrode(self.grids2, in_x, in_y, self.num_electrode, self.grids4[in_x][in_y].electrode_x, self.grids4[in_x][in_y].electrode_y)
                                #  /
                                # |
                                else:
                                    point = [(x1 + x2) / 2, (y1 + y2) / 2]
                                    E_grid_x = (point[0] - self.block2_shift[0]) // self.Tile_Unit
                                    E_grid_y = (point[1] - self.block2_shift[1]) // self.Tile_Unit
                                    ex_x = int(E_grid_x)
                                    ex_y = int(E_grid_y)
                                    in_x = int(E_grid_x+1)
                                    in_y = int(E_grid_y+1)
                                    if self.grid_is_available(self.grids2, ex_x, ex_y, self.num_electrode):
                                        self.grid_set_electrode(self.grids2, ex_x, ex_y, self.num_electrode, point[0], point[1])
                                        self.grids2[ex_x][ex_y].inner_grid = self.grids4[in_x][in_y]
                                    else:
                                        self.grid_conflict(self.grids2, ex_x, ex_y)
                                        self.grid_set_electrode(self.grids2, in_x, in_y, self.num_electrode, self.grids4[in_x][in_y].electrode_x, self.grids4[in_x][in_y].electrode_y)
                        # check_corner=0
                        ######### 直線
                        else:
                            ## ->
                            if ang == 90:
                                for k in range(E_grid_x2 - (E_grid_x1) + 1):
                                    # if self.grids4[E_grid_x1+1+k][E_grid_y1].electrode_index < 0:
                                    if self.grid_is_available(self.grids2, E_grid_x1+1+k, E_grid_y1, self.num_electrode):
                                            # if self.grids2[E_grid_x1+1+k][E_grid_y1+1].electrode_index < 0:
                                        self.grid_set_electrode(self.grids2, E_grid_x1+1+k, E_grid_y1, self.num_electrode, self.grids2[E_grid_x1+1+k][E_grid_y1].real_x, y1)
                                    # internal 1,1
                                    else:
                                        self.grid_conflict(self.grids2, E_grid_x1+1+k, E_grid_y1)
                                        # self.grid_set_electrode(self.grids2, E_grid_x1+1+k, E_grid_y1+1, self.num_electrode, self.grids2[E_grid_x1+1+k][E_grid_y1+1].real_x, y1)
                            ## | down
                            elif ang == 180:
                                for k in range(E_grid_y2 - (E_grid_y1 + 1)):
                                    if self.grid_is_available(self.grids2, E_grid_x1+1, E_grid_y1+1+k, self.num_electrode):
                                        # if self.grids2[E_grid_x1, E_grid_y1+1+k].electrode_index < 0:
                                        self.grid_set_electrode(self.grids2, E_grid_x1+1, E_grid_y1+1+k, self.num_electrode, x1, self.grids2[E_grid_x1+1][E_grid_y1+1+k].real_y)
                                    # internal 0,1
                                    else:
                                        self.grid_conflict(self.grids2, E_grid_x1+1, E_grid_y1+1+k)
                                        # self.grid_set_electrode(self.grids2, E_grid_x1, E_grid_y1+1+k, self.num_electrode, x1, self.grids2[E_grid_x1][E_grid_y1+1+k].real_y)
                            ## <-
                            elif ang == 270:
                                for k in range(E_grid_x1 - E_grid_x2):
                                    if self.grid_is_available(self.grids2, E_grid_x1-k, E_grid_y1+1, self.num_electrode):
                                        # if self.grids2[E_grid_x1-k, E_grid_y1].electrode_index < 0:
                                        self.grid_set_electrode(self.grids2, E_grid_x1-k, E_grid_y1+1, self.num_electrode, self.grids2[E_grid_x1-k][E_grid_y1+1].real_x, y1)
                                    # internal 0,0
                                    else:
                                        self.grid_conflict(self.grids2, E_grid_x1-k, E_grid_y1+1)
                                        # self.grid_set_electrode(self.grids2, E_grid_x1-k, E_grid_y1, self.num_electrode, self.grids2[E_grid_x1-k][E_grid_y1].real_x, y1)
                            ## | up
                            elif ang == 360:
                                for k in range(E_grid_y1 - (E_grid_y2 + 1) + 1):
                                    if self.grid_is_available(self.grids2, E_grid_x1, E_grid_y1-k, self.num_electrode):
                                        # if self.grids2[E_grid_x1+1, E_grid_y1-k].electrode_index < 0:
                                        self.grid_set_electrode(self.grids2, E_grid_x1, E_grid_y1-k, self.num_electrode, x1, self.grids2[E_grid_x1][E_grid_y1-k].real_y)
                                    # internal 1,0
                                    else:
                                        self.grid_conflict(self.grids2, E_grid_x1, E_grid_y1-k)
                                            # self.grid_set_electrode(self.grids2, E_grid_x1+1, E_grid_y1-k, self.num_electrode, x1, self.grids2[E_grid_x1+1][E_grid_y1-k].real_y)
                    self.electrodes[-1].boundary_U=boundary_U
                    self.electrodes[-1].boundary_D=boundary_D
                    self.electrodes[-1].boundary_L=boundary_L
                    self.electrodes[-1].boundary_R=boundary_R
            self.num_electrode+=1