import numpy as np
import math
import sys
import os
from ezdxf.r12writer import r12writer
from operator import itemgetter, attrgetter
from math import atan2,degrees

from grid import Grid
from tile import Tile
from hub import Hub
from electrode import Electrode
from wire import Wire
from degree import Degree
from draw import Draw
from mesh import Mesh
from flow import Flow

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

_mesh = Mesh(Control_pad_unit, Tile_Unit,
                block1_shift, block2_shift, block3_shift,
                grids1_length, grids2_length, grids3_length, 
                tiles1_length, tiles2_length, tiles3_length,
                hubs1_length, hubs1_y, hubs3_length, hubs3_y)

radius = 0
shape = []
shape_scope = []
# electrodes = []
# contactpads = []
num_electrode = 0
shape_count=0

#create grids2
_mesh.create_grid_electrode()
_mesh.create_grid_pad()
_mesh.create_hub()
        
ewd_content = []

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

_mesh.list_electrodes = list_electrodes_d + list_electrodes_u
_mesh.set_grid_by_electrode_edge(shape, shape_scope)

# for elec in electrodes:
#     print(elec.to_dict())
        
## DEBUG print some grid
for i in range(0, len(_mesh.grids2)-1):
    for j in range(0, len(_mesh.grids2[i])-1):
        if _mesh.grids2[i][j].electrode_index in [3]:
            print('***\n', i, j)
            # if i == 116 and j == 136:
            #     grids2[i][j].electrode_y = 52055
            for item in _mesh.grids2[i][j].to_dict():
                if item == 'electrode_x' or item == 'electrode_y':
                    print(item, _mesh.grids2[i][j].to_dict()[item])
            
#create electrodes neighbor
# lock_index1 = -1
# lock_index2 = -1
_mesh.create_neighbor_electrodes()
            
_mesh.set_safe_distance()
_mesh.create_grids_connection()
            
_mesh.create_tiles_connection(_mesh.tiles1_length, _mesh.grids1, _mesh.tiles1, block=1)
_mesh.create_tiles_connection(_mesh.tiles3_length, _mesh.grids3, _mesh.tiles3, block=3)

_mesh.create_hubs_connection(_mesh.hubs1, _mesh.hubs1_length, 0, -1, _mesh.grids1, _mesh.tiles1)
_mesh.create_hubs_connection(_mesh.hubs3, _mesh.hubs3_length, -1, 0, _mesh.grids3, _mesh.tiles3)

_flow = Flow(_mesh)
_flow.create_all_flownode()

start_nodes = []
end_nodes = []
capacities = []
unit_costs = []
supplies = [0 for i in range(len(_flow.flownodes))]
num_supply = 0
tmp_c=0

for node in _flow.flownodes:
    if type(node) == Tile and node.index != _flow.global_t.index:
        #pseudo two layer
        start_nodes.append(node.index+1)
        end_nodes.append(node.index)
        capacities.append(int(node.capacity))
        unit_costs.append(0)
        # add neighbor tiles
        for nb_node in node.neighbor:
            start_nodes.append(node.index)
            end_nodes.append(nb_node[0].index+1)
            capacities.append(int(nb_node[1]))
            unit_costs.append(int(Control_pad_unit))
        # add contact pads
        for cp_node in node.contact_pads:
            start_nodes.append(node.index)
            end_nodes.append(cp_node.index)
            capacities.append(1)
            unit_costs.append(1)
        supplies[node.index] = 0
    elif type(node) == Tile and node.index==_flow.global_t.index:
        for cp_node in node.contact_pads:
            start_nodes.append(cp_node.index)
            end_nodes.append(node.index)
            capacities.append(1)
            unit_costs.append(-1)
        supplies[node.index] = 0
    elif type(node) == Grid:
        if node.type==0:
            start_nodes.append(node.index+1)
            end_nodes.append(node.index)
            capacities.append(1)
            unit_costs.append(0)
            for nb_node in node.neighbor:
                start_nodes.append(node.index)
                if type(nb_node[0])==Grid:
                    end_nodes.append(nb_node[0].index+1)
                else:
                    end_nodes.append(nb_node[0].index)
                capacities.append(int(nb_node[1]))
                unit_costs.append(int(nb_node[2]))
        if len(node.neighbor_electrode) > 0:
            for ne_node in node.neighbor_electrode:
                start_nodes.append(_mesh.electrodes[ne_node[0]].index)
                end_nodes.append(node.index+1)
                capacities.append(1)
                if ne_node[1]==1 or ne_node[1]==6:
                    unit_costs.append(0)
                else:
                    unit_costs.append(200)
        supplies[node.index] = 0	
    elif type(node) == Hub:
        for nb_node in node.neighbor:
            start_nodes.append(node.index)
            end_nodes.append(nb_node[0].index)
            capacities.append(int(nb_node[1]))
            unit_costs.append(int(nb_node[2]))
        supplies[node.index] = 0
    elif type(node) == Electrode:
        supplies[node.index] = 1
        num_supply+=1
        
supplies[_flow.global_t.index] = -num_supply

### ortool
from ortools.graph import pywrapgraph
min_cost_flow = pywrapgraph.SimpleMinCostFlow()
# print("start min_cost_flow")

# Add each arc.
for i in range(0, len(start_nodes)):
    min_cost_flow.AddArcWithCapacityAndUnitCost(start_nodes[i], end_nodes[i],
                                                capacities[i], unit_costs[i])
# print("Add each arc")

# Add node supplies.
sum = 0
for i in range(0, len(supplies)):
    min_cost_flow.SetNodeSupply(i, supplies[i])
    sum += supplies[i]
# print("Add node supplies")

MaxFlowWithMinCost = min_cost_flow.SolveMaxFlowWithMinCost()

#Find the minimum cost flow between node 0 and node 4.
all_path = []
electrode_wire=[[] for _ in range(_mesh.num_electrode)]
if MaxFlowWithMinCost == min_cost_flow.OPTIMAL and len(electrode_wire) > 0:
#     print('Minimum cost:', min_cost_flow.OptimalCost())	
    for i in range(min_cost_flow.NumArcs()):
        if min_cost_flow.Flow(i) != 0:
            head = min_cost_flow.Tail(i)
            tail = min_cost_flow.Head(i)
            if _flow.flownodes[head] == 0:
                pass
            if _flow.flownodes[tail] == 0:
                tail -= 1

            if type(_flow.flownodes[head]) == Electrode and type(_flow.flownodes[tail]) == Grid:
                index_list = []
                tmp_x = _flow.flownodes[tail].grid_x
                tmp_y = _flow.flownodes[tail].grid_y
                for en_node in _flow.flownodes[tail].neighbor_electrode:
                    if en_node[0] == _flow.flownodes[head].electrode_index:
                        index_list.append([en_node[1],en_node[2],en_node[3]])
                if len(index_list)==1: ## only belong to ONE Electrode
                    E_x = _mesh.grids2[tmp_x+index_list[0][1],tmp_y+index_list[0][2]].electrode_x
                    E_y = _mesh.grids2[tmp_x+index_list[0][1],tmp_y+index_list[0][2]].electrode_y
                    Shift_x = E_x - _mesh.grids2[tmp_x+index_list[0][1],tmp_y+index_list[0][2]].real_x
                    Shift_y = E_y - _mesh.grids2[tmp_x+index_list[0][1],tmp_y+index_list[0][2]].real_y
                    #all_path.append(Wire(int(_mesh.grids2[tmp_x+index_list[0][1],tmp_y+index_list[0][2]].real_x),int(_mesh.grids2[tmp_x+index_list[0][1],tmp_y+index_list[0][2]].real_y),int(_flow.flownodes[tail].real_x),int(_flow.flownodes[tail].real_y)))
                    all_path.append(Wire(int(E_x),int(E_y),int(_flow.flownodes[tail].real_x+Shift_x),int(_flow.flownodes[tail].real_y+Shift_y)))
                    all_path.append(Wire(int(_flow.flownodes[tail].real_x+Shift_x),int(_flow.flownodes[tail].real_y+Shift_y),int(_flow.flownodes[tail].real_x),int(_flow.flownodes[tail].real_y)))
                else:
                    for nb_list in index_list:
                        if nb_list[0] == 1 or nb_list[0] == 6: ## dir of electrode left-top & right-top only have ONE E
                            if _mesh.grids2[tmp_x+nb_list[1],tmp_y+nb_list[2]].electrode_y2!=0:
                                _mesh.grids2[tmp_x+nb_list[1],tmp_y+nb_list[2]].electrode_y=_mesh.grids2[tmp_x+nb_list[1],tmp_y+nb_list[2]].electrode_y2
                            all_path.append(Wire(int(_mesh.grids2[tmp_x+nb_list[1],tmp_y+nb_list[2]].electrode_x),int(_mesh.grids2[tmp_x+nb_list[1],tmp_y+nb_list[2]].electrode_y),int(_flow.flownodes[tail].real_x),int(_flow.flownodes[tail].real_y)))
                        if nb_list[0] == 3 or nb_list[0] == 4:
                            all_path.append(Wire(int(_mesh.grids2[tmp_x+nb_list[1],tmp_y+nb_list[2]].electrode_x),int(_mesh.grids2[tmp_x+nb_list[1],tmp_y+nb_list[2]].electrode_y),int(_flow.flownodes[tail].real_x),int(_flow.flownodes[tail].real_y)))
            elif type(_flow.flownodes[head]) == Grid and type(_flow.flownodes[tail]) == Grid:
                all_path.append(Wire(int(_flow.flownodes[head].real_x),int(_flow.flownodes[head].real_y),int(_flow.flownodes[tail].real_x),int(_flow.flownodes[tail].real_y)))
                _flow.flownodes[head].flow=1
                _flow.flownodes[tail].flow=1
            elif type(_flow.flownodes[head]) == Grid and type(_flow.flownodes[tail]) == Hub:
                all_path.append(Wire(int(_flow.flownodes[head].real_x),int(_flow.flownodes[head].real_y),int(_flow.flownodes[tail].real_x),int(_flow.flownodes[tail].real_y)))
            elif type(_flow.flownodes[head]) == Hub and type(_flow.flownodes[tail]) == Grid:
                all_path.append(Wire(int(_flow.flownodes[head].real_x),int(_flow.flownodes[head].real_y),int(_flow.flownodes[tail].real_x),int(_flow.flownodes[tail].real_y)))
            elif type(_flow.flownodes[head]) == Hub and type(_flow.flownodes[tail]) == Tile:
                all_path.append(Wire(int(_flow.flownodes[head].real_x),int(_flow.flownodes[head].real_y),int(_flow.flownodes[head].real_x),int(_flow.flownodes[tail].real_y)))
                if _flow.flownodes[head].hub_index%3 == 1:
                    _flow.flownodes[tail].flow[0]=1
                elif _flow.flownodes[head].hub_index%3 == 2:
                    _flow.flownodes[tail].flow[1]=1
            elif type(_flow.flownodes[head]) == Tile and type(_flow.flownodes[tail]) == Tile:
                _flow.flownodes[head].total_flow+=min_cost_flow.Flow(i)
                if _flow.flownodes[head].tile_x == _flow.flownodes[tail].tile_x:
                    _flow.flownodes[head].vertical_path.append(_flow.flownodes[tail])
                elif _flow.flownodes[head].tile_y == _flow.flownodes[tail].tile_y:
                    _flow.flownodes[head].horizontal_path.append(_flow.flownodes[tail])
            elif type(_flow.flownodes[head]) == Tile and type(_flow.flownodes[tail]) == Grid:
                _flow.flownodes[head].corner_in.append(_flow.flownodes[tail])
    
if MaxFlowWithMinCost == min_cost_flow.OPTIMAL and len(electrode_wire) > 0:
    _flow.create_tiles_path(_mesh.tiles1_length,_mesh.tiles1,_mesh.hubs1,_mesh.tiles1_length[1]-1,-1,-1,all_path)
    _flow.create_tiles_path(_mesh.tiles3_length,_mesh.tiles3,_mesh.hubs3,0,_mesh.tiles1_length[1],1,all_path)
#     print("all_path = ",len(all_path))

if MaxFlowWithMinCost == min_cost_flow.OPTIMAL and len(electrode_wire) > 0:
    for i in range(len(all_path)):
        for j in range(len(all_path)):
            if all_path[j].start_x == all_path[i].end_x and all_path[j].start_y == all_path[i].end_y:
                all_path[i].next = all_path[j]
                all_path[j].head = 0 ## 0 or 1 
                break

#     print("---------------------------------")

if MaxFlowWithMinCost == min_cost_flow.OPTIMAL and len(electrode_wire) > 0:
    j=0

    for i in range(len(all_path)):
        if all_path[i].head == 1 and j < len(electrode_wire):
            #print(all_path[i].start_x,all_path[i].start_y,all_path[i].end_x,all_path[i].end_y)
            #dxf.add_circle(center=(all_path[i].start_x, -all_path[i].start_y), radius = 750.0)
            electrode_wire[j].append(all_path[i])
            tmp_next = all_path[i].next
            while tmp_next != None:
                #print(tmp_next.start_x,tmp_next.start_y,tmp_next.end_x,tmp_next.end_y)
                if tmp_next.start_x==tmp_next.end_x and tmp_next.start_y==tmp_next.end_y:
                    break
                electrode_wire[j].append(tmp_next)
                tmp_next = tmp_next.next
            j+=1
            
if MaxFlowWithMinCost == min_cost_flow.OPTIMAL and len(electrode_wire) > 0:
    draw_second = 0

    # electrode_wire[0].clear()
    # electrode_wire[0].append(Wire(start_x=-4835,start_y=13889,end_x=0,end_y=13889))
    # electrode_wire[0].append(Wire(start_x=0,start_y=13889,end_x=0,end_y=7620))
                        
_draw = Draw(MaxFlowWithMinCost, min_cost_flow, block2_shift, Tile_Unit, electrode_wire, shape_scope)

with r12writer('dwg/' + ewd_name + '.dwg') as dxf:
    _draw.draw_contact_pads(_mesh.contactpads, dxf)
    _draw.draw_electrodes(_mesh.electrodes, dxf)
    _draw.draw_all_path(dxf, _mesh.grids2)
    
response = ''
with open('dwg/' + ewd_name + '.dwg') as f:
    for line in f.readlines():
        response = response + line
        
# print(response)
    
    
## show grid text view

# draw_grid(block1_shift[0], block1_shift[1], Control_pad_unit, grids1_length[0], grids1_length[1])
# draw_grid(block2_shift[0], block2_shift[1], Tile_Unit, grids2_length[0], grids2_length[1])
# draw_grid(block3_shift[0], block3_shift[1], Control_pad_unit, grids3_length[0], grids3_length[1])
