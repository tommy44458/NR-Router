from node.grid import Grid


class Hub(Grid):
    """Hub class.
    """
    def __init__(self, real_x: int = -1, real_y: int = -1, type: int = -1, hub_index: int = -1):
        Grid.__init__(self, real_x, real_y, -1, -1, type)
        self.hub_index: int = hub_index
