import os

from config import ROUTER_CONFIG
from grid import Grid, GridType
from hub import Hub
from tile import Tile

try:
    __location__ = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__)))
except:
    __location__ = '/Users/tommy/Documents/tommy/nr-router'


class ChipSection():
    def __init__(self, start_point: tuple, width: int, height: int, unit: float, radius: float):
        self.start_point: tuple = start_point
        self.width: int = width
        self.height: int = height
        self.unit: int = unit
        self.hypo_unit: int = int(unit * 2) - 1   # int(unit*2) - 1  # 2 * unit - 1  # unit * math.sqrt(2)
        self.radius: int = radius
        self.grid: list[list[Grid]] = []
        self.tile: list[list[Tile]] = []
        self.hub: list[Hub] = []
        self.hub_gap: int = 208

    def init_grid(self, grid_type=GridType.GRID, ref_pin=None, corner_pin=None):
        self.grid = []
        for i in range(self.width // self.unit + 1):
            self.grid.append([])
            for j in range(self.height // self.unit + 1):
                if ref_pin and [i, j] in ref_pin:
                    self.grid[i].append(Grid(i * self.unit + self.start_point[0], j * self.unit + self.start_point[1], i, j, GridType.REF))
                elif corner_pin and [i, j] in corner_pin:
                    self.grid[i].append(Grid(i * self.unit + self.start_point[0], j * self.unit + self.start_point[1], i, j, GridType.CORNER))
                else:
                    self.grid[i].append(Grid(i * self.unit + self.start_point[0], j * self.unit + self.start_point[1], i, j, grid_type))
    def init_tile(self):
        self.tile = []
        for i in range(self.width // self.unit):
            self.tile.append([])
            for j in range(self.height // self.unit):
                self.tile[i].append(Tile(i * self.unit + self.start_point[0] + (self.unit / 2),
                                    j * self.unit + self.start_point[1] + (self.unit / 2), i, j))

    def init_hub(self, y: float):
        self.hub = []
        for i in range((self.width // self.unit) + 4 * (self.width // self.unit - 1) + 5):
            if i % 5 == 0:
                # grid
                self.hub.append(Hub(self.grid[i//5][0].real_x, y, 0, i))
            else:
                # tile
                offset = self.radius + (i % 5) * self.hub_gap
                self.hub.append(Hub(self.grid[i//5][0].real_x + offset, y, 1, i))

    def get_grid(self, x: int, y: int) -> Grid:
        return self.grid[x][y]

    def is_edge_grid(self, x: int, y: int) -> bool:
        if x == len(self.grid) or y == len(self.grid[0]):
            return True
        if x == 0 or y == 0:
            return False

class Chip():
    def __init__(self, ewd_name: str, ewd_content: str = None):
        self.ewd_name = ewd_name
        self.ewd_content = ewd_content
        self.ewd_config_end = 0
        self.radius = 0
        self.electrode_shape_library = {}
        self.electrode_shape_count = 0

        # contactpad_list = [[x, y], etc.]
        self.contactpad_list: list[list] = []
        # electrode_list = [[shape, x, y], etc.]
        self.electrode_list: list[list] = []

        self.top_section: ChipSection = None
        self.mid_section: ChipSection = None
        self.bottom_section: ChipSection = None

    def setup(self):
        """Read ewd file and setup chip.
        """
        if self.ewd_content is None:
            self.ewd_content = self.read_ewd()
        else:
            self.ewd_content: str = self.ewd_content.split('\n')
        self.get_config()
        self.get_position()
        self.init_section()

    def read_ewd(self) -> str:
        """Read ewd file.

        Returns:
            str: ewd input content
        """
        ewd_input = []
        dir = os.path.join(__location__, 'ewd/' + self.ewd_name)
        readfile = open(dir, "r")
        for line in readfile:
            ewd_input.append(line)
        return ewd_input

    def get_config(self):
        """Get chip config from ewd file.
        """
        content: list[str] = self.ewd_content
        for line in content:
            if line.split()[0] == "#ENDOFDEFINITION#":
                self.ewd_config_end = content.index(line)
                break
            elif line.split()[0] == "contactpad" and line.split()[1] == "circle":
                self.radius = int(line.split()[3])
            elif len(line.split()) > 1 and line.split()[1] == "path":
                shape_name = line.split()[0]
                shape_scope = []
                for i in range(2, len(line.split())-1, 2):
                    t_x = line.split()[i][1:]
                    t_y = line.split()[i+1]
                    shape_scope.append((t_x, t_y))
                shape_scope.append((int(line.split()[2][1:]), int(line.split()[3])))

                self.electrode_shape_library[shape_name] = shape_scope
        self.electrode_shape_count = len(self.electrode_shape_library.keys())

    def get_position(self):
        """Get contact pad and electrode position from ewd file.
        """
        content: list[str] = self.ewd_content[self.ewd_config_end + 1:]
        for line in content:
            if line.split()[0] == "#ENDOFLAYOUT#":
                break
            true_x = float(line.split()[1])
            true_y = float(line.split()[2])
            # contact pad
            if line.split()[0] == "contactpad":
                self.contactpad_list.append([true_x, true_y])
            # electrodes
            elif line.split()[0] in self.electrode_shape_library:
                self.electrode_list.append([line.split()[0], true_x, true_y])

    def init_section(self):
        """Init chip section.
        """
        self.top_section = ChipSection(
            start_point = ROUTER_CONFIG.TOP_START_POINT,
            width = ROUTER_CONFIG.CONTACT_PAD_GAP * 31,
            height = ROUTER_CONFIG.CONTACT_PAD_GAP * 3,
            unit = ROUTER_CONFIG.CONTACT_PAD_GAP,
            radius = ROUTER_CONFIG.CONTACT_PAD_RADIUS
        )
        self.top_section.init_grid(
            grid_type = GridType.CONTACT_PAD,
            ref_pin = ROUTER_CONFIG.TOP_SECTION_REF_PIN,
            corner_pin = ROUTER_CONFIG.TOP_SECTION_CORNER_PIN
        )
        self.top_section.init_tile()
        self.top_section.init_hub(
            y = (ROUTER_CONFIG.MID_START_POINT[1] + ROUTER_CONFIG.CONTACT_PAD_GAP * 3 + ROUTER_CONFIG.CONTACT_PAD_RADIUS) // 2
        )

        self.mid_section = ChipSection(
            start_point = ROUTER_CONFIG.MID_START_POINT,
            width = ROUTER_CONFIG.ELECTRODE_SECTION[0],
            height = ROUTER_CONFIG.ELECTRODE_SECTION[1],
            unit = ROUTER_CONFIG.TILE_UNIT,
            radius = ROUTER_CONFIG.CONTACT_PAD_RADIUS
        )
        self.mid_section.init_grid()

        self.bottom_section = ChipSection(
            start_point = ROUTER_CONFIG.BOTTOM_START_POINT,
            width = ROUTER_CONFIG.CONTACT_PAD_GAP * 31,
            height = ROUTER_CONFIG.CONTACT_PAD_GAP * 3,
            unit = ROUTER_CONFIG.CONTACT_PAD_GAP,
            radius = ROUTER_CONFIG.CONTACT_PAD_RADIUS
        )
        self.bottom_section.init_grid(
            grid_type = GridType.CONTACT_PAD,
            ref_pin = ROUTER_CONFIG.BOTTOM_SECTION_REF_PIN,
            corner_pin = ROUTER_CONFIG.BOTTOM_SECTION_CORNER_PIN
        )
        self.bottom_section.init_tile()
        self.bottom_section.init_hub(
            y = (ROUTER_CONFIG.BOTTOM_START_POINT[1] - ROUTER_CONFIG.CONTACT_PAD_RADIUS + ROUTER_CONFIG.MID_START_POINT[1] + ROUTER_CONFIG.ELECTRODE_SECTION[1]) // 2
        )
