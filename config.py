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
    MID_START_POINT: tuple = (-1630, 11258)
    ELECTRODE_SECTION: tuple = (84000, 44000)

GLASS_BASED_CONFIG = GlassBasedConfig()

class PaperBasedConfig(BaseModel):
    TILE_UNIT: int = 1300
    MID_START_POINT: tuple = (-2580, 10308)
    ELECTRODE_SECTION: tuple = (82000, 42000)

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
    TOP_SECTION_REF_PIN: list = [[0, 3], [8, 3], [16, 3], [24, 3]]
    TOP_SECTION_CORNER_PIN: list = [[0, 0], [31, 0]]
    BOTTOM_SECTION_REF_PIN: list = [[7, 0], [15, 0], [23, 0], [31, 0]]
    BOTTOM_SECTION_CORNER_PIN: list = [[0, 3], [31, 3]]

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
        elif values['CHIP_BASE'] == ChipBase.PAPER:
            values['TILE_UNIT'] = PAPER_BASED_CONFIG.TILE_UNIT
            values['MID_START_POINT'] = PAPER_BASED_CONFIG.MID_START_POINT
            values['ELECTRODE_SECTION'] = PAPER_BASED_CONFIG.ELECTRODE_SECTION

        return values

ROUTER_CONFIG = RouterConfig()


