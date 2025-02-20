import base64
from io import StringIO
import os
import shutil
import ctypes

import matplotlib.pyplot

import ezdxf
import matplotlib
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
import multiprocessing

from chip import Chip
from config import *
from draw import Draw
from gui import get_gui_result_per_wire
from model.model_flow import ModelFlow
from model.model_mesh import ModelMesh
from model.model_min_cost_flow import ModelMinCostFlow
from node.pseudo_node import PseudoNode
from wire.routing_wire_opt import RoutingWireOpt
import json
import gc

# req
# chip_base
# electrode_size
# unit
# output_format
# ewd_content

def release_memory():
    gc.collect()
    
    try:
        libc = ctypes.CDLL("libc.so.6")
        libc.malloc_trim(0)  # 強制釋放 C 擴展模組的記憶體
    except Exception as e:
        print(f"Failed to release memory: {e}")

def cleanup_tmp():
    tmp_path = "/tmp"
    for filename in os.listdir(tmp_path):
        file_path = os.path.join(tmp_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")

    release_memory()
    gc.collect()

def run_algo():
    result = {}
    try:
        gui_routing_result = ''
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

        _doc = ezdxf.new(
            dxfversion='AC1024'
        )
        # doc.layers.new('BASE_LAYER', dxfattribs={'color': 2})
        msp = _doc.modelspace()
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

        # _draw.draw_pseudo_node(_chip.mid_section.grid, blue_dxf)
        # _draw.draw_closed_elec_node(_chip.mid_section.grid, red_dxf)
        # _draw.draw_hub(_chip.top_section.hub, dxf2)
        # _draw.draw_hub(_chip.bottom_section.hub, dxf2)
        # _draw.draw_tile(top_section.tile, dxf2)
        # _draw.draw_tile(bottom_section.tile, dxf2)

        # _draw.draw_grid(top_section.start_point, top_section.unit, [len(top_section.grid), len(top_section.grid[0])], msp)
        # _draw.draw_grid(_chip.mid_section.start_point, _chip.mid_section.unit, [len(_chip.mid_section.grid), len(_chip.mid_section.grid[0])], msp)
        # _draw.draw_grid(bottom_section.start_point, bottom_section.unit, [len(bottom_section.grid), len(bottom_section.grid[0])], msp)

        # print(f'electrode_number: {len(_model_mesh.electrodes)}, total runtime: {str(time.time() - start_time)}')

        # reduce wire turn times
        # c_time = time.time()
        _routing_wire_opt = RoutingWireOpt(_pseudo_node, _chip.mid_section.grid, _model_mesh.electrodes)
        _routing_wire_opt.run()

        combined_id = 0
        for electrode in _model_mesh.electrodes:
            _draw.draw_all_wire(electrode.routing_wire, msp)

            if ROUTER_CONFIG.OUTPUT_FORMAT == 'ewds':
                gui_routing_result += get_gui_result_per_wire(electrode, _chip.electrode_shape_library, combined_id)
                combined_id += 1

        gui_routing_result += '#ENDOFELECTRODE#\n'
        gui_routing_result += '0::100:0\n'
        gui_routing_result += '#ENDOFSEQUENCE#\n'

        try:
            if ROUTER_CONFIG.OUTPUT_FORMAT == OutputFormat.DXF:
                encode_dxf = _doc.encode_base64()
                ret = base64.b64decode(encode_dxf).decode()
                del encode_dxf
                result = {
                    "statusCode": 200,
                    "body": ret
                }
            elif ROUTER_CONFIG.OUTPUT_FORMAT == OutputFormat.DXF_BASED_64:
                encode_dxf = _doc.encode_base64()
                ret = encode_dxf.decode()
                del encode_dxf
                result = {
                    "statusCode": 200,
                    "body": ret
                }
            elif ROUTER_CONFIG.OUTPUT_FORMAT == OutputFormat.SVG:
                # dxf string to svg string
                fig = matplotlib.pyplot.figure()
                ax = fig.add_axes([0, 0, 1, 1])
                ctx = RenderContext(_doc)
                out = MatplotlibBackend(ax)
                Frontend(ctx, out).draw_layout(_doc.modelspace(), finalize=True)
                strIO = StringIO()
                fig.savefig(strIO, format='svg')
                # fig.savefig(f'dwg/{ROUTER_CONFIG.OUTPUT_FILE_NAME}.svg', format='svg')
                svg = strIO.getvalue()

                result = {
                    "statusCode": 200,
                    "body": svg
                }
            elif ROUTER_CONFIG.OUTPUT_FORMAT == OutputFormat.FILE:
                _doc.saveas(f'dwg/{ROUTER_CONFIG.OUTPUT_FILE_NAME}.dxf')
            elif ROUTER_CONFIG.OUTPUT_FORMAT == OutputFormat.EWDS:
                result = {
                    "statusCode": 200,
                    "body": gui_routing_result
                }
        except Exception as e:
            result = {
                "statusCode": 401,
                "body": json.dumps({"error": str(e)})
            }
    except Exception as e:
        return {
            "statusCode": 401,
            "body": json.dumps({"error": str(e)})
        }
    finally:
        del _chip, _pseudo_node, _model_mesh, _model_flow, _model_mcmf
        del _draw, _doc, _routing_wire_opt
        gc.collect()

    return result

def run_algo_subprocess(body: str, result_dict: dict):
    """ 子進程內執行 `run_algo()`，確保記憶體釋放 """
    body_json: dict = json.loads(body)
    ROUTER_CONFIG.CHIP_BASE = body_json.get("chip_base", ROUTER_CONFIG.CHIP_BASE)
    ROUTER_CONFIG.ELECTRODE_SIZE = body_json.get("electrode_size", ROUTER_CONFIG.ELECTRODE_SIZE)
    ROUTER_CONFIG.UNIT_SCALE = body_json.get("unit", ROUTER_CONFIG.UNIT_SCALE)
    ROUTER_CONFIG.OUTPUT_FORMAT = body_json.get("output_format", ROUTER_CONFIG.OUTPUT_FORMAT)
    ROUTER_CONFIG.EWD_CONTENT = body_json.get("ewd_content", ROUTER_CONFIG.EWD_CONTENT)

    print(f"run_algo_subprocess ROUTER_CONFIG: {str(ROUTER_CONFIG)}")

    try:
        result_dict["result"] = run_algo()
    except Exception as e:
        result_dict["result"] = {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
    finally:
        os._exit(0)  # 強制子進程結束，確保記憶體完全釋放


def handler(event, context):
    # print(f'reduce runtime: {str(time.time() - c_time)}')
    
    with multiprocessing.Manager() as manager:
        result_dict = manager.dict()
        process = multiprocessing.Process(target=run_algo_subprocess, args=(event["body"], result_dict,))
        
        process.start()  # 啟動子進程
        process.join(timeout=600)   # 等待子進程完成

        if process.is_alive():
            process.terminate()  # 如果超時，強制終止子進程
            response = {
                "statusCode": 500,
                "body": json.dumps({"error": "Subprocess timed out"})
            }
        else:
            response = result_dict["result"]  # 從子進程獲取結果

    cleanup_tmp()
    return response