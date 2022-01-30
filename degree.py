from turtle import up
from typing import Tuple
import numpy as np
import math
import sys
import os
from ezdxf.addons import r12writer
from operator import itemgetter, attrgetter
from math import atan2, degrees


class Degree():

    def getdegree(x1, y1, x2, y2):
        x = x1-x2
        y = y1-y2
        hypotenuse = math.sqrt(x**2+y**2)
        if hypotenuse == 0:
            return(0, 1)
        sin = x/hypotenuse
        cos = y/hypotenuse
        return (round(sin, 5), round(cos, 5))

    def inner_degree(x1, y1, x2, y2):
        x = x1-x2
        y = y1-y2
        deg = 0
        if x == 0 and y > 0:
            deg = 0
        if x == 0 and y < 0:
            deg = 180
        if y == 0 and x > 0:
            deg = 90
        if y == 0 and x < 0:
            deg = 270
        if x > 0 and y > 0:
            deg = 360 + math.atan(x/y)*180/math.pi
        elif x < 0 and y > 0:
            deg = 360 + math.atan(x/y)*180/math.pi
        elif x < 0 and y < 0:
            deg = 180 + math.atan(x/y)*180/math.pi
        elif x > 0 and y < 0:
            deg = 180 + math.atan(x/y)*180/math.pi
        return int((deg+405) % 360)


def fill_degree_table():
    dia = abs(Degree.getdegree(0, 0, -1, -1)[0])
    # from up -> right -> down -> left
    # (0.0, -1.0)
    # (-0.71, -0.71)
    # (-1.0, 0.0)
    # (-0.71, 0.71)
    # (0.0, 1.0)
    # (0.71, 0.71)
    # (1.0, 0.0)
    # (0.71, -0.71)
    table = {
        (0.0, -1.0): {
            (0.0, -1.0): [1, 0, -1, 0],
            (-dia, -dia): [1, -2, -1, -2],
            (-1.0, 0.0): None,  # [-width, width, -width, -width],
            (-dia, dia): None,  # [-width, -tan, width, tan],
            (0.0, 1.0): None,  # [-width, 0, width, 0],
            (dia, dia): None,  # [-width, tan, width, -tan],
            (1.0, 0.0): None,  # [width, width, width, -width],
            (dia, -dia): [1, 2, -1, -2],
        },
        (-dia, -dia): {
            (0.0, -1.0): [1, -2, -1, 2],
            (-dia, -dia): [3, -3, -3, 3],
            (-1.0, 0.0): [2, -1, -2, 1],
            (-dia, dia): None,  # [-2*3_value, 0, 0, 2*3_value],
            (0.0, 1.0): None,  # [-1, 2, 1, -2],
            (dia, dia): None,  # [-3_value, 3_value, 3_value, -3_value],
            (1.0, 0.0): None,  # [-1, -2, 1, 2],
            (dia, -dia): None,  # [0, -2*3_value, 2*3_value, 0],
        },
        (-1.0, 0.0): {
            (0.0, -1.0): None,  # [-1, -1, 1, -1],
            (-dia, -dia): [2, -1, -2, 1],
            (-1.0, 0.0): [0, 1, 0, -1],
            (-dia, dia): [2, 1, -2, -1],
            (0.0, 1.0): None,  # [-1, 1, 1, 1],
            (dia, dia): None,
            (1.0, 0.0): None,
            (dia, -dia): None,
        },
        (-dia, dia): {
            (0.0, -1.0): None,
            (-dia, -dia): None,
            (-1.0, 0.0): [2, 1, -2, -1],
            (-dia, dia): [3, 3, -3, -3],
            (0.0, 1.0): [1, 2, -1, -2],
            (dia, dia): None,
            (1.0, 0.0): None,
            (dia, -dia): None,
        },
        (0.0, 1.0): {
            (0.0, -1.0): None,
            (-dia, -dia): None,
            (-1.0, 0.0): None,
            (-dia, dia): [1, 2, -1, -2],
            (0.0, 1.0): [1, 0, -1, 0],
            (dia, dia): [1, -2, -1, 2],
            (1.0, 0.0): None,
            (dia, -dia): None,
        },
        (dia, dia): {
            (0.0, -1.0): None,
            (-dia, -dia): None,
            (-1.0, 0.0): None,
            (-dia, dia): None,
            (0.0, 1.0): [1, -2, -1, 2],
            (dia, dia): [3, -3, -3, 3],
            (1.0, 0.0): [2, -1, -2, 1],
            (dia, -dia): None,
        },
        (1.0, 0.0): {
            (0.0, -1.0): None,
            (-dia, -dia): None,
            (-1.0, 0.0): None,
            (-dia, dia): None,
            (0.0, 1.0): None,
            (dia, dia): [2, -1, -2, 1],
            (1.0, 0.0): [0, 1, 0, -1],
            (dia, -dia): [2, 1, -2, -1],
        },
        (dia, -dia): {
            (0.0, -1.0): [1, 2, -1, -2],
            (-dia, -dia): None,
            (-1.0, 0.0): None,
            (-dia, dia): None,
            (0.0, 1.0): None,
            (dia, dia): None,
            (1.0, 0.0): [2, 1, -2, -1],
            (dia, -dia): [3, 3, -3, -3],
        }
    }

    return table, dia
