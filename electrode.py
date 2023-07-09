from grid import Grid
from wire import Wire


class Electrode():
    """Electrode class.
    """
    def __init__(self, real_x: int = -1, real_y: int = -1, shape: str = 'base', electrode_index: int = -1):
        self.real_x: int = int(real_x)
        self.real_y: int = int(real_y)
        self.shape: str = shape
        self.electrode_index: int = electrode_index
        self.boundary_U: int = 0
        self.boundary_D: int = 0
        self.boundary_L: int = 0
        self.boundary_R: int = 0
        self.surround: int = 0
        self.index: int = -1
        self.poly: list = []
        self.pseudo_node_set: list[Grid] = []
        self.routing_wire: list[Wire] = []
