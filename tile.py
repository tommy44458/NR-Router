from grid import Grid


class Tile():
    def __init__(self, real_x=0, real_y=0, tile_x=0, tile_y=0):
        self.real_x = real_x
        self.real_y = real_y
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.capacity = 4
        self.flow: list[tuple] = []
        self.total_flow = 0
        self.index = -1
        self.neighbor = []
        self.left_pad: Grid = None
        self.right_pad: Grid = None
        self.next_vertical: Tile = None
        self.contact_pads: list[Grid] = []
