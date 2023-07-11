import math

from config import WireDirect
from node.grid import Grid


class Wire():
    """Wire class.
    """
    def __init__(self, start_x: int = 0, start_y: int = 0, end_x: int = 0, end_y: int = 0, direct: WireDirect = None, grid_list: list[Grid] = []):
        self.start_x: int = start_x
        self.start_y: int = start_y
        self.end_x: int = end_x
        self.end_y: int = end_y
        self.next: Wire = None
        self.head: Wire = 1
        self.grid_list: list[Grid] = grid_list
        self.direct: WireDirect = direct

    def length(self) -> float:
        d_x = self.end_x - self.start_x
        d_y = self.end_y - self.start_y
        return math.sqrt(d_x**2 + d_y**2)
