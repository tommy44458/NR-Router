import base64
import math
import sys
import time
# for converting dxf string to svg sting
from io import StringIO

import ezdxf
import matplotlib.path as mplPath
import matplotlib.pyplot as plt
import numpy as np
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

from chip import Chip
from config import *
from draw import Draw
from model_flow import ModelFlow
from model_mesh import ModelMesh
from model_min_cost_flow import ModelMinCostFlow
from pseudo_node import PseudoNode
from routing_wire import RoutingWire

# start_time = time.time()

try:
    ROUTER_CONFIG.CHIP_BASE = sys.argv[1]
except:
    pass

try:
    ROUTER_CONFIG.ELECTRODE_SIZE = int(sys.argv[2])
except:
    pass

try:
    ROUTER_CONFIG.UNIT_SCALE = int(sys.argv[3])
except:
    pass

try:
    ROUTER_CONFIG.OUTPUT_FORMAT = sys.argv[4]
except:
    pass

try:
    ROUTER_CONFIG.EWD_CONTENT = sys.argv[5]
except:
    pass

# c_time = time.time()

# read ewd file
# if ewd_input is None, then open local file
_chip = Chip(
    ewd_name = ROUTER_CONFIG.INPUT_FILE_NAME,
    ewd_content = ROUTER_CONFIG.EWD_CONTENT
)
_chip.setup()

_pseudo_node = PseudoNode(
    grid = _chip.mid_section.grid,
    shape_lib = _chip.electrode_shape_library,
    start_point = _chip.mid_section.start_point,
    unit = _chip.mid_section.unit,
    electrode_list = _chip.electrode_list
)
_model_mesh = ModelMesh(
    chip = _chip,
    pseudo_node = _pseudo_node
)
_model_mesh.setup()

# print('create mesh:', time.time() - c_time)

# c_time = time.time()

# flow nodes
_model_flow = ModelFlow(
    mesh = _model_mesh
)
_model_flow.setup()
# print('create flow:', time.time() - c_time)

# c_time = time.time()
# Min Cost Flow
_model_mcmf = ModelMinCostFlow(
    mesh = _model_mesh,
    flow = _model_flow
)
_model_mcmf.init_structure()
# print('mcmf init:', time.time() - c_time)
# t1 = time.time()
_model_mcmf.solver()
# print('mcmf solver:', time.time() - t1)
# print('mcmf solver:', time.time() - c_time)
_model_mcmf.get_path()
# print('mcmf path:', time.time() - c_time)

# c_time = time.time()
_draw = Draw(
    routing_wire = _model_mcmf.all_path,
    wire_width = ROUTER_CONFIG.REGULAR_WIRE_WIDTH,
    mini_wire_width = ROUTER_CONFIG.MINI_WIRE_WIDTH
)

doc = ezdxf.new(
    dxfversion='AC1024'
)
# doc.layers.new('BASE_LAYER', dxfattribs={'color': 2})
msp = doc.modelspace()
white_hatch = msp.add_hatch(color = 0)
# hatch = msp.add_hatch(color = 7)
# hatch1 = msp.add_hatch(color = 6)
red_hatch = msp.add_hatch(color = 1)
# hatch3 = msp.add_hatch(color = 4)
blue_hatch = msp.add_hatch(color = 5)
# dxf = hatch.paths
# dxf1 = hatch1.paths
white_dxf = white_hatch.paths
red_dxf = red_hatch.paths
# dxf3 = hatch3.paths
blue_dxf = blue_hatch.paths

_draw.draw_contact_pad(
    contactpad_list = _chip.contactpad_list,
    top_ref_pin_list = ROUTER_CONFIG.TOP_SECTION_REF_PIN,
    bottom_ref_pin_list = ROUTER_CONFIG.BOTTOM_SECTION_REF_PIN,
    top_corner_pin_list = ROUTER_CONFIG.TOP_SECTION_CORNER_PIN,
    bottom_corner_pin_list = ROUTER_CONFIG.BOTTOM_SECTION_CORNER_PIN,
    unit = ROUTER_CONFIG.CONTACT_PAD_GAP,
    dxf = msp,
    white_dxf = white_dxf,
    blue_dxf = blue_dxf,
    red_dxf = red_dxf
)
_draw.draw_electrodes(
    electrodes = _chip.electrode_list,
    shape_lib = _chip.electrode_shape_library,
    mesh_electrode_list = _model_mesh.electrodes,
    dxf = msp,
    red_dxf = red_dxf,
    white_dxf = white_dxf
)
_draw.draw_reference_electrode(msp)

# _draw.draw_pseudo_node(mid_section.grid, dxf2)
# _draw.draw_hub(_chip.top_section.hub, dxf2)
# _draw.draw_hub(_chip.bottom_section.hub, dxf2)
# _draw.draw_tile(top_section.tile, dxf2)
# _draw.draw_tile(bottom_section.tile, dxf2)

# _draw.draw_grid(top_section.start_point, top_section.unit, [len(top_section.grid), len(top_section.grid[0])], msp)
# _draw.draw_grid(mid_section.start_point, mid_section.unit, [len(mid_section.grid), len(mid_section.grid[0])], msp)
# _draw.draw_grid(bottom_section.start_point, bottom_section.unit, [len(bottom_section.grid), len(bottom_section.grid[0])], msp)

# print(f'electrode_number: {len(_model_mesh.electrodes)}, total runtime: {str(time.time() - start_time)}')

# reduce wire turn times

# c_time = time.time()
_routing_wire = RoutingWire(_pseudo_node, _chip.mid_section.grid, _model_mesh.electrodes)
reduce_times = 1
while reduce_times != 0:
    reduce_times = _routing_wire.reduce_wire_turn()

_routing_wire.divide_start_wire()

gui_routing_result = ''
combined_id = 0
for electrode in _model_mesh.electrodes:
    _draw.draw_all_wire(electrode.routing_wire, msp)

    if ROUTER_CONFIG.OUTPUT_FORMAT == 'ewds':
        x = int((electrode.real_x + 628) / ROUTER_CONFIG.ELECTRODE_SIZE)
        y = int((electrode.real_y - 12260) / ROUTER_CONFIG.ELECTRODE_SIZE)
        pin_x = round(electrode.routing_wire[len(electrode.routing_wire) - 1].end_x / ROUTER_CONFIG.CONTACT_PAD_GAP)
        pin_y = electrode.routing_wire[len(electrode.routing_wire) - 1].end_y

        if pin_y >= 56896:
            pin_y -= 56896
            pin_y /= ROUTER_CONFIG.CONTACT_PAD_GAP
            pin_y = round(pin_y)
            pin_y += 4
        else:
            pin_y /= ROUTER_CONFIG.CONTACT_PAD_GAP
            pin_y = round(pin_y)

        # match gui design pattern
        pin_number = 0
        if pin_y == 0:
            pin_number = 97 + pin_x
        elif pin_y == 1:
            pin_number = 96 - pin_x
        elif pin_y == 2:
            pin_number = 225 + pin_x
        elif pin_y == 3:
            pin_number = 224 - pin_x
            if pin_x < 8:
                pin_number += 1
            elif pin_x < 16:
                pin_number += 2
            elif pin_x < 24:
                pin_number += 3
            else:
                pin_number += 4
        elif pin_y == 4:
            pin_number = 169 + pin_x
            if pin_x > 23:
                pin_number -= 3
            elif pin_x > 15:
                pin_number -= 2
            elif pin_x > 7:
                pin_number -= 1
        elif pin_y == 5:
            pin_number = 168 - pin_x
        elif pin_y == 6:
            if pin_x > 23:
                pin_number = 129 + pin_x
            else:
                pin_number = 41 + pin_x
        elif pin_y == 7:
            pin_number = 40 - pin_x

        if electrode.shape == 'base':
            gui_routing_result += 'square' + " " + str(x) + " " + str(y) + " " + str(pin_number) + "\n"
        else:
            path = _chip.electrode_shape_library[electrode.shape]
            svg = ""
            for i in range(1, len(path), 2):
                point = " L " + str(math.floor((int(path[i][0]) + 60) / ROUTER_CONFIG.ELECTRODE_SIZE))
                if i == 1:
                    point = point.replace("L", "M")
                point += " " + str(math.floor((int(path[i][1]) + 60) / ROUTER_CONFIG.ELECTRODE_SIZE))
                svg += point
            elements = svg.split()
            # Process the rest of the elements
            i = 1
            points = []
            while i < len(elements):
                if elements[i] not in ['L', 'M']:
                    points.append((float(elements[i]), float(elements[i+1])))
                    i += 2
                else:
                    i += 1

            points_np = np.array(points)
            path = mplPath.Path(points_np)
            top_left_corners = []

            # Process each point in a grid
            for _x in np.arange(int(points_np[:,0].min()), int(points_np[:,0].max())):
                for _y in np.arange(int(points_np[:,1].min()), int(points_np[:,1].max())):
                    # Check if the top-left corner of the grid square is inside the path
                    # Add a small offset to include points on the border
                    if path.contains_point((_x + 0.1, _y + 0.1)):
                        top_left_corners.append((x + _x, y + _y))

            for _x, _y in top_left_corners:
                gui_routing_result += 'combine' + " " + str(_x) + " " + str(_y) + " " + str(combined_id) + " " + str(pin_number) + "\n"
            combined_id += 1

gui_routing_result += '#ENDOFELECTRODE#\n'
gui_routing_result += '0::100:0\n'
gui_routing_result += '#ENDOFSEQUENCE#\n'

# print(f'reduce runtime: {str(time.time() - c_time)}')

if ROUTER_CONFIG.OUTPUT_FORMAT == 'dxf':
    encode_dxf = doc.encode_base64()
    print(base64.b64decode(encode_dxf).decode())
elif ROUTER_CONFIG.OUTPUT_FORMAT == 'dxf-based64':
    encode_dxf = doc.encode_base64()
    print(encode_dxf.decode())
elif ROUTER_CONFIG.OUTPUT_FORMAT == 'svg':
    # dxf string to svg string
    fig = plt.figure()
    ax = fig.add_axes([0, 0, 1, 1])
    ctx = RenderContext(doc)
    out = MatplotlibBackend(ax)
    Frontend(ctx, out).draw_layout(doc.modelspace(), finalize=True)
    str = StringIO()
    fig.savefig(str, format='svg')
    svg = str.getvalue()
    print(svg)
elif ROUTER_CONFIG.OUTPUT_FORMAT == 'file':
    doc.saveas('dwg/' + ROUTER_CONFIG.OUTPUT_FILE_NAME + '.dxf')
elif ROUTER_CONFIG.OUTPUT_FORMAT == 'ewds':
    print(gui_routing_result)

# print(f'total time: {str(time.time() - start_time)}')