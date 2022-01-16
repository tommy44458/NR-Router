import sys
import os
from ezdxf.addons import r12writer
import ezdxf
from operator import itemgetter, attrgetter
from math import atan2,degrees
import time

from chip import Chip
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

ewd_input = None
ewd_name = 'mask'
try:
    ewd_input = sys.argv[1]
except:
    ewd_input = None
    
try:
    ewd_name = sys.argv[2]
except:
    ewd_name = 'mask'

###start###
###init coordinate###
## real ship size
electrode_size = 2000
regular_line_width = int(electrode_size / 10)
control_pad_unit = 2540
# (wire width + 5) * 1.414
tile_unit = int((regular_line_width + 5) * 1.414) + 1 #(line width) 200 + (spacing) 115
if tile_unit < 150:
    tile_unit = 150
## top down dot field dot
block1_shift = (-3000 + 18000 % control_pad_unit, -17745 + 17745 % control_pad_unit)
block2_shift = (-3000, 9258)
block3_shift = (-3000 + 18000 % control_pad_unit, 56896)
# Grid_x = 317
# Grid_y = 127
grids1_length = ((100000 - 18000 - block1_shift[0]) // control_pad_unit + 1, (7620 - block1_shift[1]) // control_pad_unit + 1)
grids2_length = ( ((100000 - 18000 - block2_shift[0]) // tile_unit) + 1, (46000 // tile_unit) + 1)
grids3_length = ((100000 - 18000 - block3_shift[0]) // control_pad_unit + 1, (100000 - 17745 - block3_shift[1]) // control_pad_unit + 1)
tiles1_length = (grids1_length[0]-1, grids1_length[1]-1)
tiles2_length = (grids2_length[0]-1, grids2_length[1]-1)
tiles3_length = (grids3_length[0]-1, grids3_length[1]-1)
hubs1_length = 2 * tiles1_length[0] + grids1_length[0]
hubs1_y = (block2_shift[1] + 7620 + 750) // 2
hubs3_length = 2 * tiles3_length[0] + grids3_length[0]
hubs3_y = (block3_shift[1] - 750 + tiles2_length[1] * tile_unit + block2_shift[1] ) // 2

# print('grid: ', grids1_length, grids2_length, grids3_length)
c_time = time.time()

_mesh = Mesh(control_pad_unit, tile_unit,
                block1_shift, block2_shift, block3_shift,
                grids1_length, grids2_length, grids3_length, 
                tiles1_length, tiles2_length, tiles3_length,
                hubs1_length, hubs1_y, hubs3_length, hubs3_y)

# mesh structure
_mesh.create_grid_electrode()
_mesh.create_grid_pad()
_mesh.create_hub()
        
# read ewd file
_chip = Chip('test_1208_1.ewd', ewd_input)
_chip.setup()

_mesh.set_contactpad_grid(_chip.contactpad_list)

_mesh.set_grid_by_electrode_edge_internal2(_chip.electrode_list, _chip.electrode_shape_library)
_mesh.set_grid_by_electrode_edge_opt2(_chip.electrode_list, _chip.electrode_shape_library)

for i in range(len(_mesh.grids4)):
    for j in range(len(_mesh.grids4[i])):
        if _mesh.grids4[i, j].electrode_index >= 0 and _mesh.grids2[i, j].electrode_index < 0:
            _mesh.grids2[i, j] = _mesh.grids4[i, j]
            
_mesh.create_neighbor_electrodes()
            
_mesh.set_safe_distance()
_mesh.create_grids_connection()
            
_mesh.create_tiles_connection(_mesh.tiles1_length, _mesh.grids1, _mesh.tiles1, block=1)
_mesh.create_tiles_connection(_mesh.tiles3_length, _mesh.grids3, _mesh.tiles3, block=3)

_mesh.create_hubs_connection(_mesh.hubs1, _mesh.hubs1_length, 0, -1, _mesh.grids1, _mesh.tiles1)
_mesh.create_hubs_connection(_mesh.hubs3, _mesh.hubs3_length, -1, 0, _mesh.grids3, _mesh.tiles3)

print('create mesh:', time.time() - c_time)
        
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
_draw = Draw(_mcmf.MaxFlowWithMinCost, _mcmf.min_cost_flow, _mesh.block2_shift,
             _mesh.tile_unit, _mcmf.electrode_wire, regular_line_width, 2.5)

doc = ezdxf.new(dxfversion='R2010')
doc.layers.new('TEXTLAYER', dxfattribs={'color': 2})
msp = doc.modelspace()
hatch = msp.add_hatch(color=7)
hatch1 = msp.add_hatch(color=6)
hatch2 = msp.add_hatch(color=2)
hatch3 = msp.add_hatch(color=4)
hatch4 = msp.add_hatch(color=5)
dxf = hatch.paths
dxf1 = hatch1.paths
dxf2 = hatch2.paths
dxf3 = hatch3.paths
dxf4 = hatch4.paths

_draw.draw_contact_pads(_mesh.contactpads, msp)
_draw.draw_all_path(dxf3, _mesh.grids2)
_draw.draw_electrodes(_chip.electrode_list, _chip.electrode_shape_library, dxf)
# _draw.draw_grid(block1_shift[0], block1_shift[1], control_pad_unit, grids1_length[0], grids1_length[1], msp)
_draw.draw_grid(block2_shift[0], block2_shift[1], tile_unit, grids2_length[0], grids2_length[1], msp)
# _draw.draw_grid(block3_shift[0], block3_shift[1], control_pad_unit, grids3_length[0], grids3_length[1], msp)
_draw.draw_pseudo_node(_mesh.grids2, dxf1)
_draw.draw_pseudo_node_corner(_mesh.grids2, dxf2)
# _draw.draw_pseudo_node(_mesh.grids4, dxf2)

doc.saveas('dwg/' + ewd_name + '.dwg')

print('draw:', time.time() - c_time)

# print(_mesh.clockwise_angle([0, -1], [1, 0]))
# deg = Degree.getdegree(1, 1, 0, 0)
# dis = _mesh.point_distance_line([0, 0], [0, 2], [2, 0])
# print(deg, dis)
# print([0 + dis * deg[0], 0 + dis * deg[1]])
# print(_mesh.get_short_point([0, 0], [0, 2], [2, 0]))
# print(_mesh.get_short_point([41850, -43908], [42050, -43655], [41950, -43555]))
# print(_mesh.get_short_point([-100, -355], [0, 0], [-100, 100]))
# print(_mesh.get_points_lines(42050, -43655, 41950, -43555, 70.5))

# str1 = ''
# for i in range(0, 12):
#     x = int(8000 + 8000 * math.cos(2 * math.pi * i / 12))
#     y = int(8000 + 8000 * math.sin(2 * math.pi * i / 12))
#     if i == 0:
#         str1 += str('M' + str(x) + ' ' + str(y) + ' ')
#     elif i == 11:
#         str1 += str('L' + str(x) + ' ' + str(y) + ' ')
#     else:
#         str1 += str('L' + str(x) + ' ' + str(y) + ' ')
    
# # str1 += 'Z'

# # str1 = ''
# for i in range(11, -1, -1):
#     x = int(8000 + 6000 * math.cos(2 * math.pi * i / 12))
#     y = int(8000 + 6000 * math.sin(2 * math.pi * i / 12))
#     if i == 11:
#         str1 += str('L' + str(x) + ' ' + str(y) + ' ')
#     elif i == 0:
#         str1 += str('L' + str(x) + ' ' + str(y) + ' ')
#     else:
#         str1 += str('L' + str(x) + ' ' + str(y) + ' ')
    
# str1 += 'Z'

# print(str1)

# str1 = ''
# for i in range(0, 12):
#     x = int(8000 + 5900 * math.cos(2 * math.pi * i / 12))
#     y = int(8000 + 5900 * math.sin(2 * math.pi * i / 12))
#     if i == 0:
#         str1 += str('M' + str(x) + ' ' + str(y) + ' ')
#     elif i == 11:
#         str1 += str('L' + str(x) + ' ' + str(y) + ' ')
#     else:
#         str1 += str('L' + str(x) + ' ' + str(y) + ' ')
    
# # str1 += 'Z'

# # str1 = ''
# for i in range(11, -1, -1):
#     x = int(8000 + 3900 * math.cos(2 * math.pi * i / 12))
#     y = int(8000 + 3900 * math.sin(2 * math.pi * i / 12))
#     if i == 11:
#         str1 += str('L' + str(x) + ' ' + str(y) + ' ')
#     elif i == 0:
#         str1 += str('L' + str(x) + ' ' + str(y) + ' ')
#     else:
#         str1 += str('L' + str(x) + ' ' + str(y) + ' ')
    
# str1 += 'Z'

# print(str1)

# str1 = ''
# for i in range(0, 12):
#     x = int(8000 + 3800 * math.cos(2 * math.pi * i / 12))
#     y = int(8000 + 3800 * math.sin(2 * math.pi * i / 12))
#     if i == 0:
#         str1 += str('M' + str(x) + ' ' + str(y) + ' ')
#     elif i == 11:
#         str1 += str('L' + str(x) + ' ' + str(y) + ' ')
#     else:
#         str1 += str('L' + str(x) + ' ' + str(y) + ' ')
    
# # str1 += 'Z'
    
# str1 += 'Z'

# print(str1)

# response = ''
# with open('dwg/' + ewd_name + '.dwg') as f:
#     for line in f.readlines():
#         response = response + line
        
# print(response)
    
    
## show grid text view
