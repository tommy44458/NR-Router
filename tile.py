from grid import Grid, NeighborNode


class Tile():
    """Tile class.
    """
    def __init__(self, real_x: int = 0, real_y: int = 0, tile_x: int = 0, tile_y: int = 0):
        self.real_x: int = real_x
        self.real_y: int = real_y
        self.tile_x: int = tile_x
        self.tile_y: int = tile_y
        self.capacity: int = 4
        self.flow: list[tuple] = []
        self.total_flow: int = 0
        self.index: int = -1
        self.neighbor: list[NeighborNode] = []
        self.left_pad: Grid = None
        self.right_pad: Grid = None
        self.next_vertical: Tile = None
        self.contact_pads: list[Grid] = []
        self.covered: bool = False
