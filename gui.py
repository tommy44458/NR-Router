import math

import matplotlib.path as mplPath
import numpy as np

from config import ROUTER_CONFIG
from node.electrode import Electrode


def get_gui_result_per_wire(electrode: Electrode, electrode_shape_library: dict, combined_id: int) -> str:
    """Get GUI result (pin mapped) per wire.

    Args:
        electrode (Electrode): electrode
        electrode_shape_library (dict): electrode shape library
        combined_id (int): combined id

    Returns:
        str: GUI result
    """
    ret = ''
    x = int((electrode.real_x + 628) / ROUTER_CONFIG.ELECTRODE_SIZE)
    y = int((electrode.real_y - 12260) / ROUTER_CONFIG.ELECTRODE_SIZE)
    pin_x = round(electrode.routing_wire[len(electrode.routing_wire) - 1].end_x / ROUTER_CONFIG.CONTACT_PAD_GAP)
    pin_y = electrode.routing_wire[len(electrode.routing_wire) - 1].end_y

    if pin_y >= 56896:
        pin_y -= 56896
        pin_y /= ROUTER_CONFIG.CONTACT_PAD_GAP
        pin_y = round(pin_y)
        pin_y += 4
    else:
        pin_y /= ROUTER_CONFIG.CONTACT_PAD_GAP
        pin_y = round(pin_y)

    # match gui design pattern
    pin_number = 0
    if pin_y == 0:
        pin_number = 97 + pin_x
    elif pin_y == 1:
        pin_number = 96 - pin_x
    elif pin_y == 2:
        pin_number = 225 + pin_x
    elif pin_y == 3:
        pin_number = 224 - pin_x
        if pin_x < 8:
            pin_number += 1
        elif pin_x < 16:
            pin_number += 2
        elif pin_x < 24:
            pin_number += 3
        else:
            pin_number += 4
    elif pin_y == 4:
        pin_number = 169 + pin_x
        if pin_x > 23:
            pin_number -= 3
        elif pin_x > 15:
            pin_number -= 2
        elif pin_x > 7:
            pin_number -= 1
    elif pin_y == 5:
        pin_number = 168 - pin_x
    elif pin_y == 6:
        if pin_x > 23:
            pin_number = 129 + pin_x
        else:
            pin_number = 41 + pin_x
    elif pin_y == 7:
        pin_number = 40 - pin_x

    if electrode.shape == 'base':
        ret += 'square' + " " + str(x) + " " + str(y) + " " + str(pin_number) + "\n"
    else:
        path = electrode_shape_library[electrode.shape]
        svg = ""
        for i in range(1, len(path), 2):
            point = " L " + str(math.floor((int(path[i][0]) + 60) / ROUTER_CONFIG.ELECTRODE_SIZE))
            if i == 1:
                point = point.replace("L", "M")
            point += " " + str(math.floor((int(path[i][1]) + 60) / ROUTER_CONFIG.ELECTRODE_SIZE))
            svg += point
        elements = svg.split()
        # Process the rest of the elements
        i = 1
        points = []
        while i < len(elements):
            if elements[i] not in ['L', 'M']:
                points.append((float(elements[i]), float(elements[i+1])))
                i += 2
            else:
                i += 1

        points_np = np.array(points)
        path = mplPath.Path(points_np)
        top_left_corners = []

        # Process each point in a grid
        for _x in np.arange(int(points_np[:,0].min()), int(points_np[:,0].max())):
            for _y in np.arange(int(points_np[:,1].min()), int(points_np[:,1].max())):
                # Check if the top-left corner of the grid square is inside the path
                # Add a small offset to include points on the border
                if path.contains_point((_x + 0.1, _y + 0.1)):
                    top_left_corners.append((x + _x, y + _y))

        for _x, _y in top_left_corners:
            ret += 'combine' + " " + str(_x) + " " + str(_y) + " " + str(combined_id) + " " + str(pin_number) + "\n"

    return ret