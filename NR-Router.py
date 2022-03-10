import sys
import ezdxf
import time
import base64

# for converting dxf string to svg sting
from io import StringIO
import matplotlib.pyplot as plt
from ezdxf.addons.drawing import RenderContext, Frontend
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

from chip import Chip
from grid import Grid, GridType
from draw import Draw
from model_mesh import ModelMesh
from model_flow import ModelFlow
from model_min_cost_flow import ModelMinCostFlow
from pseudo_node import PseudoNode

from routing_wire import RoutingWire

from chip_section import ChipSection

start_time = time.time()

ewd_input = None
ewd_name = 'mask'
electrode_size = 1000
unit_scale = 4
MAX_WIRE_WIDTH = 200
UNIT_LIST = [1000, 500, 250, 200, 125, 100]

try:
    electrode_size = int(sys.argv[1])
except:
    electrode_size = 1000

try:
    unit_scale = int(sys.argv[2])
except:
    unit_scale = 4

try:
    ewd_input = sys.argv[3]
except:
    ewd_input = None

# real ship size
regular_line_width = int(electrode_size / 10)
if regular_line_width > MAX_WIRE_WIDTH:
    regular_line_width = MAX_WIRE_WIDTH
mini_line_width = 5
contactpad_unit = 2540
contactpad_radius = 750
# (wire width + 5) * 1.414
tile_unit = min(UNIT_LIST, key=lambda x: abs(x - int(electrode_size / unit_scale)))

for unit in UNIT_LIST:
    if unit <= int(electrode_size / unit_scale) and electrode_size % unit == 0:
        tile_unit = unit
        break

if (regular_line_width + 5) * 1.414 > unit:
    regular_line_width = (int((unit / 1.414) - 5) // 50) * 50
"""
    contact section
    - x: 0 ~ (32 * contact_pad_unit)
    - y: 0 ~ (3 * contact_pad_unit), 56896 ~ (56896 + 3 * contact_pad_unit)

    electrode section
    - 82000 * 42000
"""

# create chip construction: top section (pad), mid section (electrode), down section (pad)
top_start_point = [0, 0]
mid_start_point = [-1630, 11258]
down_start_point = [0, 56896]

top_section = ChipSection(top_start_point, contactpad_unit * 31, contactpad_unit * 3, contactpad_unit,
                          contactpad_radius)
top_section.init_grid(GridType.CONTACTPAD)
top_section.init_tile()
top_section.init_hub((mid_start_point[1] + top_section.unit * 3 + top_section.redius) // 2)

mid_section = ChipSection(mid_start_point, 82000, 42000, tile_unit, contactpad_radius)
mid_section.init_grid()

down_section = ChipSection(down_start_point, contactpad_unit * 31, contactpad_unit * 3, contactpad_unit,
                           contactpad_radius)
down_section.init_grid(GridType.CONTACTPAD)
down_section.init_tile()
down_section.init_hub((down_start_point[1] - down_section.redius + mid_start_point[1] + mid_section.height) // 2)

c_time = time.time()

# read ewd file
# if ewd_input is None, then open local file
_chip = Chip('ewod-chip-project.ewd', ewd_input)
_chip.setup()

_pseudo_node = PseudoNode(mid_section.grid, _chip.electrode_shape_library, mid_section.start_point,
                          mid_section.unit, _chip.electrode_list)
_model_mesh = ModelMesh(top_section, mid_section, down_section, _pseudo_node)
_model_mesh.get_pseudo_node()
_model_mesh.create_pseudo_node_connection()
_model_mesh.create_grid_connection(mid_section.grid, mid_section.unit, mid_section.hypo_unit)
_model_mesh.create_tile_connection(top_section.grid, top_section.tile, 'top')
_model_mesh.create_tile_connection(down_section.grid, down_section.tile, 'down')
_model_mesh.create_hub_connection(top_section.grid, top_section.hub, 0, -1, top_section.tile)
_model_mesh.create_hub_connection(down_section.grid, down_section.hub, -1, 0, down_section.tile)

# print('create mesh:', time.time() - c_time)

c_time = time.time()

# flow nodes
_model_flow = ModelFlow(_model_mesh)
_model_flow.create_all_flownode()
# print('create flow:', time.time() - c_time)

c_time = time.time()
# Min Cost Flow
_model_mcmf = ModelMinCostFlow(_model_mesh, _model_flow)
_model_mcmf.init_structure()
# print('mcmf init:', time.time() - c_time)
# t1 = time.time()
_model_mcmf.solver()
# print('mcmf solver:', time.time() - t1)
# print('mcmf solver:', time.time() - c_time)
_model_mcmf.get_path()
# print('mcmf path:', time.time() - c_time)

c_time = time.time()
_draw = Draw(_model_mcmf.all_path, regular_line_width, mini_line_width)

doc = ezdxf.new(dxfversion='AC1024')
# doc.layers.new('BASE_LAYER', dxfattribs={'color': 2})
msp = doc.modelspace()
# hatch = msp.add_hatch(color=7)
# hatch1 = msp.add_hatch(color=6)
hatch2 = msp.add_hatch(color=1)
# hatch3 = msp.add_hatch(color=4)
# hatch4 = msp.add_hatch(color=5)
# dxf = hatch.paths
# dxf1 = hatch1.paths
dxf2 = hatch2.paths
# dxf3 = hatch3.paths
# dxf4 = hatch4.paths

_draw.draw_contact_pad(_chip.contactpad_list, msp)
_draw.draw_electrodes(_chip.electrode_list, _chip.electrode_shape_library, _model_mesh.electrodes, msp, dxf2)

# _draw.draw_pseudo_node(mid_section.grid, dxf2)
# _draw.draw_hub(top_section.hub, dxf2)
# _draw.draw_hub(down_section.hub, dxf2)
# _draw.draw_tile(top_section.tile, dxf2)
# _draw.draw_tile(down_section.tile, dxf2)

_ruting_wire = RoutingWire(_pseudo_node, mid_section.grid, _model_mesh.electrodes)
# reduce wire turn times
reduce_times = 1
while reduce_times != 0:
    reduce_times = _ruting_wire.reduce_wire_turn()

_ruting_wire.divide_start_wire()

for electrode in _model_mesh.electrodes:
    _draw.draw_all_wire(electrode.routing_wire, msp)

# _draw.draw_grid(top_section.start_point, top_section.unit, [len(top_section.grid), len(top_section.grid[0])], msp)
# _draw.draw_grid(mid_section.start_point, mid_section.unit, [len(mid_section.grid), len(mid_section.grid[0])], msp)
# _draw.draw_grid(down_section.start_point, down_section.unit, [len(down_section.grid), len(down_section.grid[0])], msp)

# print(f'electrode_number: {len(_model_mesh.electrodes)}, total runtime: {str(time.time() - start_time)}')

encode_dxf = doc.encode_base64()
print(base64.b64decode(encode_dxf).decode())

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

# doc.saveas('dwg/' + ewd_name + '.dxf')

# print('draw:', time.time() - c_time)
