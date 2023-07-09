from grid import Grid
from wire import Wire


class Electrode():
    def __init__(self, real_x=-1, real_y=-1, shape: str = 'base', electrode_index=-1):
        self.real_x = int(real_x)
        self.real_y = int(real_y)
        self.shape = shape
        self.electrode_index = electrode_index
        self.boundary_U = 0
        self.boundary_D = 0
        self.boundary_L = 0
        self.boundary_R = 0
        self.surround = 0
        self.index = -1
        self.poly: list = []
        self.pseudo_node_set: list[Grid] = []
        self.routing_wire: list[Wire] = []
