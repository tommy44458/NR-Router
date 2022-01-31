import numpy as np
import math
from math import atan2, degrees

from degree import Degree
from grid import Grid
from tile import Tile
from hub import Hub
from electrode import Electrode


class Mesh():
    def __init__(self, control_pad_unit, tile_unit,
                 block1_shift, block2_shift, block3_shift,
                 grids1_length, grids2_length, grids3_length,
                 tiles1_length, tiles2_length, tiles3_length,
                 hubs1_length, hubs1_y, hubs3_length, hubs3_y
                 ):

        self.control_pad_unit = control_pad_unit
        self.tile_unit = tile_unit
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
        self.grids1 = np.empty((grids1_length[0], grids1_length[1]), dtype=Grid)
        self.grids2 = np.empty((grids2_length[0], grids2_length[1]), dtype=Grid)
        self.grids3 = np.empty((grids3_length[0], grids3_length[1]), dtype=Grid)

        # internal
        self.grids4 = np.empty((grids2_length[0], grids2_length[1]), dtype=Grid)

        # Tile
        self.tiles1 = np.empty((tiles1_length[0], tiles1_length[1]), dtype=Tile)
        self.tiles3 = np.empty((tiles3_length[0], tiles3_length[1]), dtype=Tile)

        # Hub
        self.hubs1 = np.empty((hubs1_length), dtype=Hub)
        self.hubs3 = np.empty((hubs3_length), dtype=Hub)

        self.num_electrode = 0

        self.electrodes = []
        self.contactpads = []
        self.contact_line_width = 100
        self.contact_line_width_gap = 20.7

    def set_contactpad_grid(self, contactpad_list: list):
        self.contactpads = contactpad_list
        for contactpad in contactpad_list:
            if contactpad[1] <= 7620:
                grid_x = (contactpad[0] - self.block1_shift[0]) // self.control_pad_unit
                grid_y = (contactpad[1] - self.block1_shift[1]) // self.control_pad_unit
                self.grids1[grid_x][grid_y] = Grid(contactpad[0], contactpad[1], grid_x, grid_y, -1)
            else:
                grid_x = (contactpad[0] - self.block3_shift[0]) // self.control_pad_unit
                grid_y = (contactpad[1] - self.block3_shift[1]) // self.control_pad_unit
                self.grids3[grid_x][grid_y] = Grid(contactpad[0], contactpad[1], grid_x, grid_y, -1)

    def point_distance_line(self, _point, _line_point1, _line_point2):
        point = np.array(_point)
        line_point1 = np.array(_line_point1)
        line_point2 = np.array(_line_point2)
        vec1 = line_point1 - point
        vec2 = line_point2 - point
        distance = np.abs(np.cross(vec1, vec2)) / np.linalg.norm(line_point1-line_point2)
        return distance

    def get_points_lines(self, x1, y1, x2, y2, d):
        d_full = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
        s = d / d_full
        points = []
        # start at s so we don't duplicate (x1, y1)
        a = s
        while a < 1 - s/2:
            x = (1 - a) * x1 + a * x2
            y = (1 - a) * y1 + a * y2
            points.append((int(x), int(y)))
            a += s
        return points

    def cal_distance(self, p1, p2):
        return math.sqrt(math.pow((p2[0] - p1[0]), 2) + math.pow((p2[1] - p1[1]), 2))

    def find_short_grid(self, grid, grid_p, elec_p):
        p1 = [grid[grid_p[0]][grid_p[1]].real_x, grid[grid_p[0]][grid_p[1]].real_y]
        p2 = [grid[grid_p[0]+1][grid_p[1]].real_x, grid[grid_p[0]+1][grid_p[1]].real_y]
        p3 = [grid[grid_p[0]+1][grid_p[1]+1].real_x, grid[grid_p[0]+1][grid_p[1]+1].real_y]
        p4 = [grid[grid_p[0]][grid_p[1]+1].real_x, grid[grid_p[0]][grid_p[1]+1].real_y]
        dis1 = self.cal_distance(elec_p, p1)
        dis2 = self.cal_distance(elec_p, p2)
        dis3 = self.cal_distance(elec_p, p3)
        dis4 = self.cal_distance(elec_p, p4)
        short_p = min([dis1, dis2, dis3, dis4])
        if dis1 == short_p:
            return [grid_p[0], grid_p[1]]
        elif dis2 == short_p:
            return [grid_p[0]+1, grid_p[1]]
        elif dis3 == short_p:
            return [grid_p[0]+1, grid_p[1]+1]
        else:
            return [grid_p[0], grid_p[1]+1]

    def find_short_grid_external(self, grid, grid_p, elec_p, poly_ps):
        grid_ps = []
        p1 = [grid[grid_p[0]][grid_p[1]].real_x, grid[grid_p[0]][grid_p[1]].real_y]
        p2 = [grid[grid_p[0]+1][grid_p[1]].real_x, grid[grid_p[0]+1][grid_p[1]].real_y]
        p3 = [grid[grid_p[0]+1][grid_p[1]+1].real_x, grid[grid_p[0]+1][grid_p[1]+1].real_y]
        p4 = [grid[grid_p[0]][grid_p[1]+1].real_x, grid[grid_p[0]][grid_p[1]+1].real_y]
        if self.is_poi_with_in_poly(p1, poly_ps) is False:
            grid_ps.append([grid_p[0], grid_p[1]])
        if self.is_poi_with_in_poly(p2, poly_ps) is False:
            grid_ps.append([grid_p[0]+1, grid_p[1]])
        if self.is_poi_with_in_poly(p3, poly_ps) is False:
            grid_ps.append([grid_p[0]+1, grid_p[1]+1])
        if self.is_poi_with_in_poly(p4, poly_ps) is False:
            grid_ps.append([grid_p[0], grid_p[1]+1])
        return self.find_short_grid_from_points(grid, grid_ps, elec_p)

    def find_short_grid_internal(self, grid, grid_p, elec_p, poly_ps, conflict_p=[-1, -1]):
        grid_ps = []
        p1 = [grid[grid_p[0]][grid_p[1]].real_x, grid[grid_p[0]][grid_p[1]].real_y]
        p2 = [grid[grid_p[0]+1][grid_p[1]].real_x, grid[grid_p[0]+1][grid_p[1]].real_y]
        p3 = [grid[grid_p[0]+1][grid_p[1]+1].real_x, grid[grid_p[0]+1][grid_p[1]+1].real_y]
        p4 = [grid[grid_p[0]][grid_p[1]+1].real_x, grid[grid_p[0]][grid_p[1]+1].real_y]
        if self.is_poi_with_in_poly(p1, poly_ps):
            # if conflict_p[0] != grid_p[0] and conflict_p[1] != grid_p[1]:
            grid_ps.append([grid_p[0], grid_p[1]])
        if self.is_poi_with_in_poly(p2, poly_ps):
            # if conflict_p[0] != grid_p[0]+1 and conflict_p[1] != grid_p[1]:
            grid_ps.append([grid_p[0]+1, grid_p[1]])
        if self.is_poi_with_in_poly(p3, poly_ps):
            # if conflict_p[0] != grid_p[0]+1 and conflict_p[1] != grid_p[1]+1:
            grid_ps.append([grid_p[0]+1, grid_p[1]+1])
        if self.is_poi_with_in_poly(p4, poly_ps):
            # if conflict_p[0] != grid_p[0] and conflict_p[1] != grid_p[1]+1:
            grid_ps.append([grid_p[0], grid_p[1]+1])
        return self.find_short_grid_from_points(grid, grid_ps, elec_p)

    def find_short_grid_from_points(self, grid, grid_ps, elec_p):
        ps = []
        for grid_p in grid_ps:
            ps.append([grid[grid_p[0]][grid_p[1]].real_x, grid[grid_p[0]][grid_p[1]].real_y])
        dis = []
        for p in ps:
            dis.append(self.cal_distance(elec_p, p))
        if len(dis) > 0:
            short_p = min(dis)
            index = dis.index(short_p)
            return grid_ps[index]
        else:
            return [0, 0]

    def is_ray_intersects_segment(self, poi, s_poi, e_poi):  # [x,y] [lng,lat]
        # 輸入：判斷點，邊起點，邊終點，都是[lng,lat]格式陣列
        if s_poi[1] == e_poi[1]:  # 排除與射線平行、重合，線段首尾端點重合的情況
            return False
        if s_poi[1] > poi[1] and e_poi[1] > poi[1]:  # 線段在射線上邊
            return False
        if s_poi[1] < poi[1] and e_poi[1] < poi[1]:  # 線段在射線下邊
            return False
        if s_poi[1] == poi[1] and e_poi[1] > poi[1]:  # 交點為下端點，對應spoint
            return False
        if e_poi[1] == poi[1] and s_poi[1] > poi[1]:  # 交點為下端點，對應epoint
            return False
        if s_poi[0] < poi[0] and e_poi[1] < poi[1]:  # 線段在射線左邊
            return False

        xseg = e_poi[0]-(e_poi[0]-s_poi[0])*(e_poi[1]-poi[1])/(e_poi[1]-s_poi[1])  # 求交
        if xseg < poi[0]:  # 交點在射線起點的左側
            return False
        return True  # 排除上述情況之後

    def is_poi_with_in_poly(self, poi, poly):
        # 輸入：點，多邊形二維陣列
        # poly=[[x1,y1],[x2,y2],……,[xn,yn],[x1,y1]] 二維陣列
        sinsc = 0  # 交點個數
        for i in range(len(poly)-1):  # [0,len-1]
            s_poi = poly[i]
            e_poi = poly[i+1]
            if self.is_ray_intersects_segment(poi, s_poi, e_poi):
                sinsc += 1  # 有交點就加1

        return True if sinsc % 2 == 1 else False

    def get_short_point(self, _point, _line_point1, _line_point2):
        m = (_line_point1[1]-_line_point2[1])/(_line_point1[0]-_line_point2[0])
        b = (_line_point1[0]*_line_point1[1] - _line_point2[0]*_line_point1[1])/(_line_point1[0]-_line_point2[0])
        x1 = (m*_point[1]+_point[0]-m*b)/((m**2)+1)
        y1 = ((m**2)*_point[1]+m*_point[0]+b)/((m**2)+1)
        return [x1, y1]

    def clockwise_angle(self, v1, v2):
        x1, y1 = v1
        x2, y2 = v2
        dot = x1*x2+y1*y2
        det = x1*y2-y1*x2
        theta = np.arctan2(det, dot)
        theta = theta if theta > 0 else 2*np.pi+theta
        return (theta*180/np.pi)

    def create_block(self, x, y, grids, tiles, block_shift, UNIT_LENGTH):
        for i in range(x):
            for j in range(y):
                if grids[i, j] == None:
                    grids[i, j] = Grid(i*UNIT_LENGTH+block_shift[0], j*UNIT_LENGTH+block_shift[1], i, j, 0)
                if i != x-1 and j != y-1:
                    tiles[i, j] = Tile(i*UNIT_LENGTH+block_shift[0]+UNIT_LENGTH/2, j*UNIT_LENGTH+block_shift[1]+UNIT_LENGTH/2, i, j)

    def create_grid_electrode(self):
        for i in range(self.grids2_length[0]):
            for j in range(self.grids2_length[1]):
                self.grids2[i][j] = Grid(i * self.tile_unit + self.block2_shift[0], j * self.tile_unit + self.block2_shift[1], i, j, 0)
                self.grids4[i][j] = Grid(i * self.tile_unit + self.block2_shift[0], j * self.tile_unit + self.block2_shift[1], i, j, 0)

    def create_grid_pad(self):
        self.create_block(self.grids1_length[0], self.grids1_length[1], self.grids1, self.tiles1, self.block1_shift, self.control_pad_unit)
        self.create_block(self.grids3_length[0], self.grids3_length[1], self.grids3, self.tiles3, self.block3_shift, self.control_pad_unit)
        # pogo pins
        # self.grids1[7,-1].special=True # need lock
        # self.grids1[15,-1].special=True
        # self.grids1[23,-1].special=True
        # self.grids1[31,-1].special=True
        # self.grids3[14,0].special=True
        # self.grids3[22,0].special=True
        # self.grids3[30,0].special=True
        # self.grids3[38,0].special=True

    def create_hub(self):
        for i in range(self.hubs1_length):
            if i % 3 == 0:
                self.hubs1[i] = Hub(real_x=self.grids1[i//3, self.grids1_length[1]-1].real_x, real_y=self.hubs1_y, type=0, hub_index=i)
                self.hubs3[i] = Hub(real_x=self.grids3[i//3, 0].real_x, real_y=self.hubs3_y, type=0, hub_index=i)
            elif i % 3 == 1:
                thub_real_x1 = self.block1_shift[0]+(i//3)*2540+1160+(i % 3-1)*220
                thub_real_x2 = self.block1_shift[0]+(i//3)*2540+1160+((i+1) % 3-1)*220
                thub_grid_x1 = (thub_real_x1-self.block2_shift[0])//self.tile_unit
                thub_grid_x2 = (thub_real_x2-self.block2_shift[0])//self.tile_unit
                thub_tile_x1 = (thub_real_x1-self.block1_shift[0])//self.control_pad_unit
                thub_tile_x2 = (thub_real_x1-self.block1_shift[0])//self.control_pad_unit+1
                if thub_grid_x1 != thub_grid_x2:
                    if abs((thub_grid_x1*self.tile_unit+self.block2_shift[0])-(thub_tile_x1*self.control_pad_unit+self.block1_shift[0])) < 950:
                        thub_grid_x1 += 1
                        thub_grid_x2 += 1
                    elif abs((thub_grid_x2*self.tile_unit+self.block2_shift[0])-(thub_tile_x2*self.control_pad_unit+self.block1_shift[0])) < 950:
                        thub_grid_x1 -= 1
                        thub_grid_x2 -= 1
                if abs((thub_grid_x1*self.tile_unit+self.block2_shift[0])-(thub_tile_x1*self.control_pad_unit+self.block1_shift[0])) < 1000 or abs(((thub_grid_x1+1)*self.tile_unit+self.block2_shift[0])-((thub_tile_x1+1)*self.control_pad_unit+self.block1_shift[0])) < 1000:
                    self.hubs1[i] = Hub(real_x=self.block1_shift[0]+(i//3)*2540+1160+(i % 3-1)*220, real_y=self.hubs1_y, type=1, hub_index=i)
                    self.hubs3[i] = Hub(real_x=self.block1_shift[0]+(i//3)*2540+1160+(i % 3-1)*220, real_y=self.hubs3_y, type=1, hub_index=i)
                    i += 1
                    self.hubs1[i] = Hub(real_x=self.block1_shift[0]+(i//3)*2540+1160+(i % 3-1)*220, real_y=self.hubs1_y, type=1, hub_index=i)
                    self.hubs3[i] = Hub(real_x=self.block1_shift[0]+(i//3)*2540+1160+(i % 3-1)*220, real_y=self.hubs3_y, type=1, hub_index=i)
                else:
                    self.hubs1[i] = Hub(real_x=thub_grid_x1*self.tile_unit+self.block2_shift[0], real_y=self.hubs1_y, type=1, hub_index=i)
                    self.hubs3[i] = Hub(real_x=thub_grid_x1*self.tile_unit+self.block2_shift[0], real_y=self.hubs3_y, type=1, hub_index=i)
                    i += 1
                    self.hubs1[i] = Hub(real_x=(thub_grid_x1+1)*self.tile_unit+self.block2_shift[0], real_y=self.hubs1_y, type=1, hub_index=i)
                    self.hubs3[i] = Hub(real_x=(thub_grid_x1+1)*self.tile_unit+self.block2_shift[0], real_y=self.hubs3_y, type=1, hub_index=i)

    def trian_corner_electrode_index(self, a, b, c):
        if (a != b and b != c and c != a):
            return True
        else:
            return False

    def is_trian_corner(self, i, j):
        if i == 0 or j == 0:
            return 0
        if i == self.grids2_length[0]-1 or j == self.grids2_length[1]-1:
            return 0
        # --
        # |*
        if self.grids2[i-1, j-1].type > 0 and self.grids2[i-1, j].type > 0 and self.grids2[i, j-1].type > 0 and self.grids2[i+1, j+1].type == 0 and self.grids2[i, j+1].type == 0:
            if self.trian_corner_electrode_index(self.grids2[i-1, j-1].electrode_index, self.grids2[i-1, j].electrode_index, self.grids2[i, j-1].electrode_index):
                return 1
        # --
        # *|
        if self.grids2[i, j-1].type > 0 and self.grids2[i+1, j-1].type > 0 and self.grids2[i+1, j].type > 0 and self.grids2[i-1, j+1].type == 0 and self.grids2[i, j+1].type == 0:
            if self.trian_corner_electrode_index(self.grids2[i, j-1].electrode_index, self.grids2[i+1, j-1].electrode_index, self.grids2[i+1, j].electrode_index):
                return 2
        # *|
        # --
        if self.grids2[i+1, j].type > 0 and self.grids2[i+1, j+1].type > 0 and self.grids2[i, j+1].type > 0 and self.grids2[i-1, j-1].type == 0 and self.grids2[i, j-1].type == 0:
            if self.trian_corner_electrode_index(self.grids2[i+1, j].electrode_index, self.grids2[i+1, j+1].electrode_index, self.grids2[i, j+1].electrode_index):
                return 3
        # |*
        # --
        if self.grids2[i-1, j].type > 0 and self.grids2[i-1, j+1].type > 0 and self.grids2[i, j+1].type > 0 and self.grids2[i+1, j-1].type == 0 and self.grids2[i, j-1].type == 0:
            if self.trian_corner_electrode_index(self.grids2[i-1, j].electrode_index, self.grids2[i-1, j+1].electrode_index, self.grids2[i, j+1].electrode_index):
                return 4
        return 0

    # 對電極鄰近的grid建立連線
    def create_neighbor_electrodes(self):
        for i in range(self.grids2_length[0]):
            lock = False
            for j in range(self.grids2_length[1]):
                # if lock==False and self.grids2[i,j].type>0 and self.grids2[i,j+1].type==0 and self.grids2[i,j-1].electrode_index!=self.grids2[i,j].electrode_index :
                #     lock = True
                # elif lock==True and self.grids2[i,j].type>0 and self.grids2[i,j-1].type==0 and self.grids2[i,j+1].electrode_index!=self.grids2[i,j].electrode_index :
                #     lock = False
                # elif lock==True and self.grids2[i,j].type>0 and self.grids2[i,j+1].type==0 and self.next_electrode_index(i,j,self.grids2,self.grids2_length[1])!=self.grids2[i,j].electrode_index :
                #     lock = False
                dir = [0, 0, 0, 0, 0, 0, 0, 0]
                if (self.grids2[i, j].type == 0 and lock == False):
                    # check 9 directions
                    if i == 0:
                        if j == 0:						# O *
                            dir = [0, 0, 0, 0, 1, 0, 1, 1]		# * *

                        elif j == self.grids2_length[1]-1:  # * *
                            dir = [0, 1, 1, 0, 1, 0, 0, 0]		    # O *

                        else:							# * *
                            dir = [0, 1, 1, 0, 1, 0, 1, 1]		# O *
                            # * *
                    elif i == self.grids2_length[0]-1:
                        if j == 0:						# * O
                            dir = [0, 0, 0, 1, 0, 1, 1, 0]		# * *

                        elif j == self.grids2_length[1]-1:  # * *
                            dir = [1, 1, 0, 1, 0, 0, 0, 0]		    # * O

                        else:							# * *
                            dir = [1, 1, 0, 1, 0, 1, 1, 0]		# * O
                            # * *
                    else:
                        if j == 0:						# * O *
                            dir = [0, 0, 0, 1, 1, 1, 1, 1]		# * * *

                        elif j == self.grids2_length[1]-1:  # * * *
                            dir = [1, 1, 1, 1, 1, 0, 0, 0]		# * O *

                        else:							# * * *
                            dir = [1, 1, 1, 1, 1, 1, 1, 1]		# * O *
                            # * * *
                    self._create_neighbor_electrodes(i, j, dir)
                # else:
                trian_corner = self.is_trian_corner(i, j)
                if trian_corner > 0:
                    self.grids2[i][j].electrode_index = -1
                    self.grids2[i][j].type = 0
                    self.grids2[i][j].electrode_x = 0
                    self.grids2[i][j].electrode_y = 0
                    if trian_corner == 1:
                        self.grids2[i][j].neighbor_electrode.append([self.grids2[i-1, j-1].electrode_index, 0, -1, -1, self.tile_unit*2-100, True])
                    if trian_corner == 2:
                        self.grids2[i][j].neighbor_electrode.append([self.grids2[i+1, j-1].electrode_index, 2, 1, -1, self.tile_unit*2-100, True])
                    if trian_corner == 3:
                        self.grids2[i][j].neighbor_electrode.append([self.grids2[i+1, j+1].electrode_index, 7, 1, 1, self.tile_unit*2-100, True])
                    if trian_corner == 4:
                        self.grids2[i][j].neighbor_electrode.append([self.grids2[i-1, j+1].electrode_index, 5, -1, 1, self.tile_unit*2-100, True])

    def _create_neighbor_electrodes(self, i, j, dir):
        # 012
        # 3 4
        # 567
        # if self.grids2[i][j].conflict is False:
        if dir[0] == 1 and self.grids2[i-1][j-1].type > 0:
            if self.grids2[i][j-1].type > 0 and self.grids2[i-1][j].type > 0:
                self.grids2[i][j].neighbor_electrode.append([self.grids2[i-1][j-1].electrode_index, 0, -
                                                            1, -1, self.tile_unit*2-100, False])  # index dir self.grids2[i-1][j-1]
        if dir[1] == 1 and self.grids2[i][j-1].type > 0:
            self.grids2[i][j].neighbor_electrode.append([self.grids2[i][j-1].electrode_index, 1, 0, -1, self.tile_unit, False])
        if dir[2] == 1 and self.grids2[i+1][j-1].type > 0:
            if self.grids2[i][j-1].type > 0 and self.grids2[i+1][j].type > 0:
                self.grids2[i][j].neighbor_electrode.append([self.grids2[i+1][j-1].electrode_index, 2, 1, -1, self.tile_unit*2-100, False])
        if dir[3] == 1 and self.grids2[i-1][j].type > 0:
            self.grids2[i][j].neighbor_electrode.append([self.grids2[i-1][j].electrode_index, 3, -1, 0, self.tile_unit, False])
        if dir[4] == 1 and self.grids2[i+1][j].type > 0:
            self.grids2[i][j].neighbor_electrode.append([self.grids2[i+1][j].electrode_index, 4, 1, 0, self.tile_unit, False])
        if dir[5] == 1 and self.grids2[i-1][j+1].type > 0:
            if self.grids2[i-1][j].type > 0 and self.grids2[i][j+1].type > 0:
                self.grids2[i][j].neighbor_electrode.append([self.grids2[i-1][j+1].electrode_index, 5, -1, 1, self.tile_unit*2-100, False])
        if dir[6] == 1 and self.grids2[i][j+1].type > 0:
            self.grids2[i][j].neighbor_electrode.append([self.grids2[i][j+1].electrode_index, 6, 0, 1, self.tile_unit, False])
        if dir[7] == 1 and self.grids2[i+1][j+1].type > 0:
            if self.grids2[i+1][j].type > 0 and self.grids2[i][j+1].type > 0:
                self.grids2[i][j].neighbor_electrode.append([self.grids2[i+1][j+1].electrode_index, 7, 1, 1, self.tile_unit*2-100, False])
        # else:
        #     if dir[0]==1 and self.grids2[i-1][j-1].type>0 and self.grids2[i-1][j-1].corner:
        #         self.grids2[i][j].neighbor_electrode.append([self.grids2[i-1][j-1].electrode_index,0,-1,-1, self.tile_unit*2-1, True]) # index dir self.grids2[i-1][j-1]
        #     if dir[1]==1 and self.grids2[i][j-1].type>0 and self.grids2[i][j-1].corner:
        #         self.grids2[i][j].neighbor_electrode.append([self.grids2[i][j-1].electrode_index,1,0,-1, self.tile_unit, False])
        #     if dir[2]==1 and self.grids2[i+1][j-1].type>0 and self.grids2[i+1][j-1].corner:
        #         self.grids2[i][j].neighbor_electrode.append([self.grids2[i+1][j-1].electrode_index,2,1,-1, self.tile_unit*2-1, True])
        #     if dir[3]==1 and self.grids2[i-1][j].type>0 and self.grids2[i-1][j].corner:
        #         self.grids2[i][j].neighbor_electrode.append([self.grids2[i-1][j].electrode_index,3,-1,0, self.tile_unit, False])
        #     if dir[4]==1 and self.grids2[i+1][j].type>0 and self.grids2[i+1][j].corner:
        #         self.grids2[i][j].neighbor_electrode.append([self.grids2[i+1][j].electrode_index,4,1,0, self.tile_unit, False])
        #     if dir[5]==1 and self.grids2[i-1][j+1].type>0 and self.grids2[i-1][j+1].corner:
        #         self.grids2[i][j].neighbor_electrode.append([self.grids2[i-1][j+1].electrode_index,5,-1,1, self.tile_unit*2-1, True])
        #     if dir[6]==1 and self.grids2[i][j+1].type>0 and self.grids2[i][j+1].corner:
        #         self.grids2[i][j].neighbor_electrode.append([self.grids2[i][j+1].electrode_index,6,0,1, self.tile_unit, False])
        #     if dir[7]==1 and self.grids2[i+1][j+1].type>0 and self.grids2[i+1][j+1].corner:
        #         self.grids2[i][j].neighbor_electrode.append([self.grids2[i+1][j+1].electrode_index,7,1,1, self.tile_unit*2-1, True])

    def next_electrode_index(self, x, y, grids, length):
        for i in range(y+1, length):
            if grids[x, i].type > 0:
                return grids[x, i].electrode_index
        return -1

    def set_safe_distance(self):
        for i in range(self.grids2_length[0]):
            for j in range(self.grids2_length[1]):
                if len(self.grids2[i][j].neighbor_electrode) > 0:
                    if i != 0 and len(self.grids2[i-1][j].neighbor_electrode) == 0:
                        self.grids2[i-1][j].safe_distance = 1
                        #dxf.add_circle(center=(grids2[i-1][j].real_x, -grids2[i][j].real_y), radius = 200.0)
                    if i != self.grids2_length[0]-1 and len(self.grids2[i+1][j].neighbor_electrode) == 0:
                        self.grids2[i+1][j].safe_distance = 1
                        #dxf.add_circle(center=(grids2[i+1][j].real_x, -grids2[i][j].real_y), radius = 200.0)

                    #dxf.add_circle(center=(grids2[i][j].real_x, -grids2[i][j].real_y), radius = 50.0)

                # if grids2[i][j].type>0:#check electrode
                #	dxf.add_circle(center=(grids2[i][j].real_x, -grids2[i][j].real_y), radius = 100.0)

        for i in range(self.grids2_length[0]):
            for j in range(self.grids2_length[1]):
                if self.grids2[i][j].safe_distance == 1:
                    if i != 0 and len(self.grids2[i-1][j].neighbor_electrode) == 0 and self.grids2[i-1][j].safe_distance == 0:
                        self.grids2[i-1][j].safe_distance2 = 1
                        #dxf.add_circle(center=(grids2[i-1][j].real_x, -grids2[i][j].real_y), radius = 200.0)
                    if i != self.grids2_length[0]-1 and len(self.grids2[i+1][j].neighbor_electrode) == 0 and self.grids2[i+1][j].safe_distance == 0:
                        self.grids2[i+1][j].safe_distance2 = 1
                        #dxf.add_circle(center=(grids2[i+1][j].real_x, -grids2[i][j].real_y), radius = 200.0)

    # 對所有不被電極覆蓋的grid建立連線
    def create_grids_connection(self):
        for i in range(self.grids2_length[0]):
            for j in range(self.grids2_length[1]):
                dir = [0, 0, 0, 0, 0, 0, 0, 0]
                if self.grids2[i, j].type == 0:
                    # check 9 directions
                    if i == 0:
                        if j == 0:						# O *
                            dir = [0, 0, 0, 0, 1, 0, 1, 1]		# * *

                        elif j == self.grids2_length[1]-1:  # * *
                            dir = [0, 1, 1, 0, 1, 0, 0, 0]		# O *

                        else:							# * *
                            dir = [0, 1, 1, 0, 1, 0, 1, 1]		# O *
                            # * *
                    elif i == self.grids2_length[0]-1:
                        if j == 0:						# * O
                            dir = [0, 0, 0, 1, 0, 1, 1, 0]		# * *

                        elif j == self.grids2_length[1]-1:  # * *
                            dir = [1, 1, 0, 1, 0, 0, 0, 0]		# * O

                        else:							# * *
                            dir = [1, 1, 0, 1, 0, 1, 1, 0]		# * O
                            # * *
                    else:
                        if j == 0:						# * O *
                            dir = [0, 0, 0, 1, 1, 1, 1, 1]		# * * *

                        elif j == self.grids2_length[1]-1:  # * * *
                            dir = [1, 1, 1, 1, 1, 0, 0, 0]		# * O *

                        else:							# * * *
                            dir = [1, 1, 1, 1, 1, 1, 1, 1]		# * O *
                            # * * *
                    self._create_grids_connection(self.grids2, i, j, dir)
                trian_corner = self.is_trian_corner(i, j)
                if trian_corner > 0:
                    # self.grids2[i][j].electrode_index = -1
                    # self.grids2[i][j].type = 0
                    # self.grids2[i][j].electrode_x = 0
                    # self.grids2[i][j].electrode_y = 0
                    self.grids2[i][j].neighbor = []
                    if trian_corner == 1:
                        self.grids2[i][j].neighbor.append([self.grids2[i-1, j-1], 1, self.tile_unit*2-100])
                        self.grids2[i][j].neighbor.append([self.grids2[i+1, j+1], 1, self.tile_unit*2-100])
                    if trian_corner == 2:
                        self.grids2[i][j].neighbor.append([self.grids2[i+1, j-1], 1, self.tile_unit*2-100])
                        self.grids2[i][j].neighbor.append([self.grids2[i-1, j+1], 1, self.tile_unit*2-100])
                    if trian_corner == 3:
                        self.grids2[i][j].neighbor.append([self.grids2[i+1, j+1], 1, self.tile_unit*2-100])
                        self.grids2[i][j].neighbor.append([self.grids2[i-1, j-1], 1, self.tile_unit*2-100])
                    if trian_corner == 4:
                        self.grids2[i][j].neighbor.append([self.grids2[i-1, j+1], 1, self.tile_unit*2-100])
                        self.grids2[i][j].neighbor.append([self.grids2[i+1, j-1], 1, self.tile_unit*2-100])

    # create grids connection
    def _create_grids_connection(self, grids, x, y, dir):
        # if grids[x][y].conflict is False:
        if dir[0] == 1:
            if grids[x-1][y-1].type == 0 and len(grids[x-1][y-1].neighbor_electrode) == 0 and grids[x-1][y-1].safe_distance == 0 and grids[x-1][y-1].safe_distance2 == 0 or (len(grids[x][y].neighbor_electrode) > 0 and grids[x-1][y-1].safe_distance == 1) or (grids[x-1][y-1].safe_distance2 == 1 and grids[x][y].safe_distance == 1):
                grids[x][y].neighbor.append([grids[x-1][y-1], 1, self.tile_unit*2-100])  # self.tile_unit*math.sqrt(2)
        if dir[1] == 1:
            if grids[x][y-1].type == 0 and len(grids[x][y-1].neighbor_electrode) == 0 and grids[x][y-1].safe_distance == 0 and grids[x][y-1].safe_distance2 == 0 or (len(grids[x][y].neighbor_electrode) > 0 and grids[x][y-1].safe_distance == 1) or (grids[x][y-1].safe_distance2 == 1 and grids[x][y].safe_distance == 1):
                grids[x][y].neighbor.append([grids[x][y-1], 1, self.tile_unit])  # max(0,self.tile_unit-grids[x][y-1].cost*500)])
        if dir[2] == 1:
            if grids[x+1][y-1].type == 0 and len(grids[x+1][y-1].neighbor_electrode) == 0 and grids[x+1][y-1].safe_distance == 0 and grids[x+1][y-1].safe_distance2 == 0 or (len(grids[x][y].neighbor_electrode) > 0 and grids[x+1][y-1].safe_distance == 1) or (grids[x+1][y-1].safe_distance2 == 1 and grids[x][y].safe_distance == 1):
                grids[x][y].neighbor.append([grids[x+1][y-1], 1, self.tile_unit*2-100])
        if dir[3] == 1:
            if grids[x-1][y].type == 0 and len(grids[x-1][y].neighbor_electrode) == 0 and grids[x-1][y].safe_distance == 0 and grids[x-1][y].safe_distance2 == 0 or (len(grids[x][y].neighbor_electrode) > 0 and grids[x-1][y].safe_distance == 1) or (grids[x-1][y].safe_distance2 == 1 and grids[x][y].safe_distance == 1):
                grids[x][y].neighbor.append([grids[x-1][y], 1, self.tile_unit])
        if dir[4] == 1:
            if grids[x+1][y].type == 0 and len(grids[x+1][y].neighbor_electrode) == 0 and grids[x+1][y].safe_distance == 0 and grids[x+1][y].safe_distance2 == 0 or (len(grids[x][y].neighbor_electrode) > 0 and grids[x+1][y].safe_distance == 1) or (grids[x+1][y].safe_distance2 == 1 and grids[x][y].safe_distance == 1):
                grids[x][y].neighbor.append([grids[x+1][y], 1, self.tile_unit])
        if dir[5] == 1:
            if grids[x-1][y+1].type == 0 and len(grids[x-1][y+1].neighbor_electrode) == 0 and grids[x-1][y+1].safe_distance == 0 and grids[x-1][y+1].safe_distance2 == 0 or (len(grids[x][y].neighbor_electrode) > 0 and grids[x-1][y+1].safe_distance == 1) or (grids[x-1][y+1].safe_distance2 == 1 and grids[x][y].safe_distance == 1):
                grids[x][y].neighbor.append([grids[x-1][y+1], 1, self.tile_unit*2-100])
        if dir[6] == 1:
            if grids[x][y+1].type == 0 and len(grids[x][y+1].neighbor_electrode) == 0 and grids[x][y+1].safe_distance == 0 and grids[x][y+1].safe_distance2 == 0 or (len(grids[x][y].neighbor_electrode) > 0 and grids[x][y+1].safe_distance == 1) or (grids[x][y+1].safe_distance2 == 1 and grids[x][y].safe_distance == 1):
                grids[x][y].neighbor.append([grids[x][y+1], 1, self.tile_unit])  # max(0,self.tile_unit-grids[x][y+1].cost*500)])
        if dir[7] == 1:
            if grids[x+1][y+1].type == 0 and len(grids[x+1][y+1].neighbor_electrode) == 0 and grids[x+1][y+1].safe_distance == 0 and grids[x+1][y+1].safe_distance2 == 0 or (len(grids[x][y].neighbor_electrode) > 0 and grids[x+1][y+1].safe_distance == 1) or (grids[x+1][y+1].safe_distance2 == 1 and grids[x][y].safe_distance == 1):
                grids[x][y].neighbor.append([grids[x+1][y+1], 1, self.tile_unit*2-100])
        # else:
        #     if dir[0]==1:
        #         if grids[x-1][y-1].type==0 and len(grids[x-1][y-1].neighbor_electrode)==0 and grids[x-1][y-1].safe_distance==0 and grids[x-1][y-1].safe_distance2==0:
        #             grids[x][y].neighbor.append([grids[x-1][y-1], 1, self.tile_unit*math.sqrt(2)-50])
        #         if grids[x-1][y-1].corner:
        #             grids[x][y].neighbor.append([grids[x-1][y-1], 1, self.tile_unit*math.sqrt(2)-50])
        #     if dir[1]==1:
        #         if grids[x][y-1].type==0 and len(grids[x][y-1].neighbor_electrode)==0 and grids[x][y-1].safe_distance==0 and grids[x][y-1].safe_distance2==0:
        #             grids[x][y].neighbor.append([grids[x][y-1], 1, self.tile_unit-100])# max(0,self.tile_unit-grids[x][y-1].cost*500)])
        #         if grids[x][y-1].corner:
        #             grids[x][y].neighbor.append([grids[x][y-1], 1, self.tile_unit-100])
        #     if dir[2]==1:
        #         if grids[x+1][y-1].type==0 and len(grids[x+1][y-1].neighbor_electrode)==0 and grids[x+1][y-1].safe_distance==0 and grids[x+1][y-1].safe_distance2==0 or (len(grids[x][y].neighbor_electrode)>0 and grids[x+1][y-1].corner and grids[x+1][y-1].safe_distance==1) or (grids[x+1][y-1].safe_distance2==1 and grids[x][y].safe_distance==1):
        #             grids[x][y].neighbor.append([grids[x+1][y-1], 1, self.tile_unit*math.sqrt(2)-50])
        #         if grids[x+1][y-1].corner:
        #             grids[x][y].neighbor.append([grids[x+1][y-1], 1, self.tile_unit*math.sqrt(2)-50])
        #     if dir[3]==1:
        #         if grids[x-1][y].type==0 and len(grids[x-1][y].neighbor_electrode)==0 and grids[x-1][y].safe_distance==0 and grids[x-1][y].safe_distance2==0:
        #             grids[x][y].neighbor.append([grids[x-1][y], 1, self.tile_unit])
        #         if grids[x-1][y].corner:
        #             grids[x][y].neighbor.append([grids[x-1][y], 1, self.tile_unit*math.sqrt(2)-50])
        #     if dir[4]==1:
        #         if grids[x+1][y].type==0 and len(grids[x+1][y].neighbor_electrode)==0 and grids[x+1][y].safe_distance==0 and grids[x+1][y].safe_distance2==0:
        #             grids[x][y].neighbor.append([grids[x+1][y], 1, self.tile_unit])
        #         if grids[x+1][y].corner:
        #             grids[x][y].neighbor.append([grids[x+1][y], 1, self.tile_unit])
        #     if dir[5]==1:
        #         if grids[x-1][y+1].type==0 and len(grids[x-1][y+1].neighbor_electrode)==0 and grids[x-1][y+1].safe_distance==0 and grids[x-1][y+1].safe_distance2==0:
        #             grids[x][y].neighbor.append([grids[x-1][y+1], 1, self.tile_unit*math.sqrt(2)-50])
        #         if grids[x-1][y+1].corner:
        #             grids[x][y].neighbor.append([grids[x-1][y+1], 1, self.tile_unit*math.sqrt(2)-50])
        #     if dir[6]==1:
        #         if grids[x][y+1].type==0 and len(grids[x][y+1].neighbor_electrode)==0 and grids[x][y+1].safe_distance==0 and grids[x][y+1].safe_distance2==0:
        #             grids[x][y].neighbor.append([grids[x][y+1], 1, self.tile_unit-100])# max(0,self.tile_unit-grids[x][y+1].cost*500)])
        #         if grids[x][y+1].corner:
        #             grids[x][y].neighbor.append([grids[x][y+1], 1, self.tile_unit-100])
        #     if dir[7]==1:
        #         if grids[x+1][y+1].type==0 and len(grids[x+1][y+1].neighbor_electrode)==0 and grids[x+1][y+1].safe_distance==0  and grids[x+1][y+1].safe_distance2==0 or (len(grids[x][y].neighbor_electrode)>0 and grids[x+1][y+1].corner and grids[x+1][y+1].safe_distance==1):
        #             grids[x][y].neighbor.append([grids[x+1][y+1], 1, self.tile_unit*math.sqrt(2)-50])
        #         if grids[x+1][y+1].corner:
        #             grids[x][y].neighbor.append([grids[x+1][y+1], 1, self.tile_unit*math.sqrt(2)-50])

    def create_tiles_connection(self, tile_length, grids, tiles, block):
        for i in range(tile_length[0]):
            for j in range(tile_length[1]):
                # add corner
                capacity = [8, 8, 8, 8]  # u, l, d, r
                for k in (i, i+1):
                    for l in (j, j+1):
                        # contact pads
                        if grids[k, l].type == -1:
                            if grids[k, l].special == False:
                                if block == 1 and l == tile_length[1]:
                                    pass
                                elif block == 3 and l == 0:
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
                    tiles[i, j].neighbor.append([tiles[i-1, j], capacity[0]])  # left
                if i != tile_length[0]-1:
                    tiles[i, j].neighbor.append([tiles[i+1, j], capacity[2]])  # right
                if j != 0:
                    tiles[i, j].neighbor.append([tiles[i, j-1], capacity[1]])  # top
                if j != tile_length[1]-1:
                    tiles[i, j].neighbor.append([tiles[i, j+1], capacity[3]])  # down

    def create_hubs_connection(self, hubs, hubs_length, block2_n, tile_n, grids, tiles):
        for i in range(hubs_length):
            left = int((hubs[i].real_x-self.block1_shift[0]) // self.tile_unit)
            right = int((hubs[i].real_x-self.block1_shift[0]) // self.tile_unit+1)
            if i % 3 == 0:
                if (hubs[i].real_x - self.grids2[left][block2_n].real_x) > (self.tile_unit/2):
                    near = right
                else:
                    near = left
                if grids[i//3][tile_n].special == False:
                    self.grids2[near][block2_n].neighbor.append([hubs[i], 1, 1944])
                    hubs[i].neighbor.append([grids[i//3][tile_n], 1, 1944])
            elif i % 3 == 1:
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
        # if self.grids4[x, y].electrode_index < 0:
        # if grid[x, y].conflict is False:
        #     if grid[x, y].inner_grid is not None:
        #         self.grid_set_electrode(grid, grid[x, y].inner_grid.grid_x, grid[x, y].inner_grid.grid_y, grid[x, y].inner_grid.electrode_index, grid[x, y].inner_grid.electrode_x, grid[x, y].inner_grid.electrode_y)
        grid[x, y].conflict = True
        grid[x, y].electrode_index = -1
        grid[x, y].type = 0
        grid[x, y].electrode_x = 0
        grid[x, y].electrode_y = 0
        # grid[x, y].cost = -1
        return False

    def grid_set_electrode(self, grid, x, y, electrode_index, p1, p2, corner=False):
        grid[x, y].electrode_index = electrode_index
        grid[x, y].type += 1
        grid[x, y].electrode_x = p1
        grid[x, y].electrode_y = p2
        grid[x, y].corner = corner

    def set_grid_by_electrode_edge_internal2(self, elec_list, shape_lib):
        for electrode_index, electrode in enumerate(elec_list):
            if electrode[0] in shape_lib:
                true_x = electrode[1]
                true_y = electrode[2]
                electrode_shape_path = shape_lib[electrode[0]]
                for j in range(len(electrode_shape_path)-1):
                    x1 = true_x+electrode_shape_path[j][0]
                    y1 = true_y+electrode_shape_path[j][1]
                    x2 = true_x+electrode_shape_path[j+1][0]
                    y2 = true_y+electrode_shape_path[j+1][1]
                    E_grid_x1 = (x1-self.block2_shift[0]) // self.tile_unit
                    E_grid_x2 = (x2-self.block2_shift[0]) // self.tile_unit
                    E_grid_y1 = (y1-self.block2_shift[1]) // self.tile_unit
                    E_grid_y2 = (y2-self.block2_shift[1]) // self.tile_unit

                    ang = self.clockwise_angle([0, -1], [x2-x1, y2-y1])

                    # 直線
                    if ang % 90 == 0:
                        # ->
                        if ang == 90:
                            for k in range(E_grid_x2 - (E_grid_x1 + 1) + 1):
                                self.grid_set_electrode(self.grids4, E_grid_x1+1+k, E_grid_y1+1, electrode_index,
                                                        self.grids4[E_grid_x1+1+k][E_grid_y1+1].real_x, y1)
                        # ## | down
                        if ang == 180:
                            for k in range(E_grid_y2 - (E_grid_y1 + 1) + 1):
                                self.grid_set_electrode(self.grids4, E_grid_x1, E_grid_y1+1+k, electrode_index,
                                                        x1, self.grids4[E_grid_x1][E_grid_y1+1+k].real_y)
                        # <-
                        elif ang == 270:
                            for k in range(E_grid_x1 - E_grid_x2):
                                self.grid_set_electrode(self.grids4, E_grid_x1-k, E_grid_y1, electrode_index,
                                                        self.grids4[E_grid_x1-k][E_grid_y1].real_x, y1)
                        # | up
                        elif ang == 360:
                            for k in range(E_grid_y1 - (E_grid_y2 + 1) + 1):
                                self.grid_set_electrode(self.grids4, E_grid_x1+1, E_grid_y1-k, electrode_index,
                                                        x1, self.grids4[E_grid_x1+1][E_grid_y1-k].real_y)
                for j in range(len(electrode_shape_path)-1):
                    x1 = true_x+electrode_shape_path[j][0]
                    y1 = true_y+electrode_shape_path[j][1]
                    x2 = true_x+electrode_shape_path[j+1][0]
                    y2 = true_y+electrode_shape_path[j+1][1]
                    E_grid_x1 = (x1-self.block2_shift[0]) // self.tile_unit
                    E_grid_x2 = (x2-self.block2_shift[0]) // self.tile_unit
                    E_grid_y1 = (y1-self.block2_shift[1]) // self.tile_unit
                    E_grid_y2 = (y2-self.block2_shift[1]) // self.tile_unit

                    ang = self.clockwise_angle([0, -1], [x2-x1, y2-y1])
                    if ang % 90 != 0:
                        if x1 > x2:
                            # |
                            #  \ _
                            if y1 > y2:
                                point = [(x1 + x2) / 2, (y1 + y2) / 2]
                                E_grid_x = (point[0] - self.block2_shift[0]) // self.tile_unit
                                E_grid_y = (point[1] - self.block2_shift[1]) // self.tile_unit
                                in_x = int(E_grid_x+1)
                                in_y = int(E_grid_y)
                                self.grid_set_electrode(self.grids4, in_x, in_y, electrode_index, point[0], point[1], True)
                            #  |
                            # /
                            else:
                                point = [(x1 + x2) / 2, (y1 + y2) / 2]
                                E_grid_x = (point[0] - self.block2_shift[0]) // self.tile_unit
                                E_grid_y = (point[1] - self.block2_shift[1]) // self.tile_unit
                                in_x = int(E_grid_x)
                                in_y = int(E_grid_y)
                                self.grid_set_electrode(self.grids4, in_x, in_y, electrode_index, point[0], point[1], True)
                        elif x1 < x2:
                            # \
                            #  |
                            if y1 < y2:
                                point = [(x1 + x2) / 2, (y1 + y2) / 2]
                                E_grid_x = (point[0] - self.block2_shift[0]) // self.tile_unit
                                E_grid_y = (point[1] - self.block2_shift[1]) // self.tile_unit
                                in_x = int(E_grid_x)
                                in_y = int(E_grid_y+1)
                                self.grid_set_electrode(self.grids4, in_x, in_y, electrode_index, point[0], point[1], True)
                            #  /
                            # |
                            else:
                                point = [(x1 + x2) / 2, (y1 + y2) / 2]
                                E_grid_x = (point[0] - self.block2_shift[0]) // self.tile_unit
                                E_grid_y = (point[1] - self.block2_shift[1]) // self.tile_unit
                                in_x = int(E_grid_x+1)
                                in_y = int(E_grid_y+1)
                                self.grid_set_electrode(self.grids4, in_x, in_y, electrode_index, point[0], point[1], True)

    def set_grid_by_electrode_edge_opt2(self, elec_list, shape_lib):
        for electrode_index, electrode in enumerate(elec_list):
            if electrode[0] in shape_lib:
                true_x = electrode[1]
                true_y = electrode[2]
                electrode_shape_path = shape_lib[electrode[0]]
                new_electrode = Electrode(true_x, true_y, electrode[0], electrode_index)

                boundary_U = true_y
                boundary_D = true_y
                boundary_L = true_x
                boundary_R = true_x
                poly_points = []

                for j in range(len(electrode_shape_path)-1):
                    x = true_x+electrode_shape_path[j][0]
                    y = true_y+electrode_shape_path[j][1]
                    poly_points.append([x, y])
                poly_points.append([poly_points[0][0], poly_points[0][1]])

                new_electrode.poly = poly_points
                for j in range(len(electrode_shape_path)-1):
                    x1 = true_x+electrode_shape_path[j][0]
                    y1 = true_y+electrode_shape_path[j][1]
                    x2 = true_x+electrode_shape_path[j+1][0]
                    y2 = true_y+electrode_shape_path[j+1][1]
                    E_grid_x1 = (x1-self.block2_shift[0]) // self.tile_unit
                    E_grid_x2 = (x2-self.block2_shift[0]) // self.tile_unit
                    E_grid_y1 = (y1-self.block2_shift[1]) // self.tile_unit
                    E_grid_y2 = (y2-self.block2_shift[1]) // self.tile_unit

                    ang = self.clockwise_angle([0, -1], [x2-x1, y2-y1])

                    if ang % 90 == 0:
                        # ->
                        if ang == 90:
                            for k in range(E_grid_x2 - (E_grid_x1 + 1) + 1):
                                ex_dis = abs(y1 - self.grids2[E_grid_x1+1+k][E_grid_y1].real_y)
                                ex_x = E_grid_x1+1+k
                                ex_y = E_grid_y1
                                in_dis = abs(y1 - self.grids4[E_grid_x1+1+k][E_grid_y1+1].real_y)
                                if ex_dis < in_dis:
                                    if self.grid_is_available(self.grids2, ex_x, ex_y, electrode_index):
                                        self.grid_set_electrode(self.grids2, ex_x, ex_y, electrode_index,
                                                                self.grids2[E_grid_x1+1+k][E_grid_y1].real_x, y1)
                        # | down
                        elif ang == 180:
                            for k in range(E_grid_y2 - (E_grid_y1 + 1) + 1):
                                ex_dis = abs(x1 - self.grids2[E_grid_x1+1][E_grid_y1+1+k].real_x)
                                ex_x = E_grid_x1+1
                                ex_y = E_grid_y1+1+k
                                in_dis = abs(x1 - self.grids4[E_grid_x1][E_grid_y1+1+k].real_x)
                                if ex_dis < in_dis:
                                    if self.grid_is_available(self.grids2, ex_x, ex_y, electrode_index):
                                        self.grid_set_electrode(self.grids2, ex_x, ex_y, electrode_index, x1,
                                                                self.grids2[E_grid_x1+1][E_grid_y1+1+k].real_y)
                        # <-
                        elif ang == 270:
                            for k in range(E_grid_x1 - E_grid_x2):
                                ex_dis = abs(y1 - self.grids2[E_grid_x1-k][E_grid_y1+1].real_y)
                                ex_x = E_grid_x1-k
                                ex_y = E_grid_y1+1
                                in_dis = abs(y1 - self.grids4[E_grid_x1-k][E_grid_y1].real_y)
                                if ex_dis < in_dis:
                                    if self.grid_is_available(self.grids2, ex_x, ex_y, electrode_index):
                                        self.grid_set_electrode(self.grids2, ex_x, ex_y, electrode_index,
                                                                self.grids2[E_grid_x1-k][E_grid_y1+1].real_x, y1)
                        # | up
                        elif ang == 360:
                            for k in range(E_grid_y1 - (E_grid_y2 + 1) + 1):
                                ex_dis = abs(x1 - self.grids2[E_grid_x1][E_grid_y1-k].real_x)
                                ex_x = E_grid_x1
                                ex_y = E_grid_y1-k
                                in_dis = abs(x1 - self.grids4[E_grid_x1+1][E_grid_y1-k].real_x)
                                if ex_dis < in_dis:
                                    if self.grid_is_available(self.grids2, ex_x, ex_y, electrode_index):
                                        self.grid_set_electrode(self.grids2, ex_x, ex_y, electrode_index, x1,
                                                                self.grids2[E_grid_x1][E_grid_y1-k].real_y)

                for j in range(len(electrode_shape_path)-1):
                    x1 = true_x+electrode_shape_path[j][0]
                    y1 = true_y+electrode_shape_path[j][1]
                    x2 = true_x+electrode_shape_path[j+1][0]
                    y2 = true_y+electrode_shape_path[j+1][1]

                    if x1 > boundary_R:
                        boundary_R = x1
                    if x1 < boundary_L:
                        boundary_L = x1
                    if y1 < boundary_U:
                        boundary_U = y1
                    if y1 > boundary_D:
                        boundary_D = y1

                    ang = self.clockwise_angle([0, -1], [x2-x1, y2-y1])

                    # 有角度
                    if ang % 90 != 0:
                        point = [(x1 + x2) / 2, (y1 + y2) / 2]
                        E_grid_x = int((point[0] - self.block2_shift[0]) // self.tile_unit)
                        E_grid_y = int((point[1] - self.block2_shift[1]) // self.tile_unit)
                        short_p = self.find_short_grid(self.grids2, [E_grid_x, E_grid_y], point)
                        ex_x = short_p[0]
                        ex_y = short_p[1]
                        if self.grid_is_available(self.grids2, ex_x, ex_y, electrode_index):
                            self.grid_set_electrode(self.grids2, ex_x, ex_y, electrode_index, point[0], point[1], True)
                            short_p_inner = self.find_short_grid_internal(self.grids4, [E_grid_x, E_grid_y], point, poly_points)
                            self.grid_set_electrode(self.grids4, short_p_inner[0], short_p_inner[1], electrode_index, point[0], point[1], True)
                            self.grids2[ex_x][ex_y].inner_grid = self.grids4[short_p_inner[0]][short_p_inner[1]]
                        else:
                            self.grid_conflict(self.grids2, ex_x, ex_y)
                            short_p_inner = self.find_short_grid_internal(self.grids2, [E_grid_x, E_grid_y], point, poly_points, [ex_x, ex_y])
                            # if short_p_inner[0] != ex_x and short_p_inner[1] != ex_y:
                            self.grid_set_electrode(self.grids2, short_p_inner[0], short_p_inner[1], electrode_index, point[0], point[1], True)
                new_electrode.boundary_U = boundary_U
                new_electrode.boundary_D = boundary_D
                new_electrode.boundary_L = boundary_L
                new_electrode.boundary_R = boundary_R

                self.electrodes.append(new_electrode)
