
class Hub():
    def __init__(self, real_x=-1, real_y=-1, type=-1, hub_index=-1):
        self.real_x = int(real_x)
        self.real_y = int(real_y)
        self.flow = 0
        self.index = -1
        self.hub_index = hub_index
        self.type = type
        self.neighbor = []

    def to_dict(self):
        _dict = {
            'real_x': self.real_x,
            'real_y': self.real_y,
            'flow': self.flow,
            'index': self.index,
            'hub_index': self.hub_index,
            'type': self.type,
            'neighbor': self.neighbor,
        }

        return _dict
