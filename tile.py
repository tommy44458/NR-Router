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

    def to_dict(self):
        _dict = {
            'real_x': self.real_x,
            'real_y': self.real_y,
            'tile_x': self.tile_x,
            'tile_y': self.tile_y,
            'capacity': self.capacity,
            'flow': self.flow,
            'total_flow': self.total_flow,
            'index': self.index,
            'neighbor': self.neighbor,
            'contact_pads': self.contact_pads
        }

        return _dict
