import numpy as np
import math
import sys
import os
from ezdxf.r12writer import r12writer
from operator import itemgetter, attrgetter
from math import atan2,degrees

class Wire():
    def __init__(self, start_x=0,start_y=0,end_x=0,end_y=0):
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.next=None
        self.head=1

    def to_dict(self):
        _dict = {
            'start_x': self.start_x,
            'start_y': self.start_y,
            'end_x': self.end_x,
            'end_y': self.end_y,
            'head': self.head
        }
        if self.next is not None:
            _dict['next'] = self.next.to_dict()
        else:
            _dict['next'] = None
            
        return _dict