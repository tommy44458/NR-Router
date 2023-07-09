from enum import IntEnum
from typing import Union

from pydantic import BaseModel, root_validator
from strenum import StrEnum

"""
    contact section
    - x: 0 ~ (32 * contact_pad_unit)
    - y: 0 ~ (3 * contact_pad_unit), 56896 ~ (56896 + 3 * contact_pad_unit)

    electrode section
    - 82000 * 42000
"""

UNIT_LIST = [1000, 500, 250, 200, 125, 100]

class WireDirect(IntEnum):
    UP = 0
    TOP_RIGHT = 1
    RIGHT = 2
    BOTTOM_RIGHT = 3
    BOTTOM = 4
    BOTTOM_LEFT = 5
    LEFT = 6
    TOP_LEFT = 7

class ChipBase(StrEnum):
    GLASS = 'glass'
    PAPER = 'paper'

class OutputFormat(StrEnum):
    FILE = 'file'
    DXF = 'dxf'
    EWDS = 'ewds'
    DXF_BASED_64 = 'dxf_base64'
    SVG = 'svg'

class GlassBasedConfig(BaseModel):
    INPUT_FILE_NAME: str = 'test0307.ewd'
    MID_START_POINT: tuple = (-1630, 11258)
    ELECTRODE_SECTION: tuple = (84000, 44000)
    HUB_NUM: int = 5
    REGULAR_WIRE_WIDTH: int = 40
    MINI_WIRE_WIDTH: int = 20

GLASS_BASED_CONFIG = GlassBasedConfig()

class PaperBasedConfig(BaseModel):
    INPUT_FILE_NAME: str = 'test0625-1.ewd'
    TILE_UNIT: int = 1300
    MID_START_POINT: tuple = (-2580, 10308)
    ELECTRODE_SECTION: tuple = (82000, 42000)
    HUB_NUM: int = 2
    REGULAR_WIRE_WIDTH: int = 300
    MINI_WIRE_WIDTH: int = 300

PAPER_BASED_CONFIG = PaperBasedConfig()

class RouterConfig(BaseModel):
    # chip base material
    CHIP_BASE: ChipBase = ChipBase.GLASS
    # input file name
    INPUT_FILE_NAME: str = 'test0307.ewd'
    # output file name
    OUTPUT_FILE_NAME: str = 'mask'
    # output format
    OUTPUT_FORMAT: OutputFormat = OutputFormat.FILE
    # electrode size in um
    ELECTRODE_SIZE: int = 1000
    # for calculating the routing tile size
    UNIT_SCALE: int = 4
    # ewd content from front-end
    EWD_CONTENT: Union[str, None] = None
    # contact pad gap in um in up, bottom section
    CONTACT_PAD_GAP: int = 2540
    # contact pad radius in um
    CONTACT_PAD_RADIUS: int = 750
    # routing tile unit in um
    TILE_UNIT: int = 0
    # routing wire width size in um
    REGULAR_WIRE_WIDTH: int = 40
    MINI_WIRE_WIDTH: int = 20
    # routing section start point
    TOP_START_POINT: tuple = (0, 0)
    MID_START_POINT: tuple = (-2580, 10308)
    BOTTOM_START_POINT: tuple = (0, 56896)
    # the section of the chip that is used for placing the electrodes
    ELECTRODE_SECTION: tuple = (82000, 42000)


    # reference contact pad position
    TOP_SECTION_REF_PIN: list[tuple] = [[0, 3], [8, 3], [16, 3], [24, 3]]
    TOP_SECTION_CORNER_PIN: list[tuple] = [[0, 0], [31, 0]]
    BOTTOM_SECTION_REF_PIN: list[tuple] = [[7, 0], [15, 0], [23, 0], [31, 0]]
    BOTTOM_SECTION_CORNER_PIN: list[tuple] = [[0, 3], [31, 3]]

    # hub number per each contact pad gap
    HUB_NUM: int = 5

    class Config:
        validate_assignment = True

    @root_validator(skip_on_failure=True)
    def sync(cls, values: dict):
        if values['CHIP_BASE'] == ChipBase.GLASS:
            for unit in UNIT_LIST:
                if unit <= int(values['ELECTRODE_SIZE'] / values['UNIT_SCALE']) and values['ELECTRODE_SIZE'] % unit == 0:
                    values['TILE_UNIT'] = unit
                    break
            values['MID_START_POINT'] = GLASS_BASED_CONFIG.MID_START_POINT
            values['ELECTRODE_SECTION'] = GLASS_BASED_CONFIG.ELECTRODE_SECTION
            values['INPUT_FILE_NAME'] = GLASS_BASED_CONFIG.INPUT_FILE_NAME
            values['HUB_NUM'] = GLASS_BASED_CONFIG.HUB_NUM
            values['REGULAR_WIRE_WIDTH'] = GLASS_BASED_CONFIG.REGULAR_WIRE_WIDTH
            values['MINI_WIRE_WIDTH'] = GLASS_BASED_CONFIG.MINI_WIRE_WIDTH
        elif values['CHIP_BASE'] == ChipBase.PAPER:
            values['TILE_UNIT'] = PAPER_BASED_CONFIG.TILE_UNIT
            values['MID_START_POINT'] = PAPER_BASED_CONFIG.MID_START_POINT
            values['ELECTRODE_SECTION'] = PAPER_BASED_CONFIG.ELECTRODE_SECTION
            values['INPUT_FILE_NAME'] = PAPER_BASED_CONFIG.INPUT_FILE_NAME
            values['HUB_NUM'] = PAPER_BASED_CONFIG.HUB_NUM
            values['REGULAR_WIRE_WIDTH'] = PAPER_BASED_CONFIG.REGULAR_WIRE_WIDTH
            values['MINI_WIRE_WIDTH'] = PAPER_BASED_CONFIG.MINI_WIRE_WIDTH

        return values

ROUTER_CONFIG = RouterConfig()


