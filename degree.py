import math

from config import WireDirect


class Degree():

    def get_degree(x1, y1, x2, y2):
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


dia = abs(Degree.get_degree(0, 0, -1, -1)[0])


def wire_offset_table():
    dia = abs(Degree.get_degree(0, 0, -1, -1)[0])
    """
        from up -> right -> bottom -> left
        (0.0, -1.0) - top
        (-0.71, -0.71) - top-right
        (-1.0, 0.0) - right
        (-0.71, 0.71) - bottom-right
        (0.0, 1.0) - bottom
        (0.71, 0.71) - bottom-left
        (1.0, 0.0) left
        (0.71, -0.71) left-up
    """
    table = {
        (0.0, -1.0): {
            (0.0, -1.0): [1, 0, -1, 0],
            (-dia, -dia): [1, -2, -1, 2],
            (-1.0, 0.0): None,
            (-dia, dia): None,
            (0.0, 1.0): None,
            (dia, dia): None,
            (1.0, 0.0): None,
            (dia, -dia): [1, 2, -1, -2],
            None: [1, 0, -1, 0]
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
            None: [3, -3, -3, 3]
        },
        (-1.0, 0.0): {
            (0.0, -1.0): [1, -1, -1, 1],  # [-1, -1, 1, -1],
            (-dia, -dia): [2, -1, -2, 1],
            (-1.0, 0.0): [0, 1, 0, -1],
            (-dia, dia): [2, 1, -2, -1],
            (0.0, 1.0): [1, 1, -1, -1],  # [-1, 1, 1, 1],
            (dia, dia): None,
            (1.0, 0.0): None,
            (dia, -dia): None,
            None: [0, 1, 0, -1]
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
            None: [3, 3, -3, -3]
        },
        (0.0, 1.0): {
            (0.0, -1.0): None,
            (-dia, -dia): None,
            (-1.0, 0.0): [1, 1, -1, -1],
            (-dia, dia): [1, 2, -1, -2],
            (0.0, 1.0): [1, 0, -1, 0],
            (dia, dia): [1, -2, -1, 2],
            (1.0, 0.0): [1, -1, -1, 1],
            (dia, -dia): None,
            None: [1, 0, -1, 0]
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
            None: [3, -3, -3, 3]
        },
        (1.0, 0.0): {
            (0.0, -1.0): [1, 1, -1, -1],
            (-dia, -dia): None,
            (-1.0, 0.0): None,
            (-dia, dia): None,
            (0.0, 1.0): [1, -1, -1, 1],
            (dia, dia): [2, -1, -2, 1],
            (1.0, 0.0): [0, 1, 0, -1],
            (dia, -dia): [2, 1, -2, -1],
            None: [0, 1, 0, -1]
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
            None: [3, 3, -3, -3]
        },
        None: {
            (0.0, -1.0): [1, 0, -1, 0],
            (-dia, -dia): [3, -3, -3, 3],
            (-1.0, 0.0): [0, 1, 0, -1],
            (-dia, dia): [3, 3, -3, -3],
            (0.0, 1.0): [1, 0, -1, 0],
            (dia, dia): [3, -3, -3, 3],
            (1.0, 0.0): [0, 1, 0, -1],
            (dia, -dia): [3, 3, -3, -3],
        }
    }

    return table, dia


direct_table = {
    (0.0, -1.0): WireDirect.UP,
    (-dia, -dia): WireDirect.TOP_RIGHT,
    (-1.0, 0.0): WireDirect.RIGHT,
    (-dia, dia): WireDirect.BOTTOM_RIGHT,
    (0.0, 1.0): WireDirect.BOTTOM,
    (dia, dia): WireDirect.BOTTOM_LEFT,
    (1.0, 0.0): WireDirect.LEFT,
    (dia, -dia): WireDirect.TOP_LEFT,
    None: None
}


def reverse_direct(wire_direct: WireDirect):
    if wire_direct == WireDirect.TOP_RIGHT:
        return WireDirect.BOTTOM_LEFT
    if wire_direct == WireDirect.BOTTOM_RIGHT:
        return WireDirect.TOP_LEFT
    if wire_direct == WireDirect.TOP_LEFT:
        return WireDirect.BOTTOM_RIGHT
    if wire_direct == WireDirect.BOTTOM_LEFT:
        return WireDirect.TOP_RIGHT
    if wire_direct == WireDirect.UP:
        return WireDirect.BOTTOM
    if wire_direct == WireDirect.BOTTOM:
        return WireDirect.UP
    if wire_direct == WireDirect.LEFT:
        return WireDirect.RIGHT
    if wire_direct == WireDirect.RIGHT:
        return WireDirect.LEFT
