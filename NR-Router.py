import base64
import sys
import time
# for converting dxf string to svg sting
from io import StringIO

import ezdxf
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

from chip import Chip
from config import *
from draw import Draw
from gui import get_gui_result_per_wire
from model.model_flow import ModelFlow
from model.model_mesh import ModelMesh
from model.model_min_cost_flow import ModelMinCostFlow
from node.pseudo_node import PseudoNode
from wire.routing_wire_opt import RoutingWireOpt

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
white_hatch_2 = msp.add_hatch(color = 0)
# hatch = msp.add_hatch(color = 7)
# hatch1 = msp.add_hatch(color = 6)
red_hatch = msp.add_hatch(color = 1)
red_hatch_2 = msp.add_hatch(color = 1)
# hatch3 = msp.add_hatch(color = 4)
blue_hatch = msp.add_hatch(color = 5)
# dxf = hatch.paths
# dxf1 = hatch1.paths
white_dxf = white_hatch.paths
white_dxf_2 = white_hatch_2.paths
red_dxf = red_hatch.paths
red_dxf_2 = red_hatch_2.paths
# dxf3 = hatch3.paths
blue_dxf = blue_hatch.paths

_draw.draw_contact_pad(
    contactpad_list = _chip.contactpad_list,
    top_section = _chip.top_section,
    bottom_section = _chip.bottom_section,
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
    red_dxf_2 = red_dxf_2,
    white_dxf = white_dxf,
    white_dxf_2 = white_dxf_2

)
if ROUTER_CONFIG.CHIP_BASE == ChipBase.GLASS:
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
_routing_wire_opt = RoutingWireOpt(_pseudo_node, _chip.mid_section.grid, _model_mesh.electrodes)
_routing_wire_opt.run()

gui_routing_result = ''
combined_id = 0
for electrode in _model_mesh.electrodes:
    _draw.draw_all_wire(electrode.routing_wire, msp)

    if ROUTER_CONFIG.OUTPUT_FORMAT == 'ewds':
        gui_routing_result += get_gui_result_per_wire(electrode, _chip.electrode_shape_library, combined_id)
        combined_id += 1

gui_routing_result += '#ENDOFELECTRODE#\n'
gui_routing_result += '0::100:0\n'
gui_routing_result += '#ENDOFSEQUENCE#\n'

# print(f'reduce runtime: {str(time.time() - c_time)}')

if ROUTER_CONFIG.OUTPUT_FORMAT == OutputFormat.DXF:
    encode_dxf = doc.encode_base64()
    print(base64.b64decode(encode_dxf).decode())
elif ROUTER_CONFIG.OUTPUT_FORMAT == OutputFormat.DXF_BASED_64:
    encode_dxf = doc.encode_base64()
    print(encode_dxf.decode())
elif ROUTER_CONFIG.OUTPUT_FORMAT == OutputFormat.SVG:
    # dxf string to svg string
    fig = plt.figure()
    ax = fig.add_axes([0, 0, 1, 1])
    ctx = RenderContext(doc)
    out = MatplotlibBackend(ax)
    Frontend(ctx, out).draw_layout(doc.modelspace(), finalize=True)
    str = StringIO()
    fig.savefig(str, format='svg')
    # fig.savefig(f'dwg/{ROUTER_CONFIG.OUTPUT_FILE_NAME}.svg', format='svg')
    svg = str.getvalue()
    print(svg)
elif ROUTER_CONFIG.OUTPUT_FORMAT == OutputFormat.FILE:
    doc.saveas(f'dwg/{ROUTER_CONFIG.OUTPUT_FILE_NAME}.dxf')
elif ROUTER_CONFIG.OUTPUT_FORMAT == OutputFormat.EWDS:
    print(gui_routing_result)

# print(f'total time: {str(time.time() - start_time)}')