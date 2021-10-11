import numpy as np
import math
import sys
import os
from ezdxf.addons import r12writer
from operator import itemgetter, attrgetter
from math import atan2,degrees

class Degree():

    def getdegree(x1, y1, x2, y2):
        x=x1-x2
        y=y1-y2
        hypotenuse = math.sqrt(x**2+y**2)
        if hypotenuse == 0:
            return(0,1)
        sin = x/hypotenuse
        cos = y/hypotenuse
        return (sin,cos)

    def inner_degree(x1, y1, x2, y2):
        x=x1-x2
        y=y1-y2
        deg=0
        if x==0 and y>0:
            deg = 0
        if x==0 and y<0:
            deg = 180
        if y==0 and x>0:
            deg = 90
        if y==0 and x<0:
            deg = 270
        if x>0 and y>0:
            deg = 360 + math.atan(x/y)*180/math.pi
        elif x<0 and y>0:
            deg = 360 + math.atan(x/y)*180/math.pi
        elif x<0 and y<0:
            deg = 180 + math.atan(x/y)*180/math.pi
        elif x>0 and y<0:
            deg = 180 + math.atan(x/y)*180/math.pi
        return int((deg+405)%360)