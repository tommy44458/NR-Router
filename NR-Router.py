import numpy as np
import math
import sys
import os
from ezdxf.r12writer import r12writer
from operator import itemgetter, attrgetter
from math import atan2,degrees
import time

from grid import Grid
from tile import Tile
from hub import Hub
from electrode import Electrode
from wire import Wire
from degree import Degree
from draw import Draw
from mesh import Mesh
from flow import Flow
from mcmf import MCMF

try:
    __location__ = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__)))
except:
    __location__ = '/Users/tommy/Documents/tommy/nr-router'
    
_use_ewd_file = False

ewd_input = ""
ewd_name = ""
try:
    ewd_input = sys.argv[1]
except:
    _use_ewd_file = True
    
try:
    ewd_name = sys.argv[2]
except:
    ewd_name = 'mask'
    
if len(ewd_input) < 10:
    _use_ewd_file = True
if len(ewd_name) > 20:
    ewd_name = 'mask'
                    
                    
###start###
###init coordinate###
## real ship size
Control_pad_unit = 2540
Tile_Unit = 315 #(line width) 200 + (spacing) 115
## top down dot field dot
block1_shift = (-18000 + 18000 % Control_pad_unit, -17745 + 17745 % Control_pad_unit)
block2_shift = (-18000, 9258)
block3_shift = (-18000 + 18000 % Control_pad_unit, 56896)
# Grid_x = 317
# Grid_y = 127
grids1_length = ((100000 - 18000 - block1_shift[0]) // Control_pad_unit + 1, (7620 - block1_shift[1]) // Control_pad_unit + 1)
grids2_length = ( ((100000 - 18000 - block2_shift[0]) // Tile_Unit) + 1, (46000 // Tile_Unit) + 1)
grids3_length = ((100000 - 18000 - block3_shift[0]) // Control_pad_unit + 1, (100000 - 17745 - block3_shift[1]) // Control_pad_unit + 1)
tiles1_length = (grids1_length[0]-1, grids1_length[1]-1)
tiles2_length = (grids2_length[0]-1, grids2_length[1]-1)
tiles3_length = (grids3_length[0]-1, grids3_length[1]-1)
hubs1_length = 2 * tiles1_length[0] + grids1_length[0]
hubs1_y = (block2_shift[1] + 7620 + 750) // 2
hubs3_length = 2 * tiles3_length[0] + grids3_length[0]
hubs3_y = (block3_shift[1] - 750 + tiles2_length[1] * Tile_Unit + block2_shift[1] ) // 2

# print('grid: ', grids1_length, grids2_length, grids3_length)
c_time = time.time()

_mesh = Mesh(Control_pad_unit, Tile_Unit,
                block1_shift, block2_shift, block3_shift,
                grids1_length, grids2_length, grids3_length, 
                tiles1_length, tiles2_length, tiles3_length,
                hubs1_length, hubs1_y, hubs3_length, hubs3_y)

# mesh structure
_mesh.create_grid_electrode()
_mesh.create_grid_pad()
_mesh.create_hub()
        
ewd_content = []
radius = 0
shape = []
shape_scope = []
shape_count=0

if _use_ewd_file == True:
    dir = os.path.join(__location__, 'ewd/test2.ewd')
    readfile = open(dir, "r")
    for index, line in enumerate(readfile):
        ewd_input+=line
        
### ewd_input string analysis ###
ewd_content = ewd_input.split('\n')
#print(ewd_input_split)

end_index = 0
for line in ewd_content:
    if line.split()[0] == "#ENDOFDEFINITION#":
        end_index = ewd_content.index(line)
        break
    elif line.split()[0] == "contactpad" and line.split()[1] == "circle":
        radius = int(line.split()[3])
    elif len(line.split()) > 1 and line.split()[1] == "path":
        shape.append(line.split()[0])
        shape_count+=1
        scope = []
        for i in range(2,len(line.split())-1,2):
            t_x=int(line.split()[i][1:])
            t_y=int(line.split()[i+1])
            scope.append((t_x,t_y))
        scope.append((int(line.split()[2][1:]),int(line.split()[3])))
        shape_scope.append(scope)

ewd_content = ewd_content[ end_index + 1 : ]

# print('shape: ', shape, '\nshape_scope: ', shape_scope)

#print(ewd_content)
#print(ewd_content_head)

list_electrodes_u = []
list_electrodes_d = []

for line in ewd_content:
    if line.split()[0] == "#ENDOFLAYOUT#":
        break
    true_x = int(float(line.split()[1]))
    true_y = int(float(line.split()[2]))
    ## 	contact pad
    if line.split()[0] == "contactpad":	
        _mesh.contactpads.append((true_x,true_y))
        if true_y<=7620 :
            grid_x = (true_x - block1_shift[0]) // Control_pad_unit
            grid_y = (true_y - block1_shift[1]) // Control_pad_unit
            newgrid = Grid(true_x, true_y, grid_x, grid_y, -1)
            _mesh.grids1[grid_x, grid_y] = newgrid
            if abs(true_x-(((true_x-block2_shift[0])//Tile_Unit)*Tile_Unit+block2_shift[0])) > abs(true_x-(((true_x-block2_shift[0])//Tile_Unit+1)*Tile_Unit+block2_shift[0])):
                _mesh.grids1[grid_x, grid_y].real_x = (((true_x-block2_shift[0])//Tile_Unit+1)*Tile_Unit+block2_shift[0])
            else:
                _mesh.grids1[grid_x, grid_y].real_x = (((true_x-block2_shift[0])//Tile_Unit)*Tile_Unit+block2_shift[0])
        else :
            grid_x = (true_x - block3_shift[0]) // Control_pad_unit
            grid_y = (true_y - block3_shift[1]) // Control_pad_unit
            newgrid = Grid(true_x, true_y, grid_x, grid_y, -1)
            _mesh.grids3[grid_x, grid_y] = newgrid
            if abs(true_x-(((true_x-block2_shift[0])//Tile_Unit)*Tile_Unit+block2_shift[0])) > abs(true_x-(((true_x-block2_shift[0])//Tile_Unit+1)*Tile_Unit+block2_shift[0])):
                _mesh.grids3[grid_x, grid_y].real_x = (((true_x-block2_shift[0])//Tile_Unit+1)*Tile_Unit+block2_shift[0])
            else:
                _mesh.grids3[grid_x, grid_y].real_x = (((true_x-block2_shift[0])//Tile_Unit)*Tile_Unit+block2_shift[0])
    ## electrodes
    elif line.split()[0] in shape:
        grid_y = (true_y-block2_shift[1]) // Tile_Unit
        if grid_y >= 73:
            list_electrodes_d.append([true_y, true_x, line.split()[0]])
        else:
            list_electrodes_u.append([true_y, true_x, line.split()[0]])

list_electrodes_u.sort(key=lambda x: (x[0], x[1]))
list_electrodes_d.sort(key=lambda x: (-x[0], -x[1]))

# mesh connections
_mesh.list_electrodes = list_electrodes_d + list_electrodes_u
_mesh.set_grid_by_electrode_edge(shape, shape_scope)
            
_mesh.create_neighbor_electrodes()
            
_mesh.set_safe_distance()
_mesh.create_grids_connection()
            
_mesh.create_tiles_connection(_mesh.tiles1_length, _mesh.grids1, _mesh.tiles1, block=1)
_mesh.create_tiles_connection(_mesh.tiles3_length, _mesh.grids3, _mesh.tiles3, block=3)

_mesh.create_hubs_connection(_mesh.hubs1, _mesh.hubs1_length, 0, -1, _mesh.grids1, _mesh.tiles1)
_mesh.create_hubs_connection(_mesh.hubs3, _mesh.hubs3_length, -1, 0, _mesh.grids3, _mesh.tiles3)

print('create mesh:', time.time() - c_time)

# for elec in electrodes:
#     print(elec.to_dict())
        
## DEBUG print some grid
# for i in range(0, len(_mesh.grids2)-1):
#     for j in range(0, len(_mesh.grids2[i])-1):
#         if _mesh.grids2[i][j].electrode_index in [3]:
#             print('***\n', i, j)
#             # if i == 116 and j == 136:
#             #     grids2[i][j].electrode_y = 52055
#             for item in _mesh.grids2[i][j].to_dict():
#                 if item == 'electrode_x' or item == 'electrode_y':
#                     print(item, _mesh.grids2[i][j].to_dict()[item])

c_time = time.time()

# flow nodes
_flow = Flow(_mesh)
_flow.create_all_flownode()

print('create flow:', time.time() - c_time)

c_time = time.time()
# MCMF
_mcmf = MCMF(_mesh, _flow)
_mcmf.init_structure()
_mcmf.solver()
_mcmf.get_path()
print('mcmf:', time.time() - c_time)

c_time = time.time()           
_draw = Draw(_mcmf.MaxFlowWithMinCost, _mcmf.min_cost_flow, _mesh.block2_shift, _mesh.Tile_Unit, _mcmf.electrode_wire, shape_scope)

with r12writer('dwg/' + ewd_name + '.dwg') as dxf:
    _draw.draw_contact_pads(_mesh.contactpads, dxf)
    _draw.draw_electrodes(_mesh.electrodes, dxf)
    _draw.draw_all_path(dxf, _mesh.grids2)

print('draw:', time.time() - c_time)
    
# response = ''
# with open('dwg/' + ewd_name + '.dwg') as f:
#     for line in f.readlines():
#         response = response + line
        
# print(response)
    
    
## show grid text view

# draw_grid(block1_shift[0], block1_shift[1], Control_pad_unit, grids1_length[0], grids1_length[1])
# draw_grid(block2_shift[0], block2_shift[1], Tile_Unit, grids2_length[0], grids2_length[1])
# draw_grid(block3_shift[0], block3_shift[1], Control_pad_unit, grids3_length[0], grids3_length[1])
