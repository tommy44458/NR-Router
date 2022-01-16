import numpy as np
from typing import Any, Optional, Tuple, Union, List, Dict, Callable, NoReturn
import math
import sys
import os
from ezdxf.addons import r12writer
import operator
import math
from functools import reduce
from math import atan2,degrees

from degree import Degree
from electrode import Electrode

class Draw():

    def __init__(self, MaxFlowWithMinCost, min_cost_flow, block2_shift, tile_unit, electrode_wire, regular_width, mini_width):
        self.MaxFlowWithMinCost = MaxFlowWithMinCost
        self.min_cost_flow = min_cost_flow
        self.block2_shift = block2_shift
        self.tile_unit = tile_unit
        self.electrode_wire = electrode_wire
        self.mini_width = mini_width
        self.regular_width = regular_width / 2
        self.line_buffer = self.regular_width * 0.0

    def order_vertex(self, vertex):
        vertex.sort(key=lambda x:(x[0]))
        vertex_left = vertex[0:2]
        vertex_right = vertex[2:4]
        vertex_left.sort(key=lambda x:(x[1]))
        vertex_right.sort(key=lambda x:(x[1]), reverse=True)
        vertex_left.extend(vertex_right)
        return vertex_left

    def draw_orthogonal_path(self, x1, y1, x2, y2, x3, y3, x4, y4, width, connect, dxf):
        #polyline= dxf.polyline(linetype=None)
        position1 = []
        position2 = []
        deg_90_UD = 0
        deg_90_RL = 0
        deg_45 = 0
        # Tan = 82.842712 / 2 #82.842712/2
        Tan = 0.41421356237 * width
        # print('*********************', Tan)
        # if width==50:
        #     Tan=(Tan/2)

        # align because hub axis
        if abs(y3 - y4) != abs(x3 - x4):
            if abs(y3 - y4) < abs(x3 - x4):
                y4 = y3
            else:
                x4 = x3

        degree1 = Degree.getdegree(x1,y1,x2,y2)
        degree2 = Degree.getdegree(x2,y2,x3,y3)
        if x2==x3 and y2==y3:
            return 0
        if x2==x1 and y2==y1:
            return 0

        if y2 == y3:
            degree1 = (1,0)
            degree2 = (1,0)
        elif x2 == x3:
            degree1 = (0,1)
            degree2 = (0,1)

        if y3 == y4 and x2!=x3:
            degree2 = (1,0)
        elif x3 == x4 and y2!=y3:
            degree2 = (0,1)
        # 1/\4
        # 2\/3
        ###
        # 4/\1
        # 3\/2
        #45 angle
        if x2!=x3 and y2!=y3:
            if x2>x3:
                if y2>y3:
                    deg_45=2
                elif y2<y3:
                    deg_45=1
            elif x2<x3:
                if y2>y3:
                    deg_45=3
                elif y2<y3:
                    deg_45=4
        #head
        #tail

        #90 angle
        if (x3 == x4 and y2==y3):
            deg_90_UD = 1
        if (y3 == y4 and x2==x3):
            deg_90_RL = 1
        if y1 == y2 and x2!=x3:
            degree1 = (1,0)
        position_s1 = [x2-width*degree1[1],y2+width*degree1[0],Degree.inner_degree(x2-width*degree1[1],y2+width*degree1[0],(x2+x3)/2,(y2+y3)/2)]
        position_s2 = [x2+width*degree1[1],y2-width*degree1[0],Degree.inner_degree(x2-width*degree1[1],y2+width*degree1[0],(x2+x3)/2,(y2+y3)/2)]
        # if width==50:
        #     if x1!=x2 and y1!=y2:
        #         if x2==x3:
        #             if x1>x2:
        #                 if y2>y3:
        #                     position_s1=[x2+width,y2,1]
        #                     position_s2=[x2-width,y2,2]
        #                 elif y2<y3:
        #                     position_s1=[x2+width,y2,1]
        #                     position_s2=[x2-width,y2,2]
        #             elif x1<x2:
        #                 if y2>y3:
        #                     position_s1=[x2-width,y2,1]
        #                     position_s2=[x2+width,y2,2]
        #                 elif y2<y3:
        #                     position_s1=[x2-width,y2,1]
        #                     position_s2=[x2+width,y2,2]
        #         elif y2==y3:
        #             if y1>y2:
        #                 if x2>x3:
        #                     position_s1=[x2,y2-width,1]
        #                     position_s2=[x2,y2+width,2]
        #                 elif x2<x3:
        #                     position_s1=[x2,y2-width,1]
        #                     position_s2=[x2,y2+width,2]
        #             elif y1<y2:
        #                 if x2>x3:
        #                     position_s1=[x2,y2+width,1]
        #                     position_s2=[x2,y2-width,2]
        #                 elif x2<x3:
        #                     position_s1=[x2,y2+width,1]
        #                     position_s2=[x2,y2-width,2]
        if abs(position_s1[2]-position_s2[2])>90:
            if min(position_s1[2],position_s2[2]) == position_s1[2]:
                position_s2[2]-=360
            else:
                position_s1[2]-=360

        if deg_45!=0:# and connect!=1:
            #dxf.add_polyline_path([(x2+width/2,y2+width/2),(x2-width/2,y2+width/2),(x2+width/2,y2-width/2),(x2-width/2,y2-width/2)])

            if deg_45==1:
                if x1==x2:
                    position_s1[0]=x2-width
                    position_s1[1]=y2-Tan
                    position_s2[0]=x2+width
                    position_s2[1]=y2+Tan
                elif y1==y2:
                    position_s1[0]=x2+Tan
                    position_s1[1]=y2+width
                    position_s2[0]=x2-Tan
                    position_s2[1]=y2-width
            elif deg_45==2:
                if x1==x2:
                    position_s1[0]=x2-width
                    position_s1[1]=y2+Tan
                    position_s2[0]=x2+width
                    position_s2[1]=y2-Tan
                elif y1==y2:
                    position_s1[0]=x2+Tan
                    position_s1[1]=y2-width
                    position_s2[0]=x2-Tan
                    position_s2[1]=y2+width
            elif deg_45==3:
                if x1==x2:
                    position_s1[0]=x2+width
                    position_s1[1]=y2+Tan
                    position_s2[0]=x2-width
                    position_s2[1]=y2-Tan
                elif y1==y2:
                    position_s1[0]=x2-Tan
                    position_s1[1]=y2-width
                    position_s2[0]=x2+Tan
                    position_s2[1]=y2+width
            elif deg_45==4:
                if x1==x2:
                    position_s1[0]=x2+width
                    position_s1[1]=y2-Tan
                    position_s2[0]=x2-width
                    position_s2[1]=y2+Tan
                elif y1==y2:
                    position_s1[0]=x2-Tan
                    position_s1[1]=y2+width
                    position_s2[0]=x2+Tan
                    position_s2[1]=y2-width
        elif x1!=x2 and y1!=y2:#and width!=50:
            if x1>x2:
                if y1>y2:
                    if y2==y3:
                        position_s1[0]=x2-Tan
                        position_s1[1]=y2+width
                        position_s2[0]=x2+Tan
                        position_s2[1]=y2-width
                    elif x2==x3:
                        position_s1[0]=x2+width
                        position_s1[1]=y2-Tan
                        position_s2[0]=x2-width
                        position_s2[1]=y2+Tan
                elif y1<y2:
                    if y2==y3:
                        position_s1[0]=x2-Tan
                        position_s1[1]=y2-width
                        position_s2[0]=x2+Tan
                        position_s2[1]=y2+width
                    elif x2==x3:
                        position_s1[0]=x2+width
                        position_s1[1]=y2+Tan
                        position_s2[0]=x2-width
                        position_s2[1]=y2-Tan
            elif x1<x2:
                if y1>y2:
                    if y2==y3:
                        position_s1[0]=x2+Tan
                        position_s1[1]=y2+width
                        position_s2[0]=x2-Tan
                        position_s2[1]=y2-width
                    elif x2==x3:
                        position_s1[0]=x2-width
                        position_s1[1]=y2-Tan
                        position_s2[0]=x2+width
                        position_s2[1]=y2+Tan
                elif y1<y2:
                    if y2==y3:
                        position_s1[0]=x2+Tan
                        position_s1[1]=y2-width
                        position_s2[0]=x2-Tan
                        position_s2[1]=y2+width
                    elif x2==x3:
                        position_s1[0]=x2-width
                        position_s1[1]=y2+Tan
                        position_s2[0]=x2+width
                        position_s2[1]=y2-Tan
        position1.append(position_s1)
        position1.append(position_s2)
        
        # position1.sort(key=lambda k: [k[2]])
        position_e1 = [x3+width*degree2[1],y3-width*degree2[0],Degree.inner_degree(x3+width*degree2[1],y3-width*degree2[0],(x2+x3)/2,(y2+y3)/2)]
        position_e2	= [x3-width*degree2[1],y3+width*degree2[0],Degree.inner_degree(x3-width*degree2[1],y3+width*degree2[0],(x2+x3)/2,(y2+y3)/2)]
        if deg_45!=0 :

            # dxf.add_polyline_path([(x3,y3+width),(x3-width,y3),(x3+width,y3),(x3,y3-width)])
            # print('***************', [(x3,y3+width),(x3-width,y3),(x3+width,y3),(x3,y3-width)])
            # print('***************', [(x3+(width/2),y3+(width*Tan/100)),(x3+(width/2),y3+(width*Tan/100)),(x3+(width/2),y3-(width*Tan/100)),(x3-(width/2),y3-(width*Tan/100))])
            # dxf.add_polyline_path([(x3+(width/2),y3+(width*Tan/100)),(x3+(width/2),y3+(width*Tan/100)),(x3+(width/2),y3-(width*Tan/100)),(x3-(width/2),y3-(width*Tan/100))])

            if deg_45==1:
                if x3==x4:
                    position_e1[0]=x3+width
                    position_e1[1]=y3+Tan
                    position_e2[0]=x3-width
                    position_e2[1]=y3-Tan
                elif y3==y4:
                    position_e1[0]=x3-Tan
                    position_e1[1]=y3-width
                    position_e2[0]=x3+Tan
                    position_e2[1]=y3+width
            elif deg_45==2:
                if x3==x4:
                    position_e1[0]=x3+width
                    position_e1[1]=y3-Tan
                    position_e2[0]=x3-width
                    position_e2[1]=y3+Tan
                elif y3==y4:
                    position_e1[0]=x3-Tan
                    position_e1[1]=y3+width
                    position_e2[0]=x3+Tan
                    position_e2[1]=y3-width
            elif deg_45==3:
                if x3==x4:
                    position_e1[0]=x3-width
                    position_e1[1]=y3-Tan
                    position_e2[0]=x3+width
                    position_e2[1]=y3+Tan
                elif y3==y4:
                    position_e1[0]=x3+Tan
                    position_e1[1]=y3+width
                    position_e2[0]=x3-Tan
                    position_e2[1]=y3-width
            elif deg_45==4:
                if x3==x4:
                    position_e1[0]=x3-width
                    position_e1[1]=y3+Tan
                    position_e2[0]=x3+width
                    position_e2[1]=y3-Tan
                elif y3==y4:
                    position_e1[0]=x3+Tan
                    position_e1[1]=y3-width
                    position_e2[0]=x3-Tan
                    position_e2[1]=y3+width
        elif x3!=x4 and y3!=y4:# and width!=50:
            if x3>x4:
                if y3>y4:
                    if y2==y3:
                        position_e1[0]=x3+Tan
                        position_e1[1]=y3-width
                        position_e2[0]=x3-Tan
                        position_e2[1]=y3+width
                    elif x2==x3:
                        position_e1[0]=x3-width
                        position_e1[1]=y3+Tan
                        position_e2[0]=x3+width
                        position_e2[1]=y3-Tan
                elif y3<y4:
                    if y2==y3:
                        position_e1[0]=x3+Tan
                        position_e1[1]=y3+width
                        position_e2[0]=x3-Tan
                        position_e2[1]=y3-width
                    elif x2==x3:
                        position_e1[0]=x3-width
                        position_e1[1]=y3-Tan
                        position_e2[0]=x3+width
                        position_e2[1]=y3+Tan
            elif x3<x4:
                if y3>y4:
                    if y2==y3:
                        position_e1[0]=x3-Tan
                        position_e1[1]=y3-width
                        position_e2[0]=x3+Tan
                        position_e2[1]=y3+width
                    elif x2==x3:
                        position_e1[0]=x3+width
                        position_e1[1]=y3+Tan
                        position_e2[0]=x3-width
                        position_e2[1]=y3-Tan
                elif y3<y4:
                    if y2==y3:
                        position_e1[0]=x3-Tan
                        position_e1[1]=y3+width
                        position_e2[0]=x3+Tan
                        position_e2[1]=y3-width
                    elif x2==x3:
                        position_e1[0]=x3+width
                        position_e1[1]=y3-Tan
                        position_e2[0]=x3-width
                        position_e2[1]=y3+Tan

        if deg_90_UD==1:
            if x2>x3:
                position_e1[0]-=width
                position_e2[0]-=width
            elif x2<x3:
                position_e1[0]+=width
                position_e2[0]+=width

        if deg_90_RL==1:
            if y2>y3:
                position_e1[1]-=width
                position_e2[1]-=width
            elif y2<y3:
                position_e1[1]+=width
                position_e2[1]+=width		
        # if width==50:
        #     if x2!=x3 and y2!=y3:
        #         if x3==x4:
        #             position_e1[0]=x3+70.7
        #             position_e1[1]=y3
        #             position_e2[0]=x3-70.7
        #             position_e2[1]=y3
        #         elif y3==y4:
        #             position_e1[0]=x3
        #             position_e1[1]=y3+70.7
        #             position_e2[0]=x3
        #             position_e2[1]=y3-70.7
        if abs(position_e1[2]-position_e2[2])>90:
            if min(position_e1[2],position_e2[2]) == position_e1[2]:
                position_e2[2]-=360
            else:
                position_e1[2]-=360
        position2.append(position_e1)
        position2.append(position_e2)
        vertex = [(position1[0][0],position1[0][1]), (position1[1][0],position1[1][1]), (position2[0][0],position2[0][1]), (position2[1][0],position2[1][1])]
        vertex_order = self.order_vertex(vertex)
        dxf.add_polyline_path(vertex_order)
        
    def draw_path(self, x1,y1,x2,y2,x3,y3,x4,y4,width,connect,dxf):
        y1 = -1*y1
        y2 = -1*y2
        y3 = -1*y3
        y4 = -1*y4
        # if width==self.mini_width:
        #     dxf.add_arc(center=(x3,y3),radius=100,start=0, end=359)
        self.draw_orthogonal_path(x1,y1,x2,y2,x3,y3,x4,y4,width,connect,dxf)
        
    def draw_start(self, x1,y1,x2,y2,x3,y3,width,dxf):
        # if x1 == x2 and y1 == y2:
        #     return 0
        y1 = -y1
        y2 = -y2
        y3 = -y3
        degree1 = Degree.getdegree(x1,y1,x2,y2)
        Tan = 0.41421356237 * width
        #/
        #|
        if x1 < x2 and y1 < y2:
            x1 -= self.line_buffer
            y1 -= self.line_buffer
        #|
        #\
        elif x1 < x2 and y1 > y2:
            x1 -= self.line_buffer
            y1 += self.line_buffer
        #\
        # |
        elif x1 > x2 and y1 < y2:
            x1 += self.line_buffer
            y1 -= self.line_buffer
        # |
        #/
        elif x1 > x2 and y1 > y2:
            x1 += self.line_buffer
            y1 += self.line_buffer
        elif x1 == x2 and y1 < y2:
            y1 -= self.line_buffer
        elif x1 == x2 and y1 > y2:
            y1 += self.line_buffer
        elif y1 == y2 and x1 < x2:
            x1 -= self.line_buffer
        elif y1 == y2 and x1 > x2:
            x1 += self.line_buffer
        S1=(x1-width*degree1[1],y1+width*degree1[0])
        S2=(x1+width*degree1[1],y1-width*degree1[0])
        # 有角度
        if x1 != x2 and y1 != y2:
            S1=(x1-width*degree1[1],y1+width*degree1[0])
            S2=(x1+width*degree1[1],y1-width*degree1[0])
            if x2!=x3 and y2!=y3:
                E1=(x2-width*degree1[1],y2+width*degree1[0])
                E2=(x2+width*degree1[1],y2-width*degree1[0])
            elif x2==x3 and y2==y3:
                return 0
            elif x2==x3:
                if x1>x2:
                    if y2>y3:
                        E1=(x2+width,y2-Tan)
                        E2=(x2-width,y2+Tan)
                    elif y2<y3:
                        E1=(x2+width,y2+Tan)
                        E2=(x2-width,y2-Tan)
                elif x1<x2:
                    if y2>y3:
                        E1=(x2-width,y2-Tan)
                        E2=(x2+width,y2+Tan)
                    elif y2<y3:
                        E1=(x2-width,y2+Tan)
                        E2=(x2+width,y2-Tan)
            elif y2==y3:
                if y1>y2:
                    if x2>x3:
                        E1=(x2-Tan,y2+width)
                        E2=(x2+Tan,y2-width)
                    elif x2<x3:
                        E1=(x2+Tan,y2+width)
                        E2=(x2-Tan,y2-width)
                elif y1<y2:
                    if x2>x3:
                        E1=(x2-Tan,y2-width)
                        E2=(x2+Tan,y2+width)
                    elif x2<x3:
                        E1=(x2+Tan,y2-width)
                        E2=(x2-Tan,y2+width)
            vertex = [S1, S2, E1, E2]
            vertex_order = self.order_vertex(vertex)
            dxf.add_polyline_path(vertex_order)
            # dxf.add_polyline_path(	[S1,S2,E1,E2])
            # dxf.add_polyline_path(	[S1,S2,E2,E1])
        # 垂直 水平
        else:
            # 垂直
            if x1 == x2:
                if y3 > y2:
                    if x2 > x3:
                        E1=(x2-width,y2-Tan)
                        E2=(x2+width,y2+Tan)
                    elif x2 < x3:
                        E1=(x2-width,y2+Tan)
                        E2=(x2+width,y2-Tan)
                    else:
                        E1=(x2-width,y2)
                        E2=(x2+width,y2)
                else:
                    if x2 > x3:
                        E1=(x2-width,y2+Tan)
                        E2=(x2+width,y2-Tan)
                    elif x2 < x3:
                        E1=(x2-width,y2-Tan)
                        E2=(x2+width,y2+Tan)
                    else:
                        E1=(x2-width,y2)
                        E2=(x2+width,y2)
            # 水平
            else:
                if y2 > y3:
                    E1=(x2-Tan,y2-width)
                    E2=(x2+Tan,y2+width)
                elif y2 < y3:
                    E1=(x2+Tan,y2-width)
                    E2=(x2-Tan,y2+width)
                else:
                    E1=(x2,y2-width)
                    E2=(x2,y2+width)
            vertex = [S1, S2, E1, E2]
            vertex_order = self.order_vertex(vertex)
            dxf.add_polyline_path(vertex_order)

    def draw_end(self, x1,y1,x2,y2,x3,y3,width,dxf,connect):
        y1 = -y1
        y2 = -y2
        y3 = -y3
        # align to agr 90 (only 90 or 45)
        if abs(y2 - y3) != abs(x2 - x3):
            if abs(y2 - y3) < abs(x2 - x3):
                y3 = y2
            else:
                x3 = x2
        position1 = []
        position2 = []
        degree1 = Degree.getdegree(x1,y1,x2,y2)
        degree2 = Degree.getdegree(x2,y2,x3,y3)
        # if degree1[0] == degree2[0] and degree1[1] == degree2[1] and width==50:
        #     dxf.add_polyline_path(	[(x3-width,y3),
        #                     (x3,y3+width),
        #                     (x3,y3-width),
        #                     (x3+width,y3)])
        if x2==x3 and y2==y3:
            return 0
        if x2==x1 and y2==y1:
            return 0
        if y2 == y3:
            degree1 = (1,0)
            degree2 = (1,0)
        elif x2 == x3:
            degree1 = (0,1)
            degree2 = (0,1)
        
        # if abs(y2 - y3) != abs(x2 - x3):

        position_s1 = [x2-width*degree1[1],y2+width*degree1[0],Degree.inner_degree(x2-width*degree1[1],y2+width*degree1[0],(x2+x3)/2,(y2+y3)/2)]
        position_s2 = [x2+width*degree1[1],y2-width*degree1[0],Degree.inner_degree(x2-width*degree1[1],y2+width*degree1[0],(x2+x3)/2,(y2+y3)/2)]
        deg_45=0
        # 4/\1
        # 3\/2
        Tan = 0.41421356237 * width
        if x2!=x3 and y2!=y3:
            if x2>x3:
                if y2>y3:
                    deg_45=2
                elif y2<y3:
                    deg_45=1
            elif x2<x3:
                if y2>y3:
                    deg_45=3
                elif y2<y3:
                    deg_45=4
        if deg_45!=0:
            # dxf.add_polyline_path([(x2,y2+width),(x2-width,y2),(x2+width,y2),(x2,y2-width)])
            if deg_45==1:
                if x1==x2:
                    position_s1[0]=x2-width
                    position_s1[1]=y2-Tan
                    position_s2[0]=x2+width
                    position_s2[1]=y2+Tan
                elif y1==y2:
                    position_s1[0]=x2+Tan
                    position_s1[1]=y2+width
                    position_s2[0]=x2-Tan
                    position_s2[1]=y2-width
            elif deg_45==2:
                if x1==x2:
                    position_s1[0]=x2-width
                    position_s1[1]=y2+Tan
                    position_s2[0]=x2+width
                    position_s2[1]=y2-Tan
                elif y1==y2:
                    position_s1[0]=x2+Tan
                    position_s1[1]=y2-width
                    position_s2[0]=x2-Tan
                    position_s2[1]=y2+width
            elif deg_45==3:
                if x1==x2:
                    position_s1[0]=x2+width
                    position_s1[1]=y2+Tan
                    position_s2[0]=x2-width
                    position_s2[1]=y2-Tan
                elif y1==y2:
                    position_s1[0]=x2-Tan
                    position_s1[1]=y2-width
                    position_s2[0]=x2+Tan
                    position_s2[1]=y2+width
            elif deg_45==4:
                if x1==x2:
                    position_s1[0]=x2+width
                    position_s1[1]=y2-Tan
                    position_s2[0]=x2-width
                    position_s2[1]=y2+Tan
                elif y1==y2:
                    position_s1[0]=x2-Tan
                    position_s1[1]=y2+width
                    position_s2[0]=x2+Tan
                    position_s2[1]=y2-width
        elif x1!=x2 and y1!=y2:
            if x1>x2:
                if y1>y2:
                    if y2==y3:
                        position_s1[0]=x2-Tan
                        position_s1[1]=y2+width
                        position_s2[0]=x2+Tan
                        position_s2[1]=y2-width
                    elif x2==x3:
                        position_s1[0]=x2+width
                        position_s1[1]=y2-Tan
                        position_s2[0]=x2-width
                        position_s2[1]=y2+Tan
                elif y1<y2:
                    if y2==y3:
                        position_s1[0]=x2-Tan
                        position_s1[1]=y2-width
                        position_s2[0]=x2+Tan
                        position_s2[1]=y2+Tan
                    elif x2==x3:
                        position_s1[0]=x2+width
                        position_s1[1]=y2+Tan
                        position_s2[0]=x2-width
                        position_s2[1]=y2-Tan
            elif x1<x2:
                if y1>y2:
                    if y2==y3:
                        position_s1[0]=x2+Tan
                        position_s1[1]=y2+width
                        position_s2[0]=x2-Tan
                        position_s2[1]=y2-width
                    elif x2==x3:
                        position_s1[0]=x2-width
                        position_s1[1]=y2-Tan
                        position_s2[0]=x2+width
                        position_s2[1]=y2+Tan
                elif y1<y2:
                    if y2==y3:
                        position_s1[0]=x2+Tan
                        position_s1[1]=y2-width
                        position_s2[0]=x2-Tan
                        position_s2[1]=y2+width
                    elif x2==x3:
                        position_s1[0]=x2-width
                        position_s1[1]=y2+Tan
                        position_s2[0]=x2+width
                        position_s2[1]=y2-Tan

        if abs(position_s1[2]-position_s2[2])>90:
            if min(position_s1[2],position_s2[2]) == position_s1[2]:
                position_s2[2]-=360
            else:
                position_s1[2]-=360
        position1.append(position_s1)
        position1.append(position_s2)
        position1.sort(key=lambda k: [k[2]])
        position_e1 = [x3+width*degree2[1],y3-width*degree2[0],Degree.inner_degree(x3+width*degree2[1],y3-width*degree2[0],(x2+x3)/2,(y2+y3)/2)]
        position_e2	= [x3-width*degree2[1],y3+width*degree2[0],Degree.inner_degree(x3-width*degree2[1],y3+width*degree2[0],(x2+x3)/2,(y2+y3)/2)]
        if abs(position_e1[2]-position_e2[2])>90:
            if min(position_e1[2],position_e2[2]) == position_e1[2]:
                position_e2[2]-=360
            else:
                position_e1[2]-=360
        position2.append(position_e1)
        position2.append(position_e2)

        vertex = [(position1[0][0],position1[0][1]), (position1[1][0],position1[1][1]), (position2[0][0],position2[0][1]), (position2[1][0],position2[1][1])]
        vertex_order = self.order_vertex(vertex)
        dxf.add_polyline_path(vertex_order)
        
    def draw_contact_pads(self, contactpads, dxf):
        for i in range(len(contactpads)):
            dxf.add_circle(center=(contactpads[i][0], -contactpads[i][1]), radius = 750.0)
            
    def draw_electrodes(self, electrodes: list, shape_lib: dict, dxf):
        for elec in electrodes:
            shape = elec[0]
            x = elec[1]
            y = -elec[2]
            vertices = []
            for shape_p in shape_lib[shape]:
                vertices.append((x + shape_p[0], y - shape_p[1]))
            dxf.add_polyline_path(vertices)
            
    def draw_grid(self, start_x, start_y, unit_length, grids_x, grids_y, dxf):
        for i in range(grids_x):
            dxf.add_line((start_x+unit_length*i, -start_y),(start_x+unit_length*i,-(start_y+unit_length*(grids_y-1))))
        for i in range(grids_y):
            dxf.add_line((start_x, -(start_y+unit_length*i)),(start_x+unit_length*(grids_x-1),-(start_y+unit_length*i)))

    def draw_pseudo_node(self, grids, dxf):
        width = 60
        num = 0
        for i in range(len(grids)):
            for j in range(len(grids[i])):
                if grids[i][j].electrode_index >= 0:
                    # print(girds[i][j].to_dict())
                    x = grids[i][j].real_x
                    y = -grids[i][j].real_y
                    # dxf.add_edge_path().add_ellipse((girds[i][j].real_x, -girds[i][j].real_y), major_axis=(0, 10), ratio=0.5)
                    dxf.add_polyline_path([(x, y-width), (x+width, y), (x, y+width), (x-width, y)])
                    num += 1
                    # dxf.add_circle(center=(girds[i][j].real_x, -girds[i][j].real_y), radius = 20.0, dxfattribs={'color': color})
        print('grid num: ', num)

    def draw_pseudo_node_corner(self, grids, dxf):
        width = 60
        for i in range(len(grids)):
            for j in range(len(grids[i])):
                if grids[i][j].electrode_index >= 0 and grids[i][j].corner:
                    # print(girds[i][j].to_dict())
                    x = grids[i][j].real_x
                    y = -grids[i][j].real_y
                    # dxf.add_edge_path().add_ellipse((girds[i][j].real_x, -girds[i][j].real_y), major_axis=(0, 10), ratio=0.5)
                    dxf.add_polyline_path([(x, y-width), (x+width, y), (x, y+width), (x-width, y)])

    def draw_all_path(self, dxf, grids2):
        MaxFlowWithMinCost = self.MaxFlowWithMinCost
        min_cost_flow = self.min_cost_flow
        block2_shift = self.block2_shift
        tile_unit = self.tile_unit
        electrode_wire = self.electrode_wire

        connect = 0
        if MaxFlowWithMinCost == min_cost_flow.OPTIMAL:
            for i in range(len(electrode_wire)):
                #tune path start 
                ## reduce change way
                if len(electrode_wire[i]) == 0:
                    return False
                
                ## BUG 一些線斷消失
                # # 有起始線
                # abs(electrode_wire[i][0].start_x - electrode_wire[i][0].end_x) != 0
                # abs(electrode_wire[i][0].start_y - electrode_wire[i][0].end_y) != 0
                # # 起始線與下一條線有轉彎
                # (np.sign(electrode_wire[i][0].start_x - electrode_wire[i][0].end_x) != np.sign(electrode_wire[i][1].start_x-electrode_wire[i][1].end_x))
                # # 起始線下下條線為垂直線
                # (electrode_wire[i][2].start_x == electrode_wire[i][2].end_x)

                # if abs(electrode_wire[i][0].start_x-electrode_wire[i][0].end_x)!=0 and abs(electrode_wire[i][0].start_y-electrode_wire[i][0].end_y)!=0 and (np.sign(electrode_wire[i][0].start_x-electrode_wire[i][0].end_x)!=np.sign(electrode_wire[i][1].start_x-electrode_wire[i][1].end_x)) and (electrode_wire[i][2].start_x==electrode_wire[i][2].end_x):
                #     electrode_wire[i][0].end_x = electrode_wire[i][2].start_x
                #     electrode_wire[i][2].start_y = electrode_wire[i][0].start_y + abs(electrode_wire[i][2].start_x-electrode_wire[i][0].start_x) * np.sign(electrode_wire[i][2].start_y-electrode_wire[i][0].start_y)
                #     electrode_wire[i][0].end_y = electrode_wire[i][2].start_y
                #     del electrode_wire[i][1]
                ## BUG 一些線斷消失

                # if abs(electrode_wire[i][1].start_x-electrode_wire[i][1].end_x)!=abs(electrode_wire[i][1].start_y-electrode_wire[i][1].end_y) and abs(electrode_wire[i][1].start_x-electrode_wire[i][1].end_x)!=0 and abs(electrode_wire[i][1].start_y-electrode_wire[i][1].end_y)!=0:
                #     if abs(electrode_wire[i][2].end_x-electrode_wire[i][1].start_x)>abs(electrode_wire[i][2].end_y-electrode_wire[i][1].start_y):
                #         electrode_wire[i][1].end_x = electrode_wire[i][1].start_x+abs(electrode_wire[i][2].end_y-electrode_wire[i][1].start_y)*np.sign(electrode_wire[i][2].end_x-electrode_wire[i][1].start_x)
                #         electrode_wire[i][1].end_y = electrode_wire[i][2].end_y
                #         electrode_wire[i][2].start_x = electrode_wire[i][1].start_x+abs(electrode_wire[i][2].end_y-electrode_wire[i][1].start_y)*np.sign(electrode_wire[i][2].end_x-electrode_wire[i][1].start_x)
                #         electrode_wire[i][2].start_y = electrode_wire[i][2].end_y
                #     else:
                #         electrode_wire[i][1].end_x = electrode_wire[i][2].end_x
                #         electrode_wire[i][1].end_y = electrode_wire[i][1].start_y+abs(electrode_wire[i][2].end_x-electrode_wire[i][1].start_x)*np.sign(electrode_wire[i][2].end_y-electrode_wire[i][1].start_y)
                #         electrode_wire[i][2].start_x = electrode_wire[i][2].end_x
                #         electrode_wire[i][2].start_y = electrode_wire[i][1].start_y+abs(electrode_wire[i][2].end_x-electrode_wire[i][1].start_x)*np.sign(electrode_wire[i][2].end_y-electrode_wire[i][1].start_y)

                # for j in range(len(electrode_wire[i])-2):
                #     if np.sign(electrode_wire[i][j].start_x-electrode_wire[i][j].end_x)!=np.sign(electrode_wire[i][j+1].start_x-electrode_wire[i][j+1].end_x) and (electrode_wire[i][j].start_x-electrode_wire[i][j].end_x)!=0:
                #         if abs(electrode_wire[i][j+1].end_x-electrode_wire[i][j].start_x)>abs(electrode_wire[i][j+1].end_y-electrode_wire[i][j].start_y):
                #             electrode_wire[i][j].end_x = electrode_wire[i][j].start_x+abs(electrode_wire[i][j+1].end_y-electrode_wire[i][j].start_y)*np.sign(electrode_wire[i][j+1].end_x-electrode_wire[i][j].start_x)
                #             electrode_wire[i][j].end_y = electrode_wire[i][j+1].end_y
                #             electrode_wire[i][j+1].start_x = electrode_wire[i][j].start_x+abs(electrode_wire[i][j+1].end_y-electrode_wire[i][j].start_y)*np.sign(electrode_wire[i][j+1].end_x-electrode_wire[i][j].start_x)
                #             electrode_wire[i][j+1].start_y = electrode_wire[i][j+1].end_y
                #         else:
                #             electrode_wire[i][j].end_x = electrode_wire[i][j+1].end_x
                #             electrode_wire[i][j].end_y = electrode_wire[i][j].start_y+abs(electrode_wire[i][j+1].end_x-electrode_wire[i][j].start_x)*np.sign(electrode_wire[i][j+1].end_y-electrode_wire[i][j].start_y)
                #             electrode_wire[i][j+1].start_x = electrode_wire[i][j+1].end_x
                #             electrode_wire[i][j+1].start_y = electrode_wire[i][j].start_y+abs(electrode_wire[i][j+1].end_x-electrode_wire[i][j].start_x)*np.sign(electrode_wire[i][j+1].end_y-electrode_wire[i][j].start_y)

                # for j in range(len(electrode_wire[i])-2):	
                #     if abs(electrode_wire[i][j].start_x-electrode_wire[i][j].end_x) == 0 and abs(electrode_wire[i][j+1].start_y-electrode_wire[i][j+1].end_y) == 0:
                #         electrode_wire[i][j].end_x = electrode_wire[i][j].start_x+abs(electrode_wire[i][j].end_y-electrode_wire[i][j].start_y)*np.sign(electrode_wire[i][j+1].end_x-electrode_wire[i][j+1].start_x)
                #         electrode_wire[i][j+1].start_x = electrode_wire[i][j].end_x
                #     if abs(electrode_wire[i][j].start_y-electrode_wire[i][j].end_y) == 0 and abs(electrode_wire[i][j+1].start_x-electrode_wire[i][j+1].end_x) == 0:
                #         electrode_wire[i][j].end_y = electrode_wire[i][j].start_y+abs(electrode_wire[i][j].end_x-electrode_wire[i][j].start_x)*np.sign(electrode_wire[i][j+1].end_y-electrode_wire[i][j+1].start_y)
                #         electrode_wire[i][j+1].start_y = electrode_wire[i][j].end_y

                # for j in range(len(electrode_wire[i])):
                #     if (electrode_wire[i][j].start_x-electrode_wire[i][j].end_x)==0 and abs(electrode_wire[i][j].start_y-electrode_wire[i][j].end_y)==250:
                #         #dxf.add_circle(center=(electrode_wire[i][j].start_x, -electrode_wire[i][j].start_y), radius = 250.0)
                #         if np.sign(electrode_wire[i][j-1].start_x-electrode_wire[i][j-1].end_x)*np.sign(electrode_wire[i][j+1].start_x-electrode_wire[i][j+1].end_x)==-1:
                #             #dxf.add_circle(center=(electrode_wire[i][j].start_x, -electrode_wire[i][j].start_y), radius = 250.0)
                #             electrode_wire[i][j-1].end_y = electrode_wire[i][j].start_y+abs(electrode_wire[i][j+1].end_x-electrode_wire[i][j].start_x)*np.sign(electrode_wire[i][j].start_y-electrode_wire[i][j].end_y)
                #             electrode_wire[i][j].start_y = electrode_wire[i][j-1].end_y
                #             electrode_wire[i][j-1].end_x = electrode_wire[i][j+1].end_x
                #             electrode_wire[i][j].start_x = electrode_wire[i][j+1].end_x
                #             electrode_wire[i][j].end_x = electrode_wire[i][j+1].end_x
                #             electrode_wire[i][j+1].start_x = electrode_wire[i][j+1].end_x
                #         if electrode_wire[i][j-1].start_x!=electrode_wire[i][j-1].end_x and electrode_wire[i][j+1].start_x!=electrode_wire[i][j+1].end_x:
                #             #dxf.add_circle(center=(electrode_wire[i][j].start_x, -electrode_wire[i][j].start_y), radius = 250.0)
                #             electrode_wire[i][j-1].end_x = electrode_wire[i][j+1].end_x
                #             electrode_wire[i][j-1].end_y = electrode_wire[i][j-1].end_y+abs(electrode_wire[i][j+1].end_x-electrode_wire[i][j+1].start_x)*np.sign(electrode_wire[i][j+1].end_y-electrode_wire[i][j+1].start_y)
                #             electrode_wire[i][j].start_x = electrode_wire[i][j-1].end_x
                #             electrode_wire[i][j].start_y = electrode_wire[i][j-1].end_y
                #             electrode_wire[i][j].end_x = electrode_wire[i][j+1].end_x
                #             electrode_wire[i][j+1].start_x = electrode_wire[i][j+1].end_x

                #     if electrode_wire[i][j].end_y > block2_shift[1] and electrode_wire[i][j].end_y < block2_shift[1]+46000:
                #         S_grid_x = (electrode_wire[i][j].start_x-block2_shift[0])//tile_unit
                #         S_grid_y = (electrode_wire[i][j].start_y-block2_shift[1])//tile_unit
                #         T_grid_x = (electrode_wire[i][j].end_x-block2_shift[0])//tile_unit
                #         T_grid_y = (electrode_wire[i][j].end_y-block2_shift[1])//tile_unit
                #         grids2[S_grid_x,S_grid_y].flow=1
                #         grids2[T_grid_x,T_grid_y].flow=1

                # #|      |    j-1        |       \   j+1
                # #\  ->  |    j     or   \  ->    |  j
                # # |      \   j+1         |       |  j-1

                # for j in range(3,len(electrode_wire[i])):		
                #     if electrode_wire[i][j].end_y > block2_shift[1]+tile_unit and electrode_wire[i][j].end_y < block2_shift[1]+46000-tile_unit:
                #         if electrode_wire[i][j-1].start_x==electrode_wire[i][j-1].end_x and abs(electrode_wire[i][j].start_x-electrode_wire[i][j].end_x)==abs(electrode_wire[i][j].start_y-electrode_wire[i][j].end_y):
                #             check_grid_x = (electrode_wire[i][j].start_x-block2_shift[0])//tile_unit
                #             check_grid_y = (electrode_wire[i][j].end_y-block2_shift[1])//tile_unit
                #             if grids2[check_grid_x,check_grid_y].flow == 0 and grids2[check_grid_x,check_grid_y].safe_distance==0 and grids2[check_grid_x,check_grid_y].safe_distance2==0:
                #                 k=1
                #                 no_path=0
                #                 while j+k < len(electrode_wire[i]) and electrode_wire[i][j+k].start_x!=electrode_wire[i][j+k].end_x:
                #                     check_grid_x = (electrode_wire[i][j+k].start_x-block2_shift[0])//tile_unit
                #                     check_grid_y = (electrode_wire[i][j+k].end_y-block2_shift[1])//tile_unit
                #                     try:
                #                         if grids2[check_grid_x,check_grid_y].flow != 0:
                #                         # or grids2[check_grid_x,check_grid_y].safe_distance2==1 or grids2[check_grid_x,check_grid_y].safe_distance==1:
                #                             no_path=1
                #                         if electrode_wire[i][j+k].start_y < block2_shift[1]+tile_unit*2 or electrode_wire[i][j+k].start_y > block2_shift[1]+46000-tile_unit*2:
                #                             no_path=1
                #                     except:
                #                         break
                #                     finally:
                #                         k+=1
                #                 if no_path==0:
                #                     #check_grid_flow=0
                #                     grids2[check_grid_x,check_grid_y].flow=1
                #                     grids2[check_grid_x+np.sign(electrode_wire[i][j].end_x-electrode_wire[i][j].start_x),check_grid_y].flow=0
                #                     electrode_wire[i][j].end_x = electrode_wire[i][j].start_x
                #                     k=1
                #                     while j+k < len(electrode_wire[i]) and electrode_wire[i][j+k].start_x!=electrode_wire[i][j+k].end_x:# and check_grid_flow==0:
                #                         check_grid_x = (electrode_wire[i][j+k].start_x-block2_shift[0])//tile_unit
                #                         check_grid_y = (electrode_wire[i][j+k].end_y-block2_shift[1])//tile_unit	
                #                         grids2[check_grid_x,check_grid_y].flow=1
                #                         grids2[check_grid_x+np.sign(electrode_wire[i][j+k].end_x-electrode_wire[i][j+k].start_x),check_grid_y].flow=0
                #                         electrode_wire[i][j+k].end_x = electrode_wire[i][j+k].start_x
                #                         electrode_wire[i][j+k].start_x = electrode_wire[i][j+k-1].end_x	
                #                         k+=1
                #                         if (j+k)>=(len(electrode_wire[i])-1):
                #                             break
                #                         if electrode_wire[i][j+k].start_y < block2_shift[1]+tile_unit*2 or electrode_wire[i][j+k].start_y > block2_shift[1]+46000-tile_unit*2:
                #                             break
                #                     electrode_wire[i][j+k].start_x = electrode_wire[i][j+k-1].end_x	

                # #|     |    j+1           | 	 |
                # #\  -> |    j      or     /  ->  |
                # # |     \   j-1          | 		/

                # for j in range(len(electrode_wire[i])):
                #     if (electrode_wire[i][j].start_x-electrode_wire[i][j].end_x)==0 and abs(electrode_wire[i][j].start_y-electrode_wire[i][j].end_y)==250:
                #         if electrode_wire[i][j-1].start_x!=electrode_wire[i][j-1].end_x and electrode_wire[i][j+1].start_x!=electrode_wire[i][j+1].end_x and np.sign(electrode_wire[i][j-1].end_x-electrode_wire[i][j-1].start_x)==np.sign(electrode_wire[i][j+1].end_x-electrode_wire[i][j+1].start_x):
                #             if grids2[(((electrode_wire[i][j].start_x-block2_shift[0])//tile_unit)+np.sign(electrode_wire[i][j-1].end_x-electrode_wire[i][j-1].start_x)), ((electrode_wire[i][j].start_y-block2_shift[1])//tile_unit)].flow==0:
                #                 #dxf.add_circle(center=(electrode_wire[i][j].start_x, -electrode_wire[i][j].start_y), radius = 250.0)
                #                 electrode_wire[i][j-1].end_x = electrode_wire[i][j+1].end_x
                #                 electrode_wire[i][j-1].end_y = electrode_wire[i][j-1].end_y+abs(electrode_wire[i][j+1].end_x-electrode_wire[i][j+1].start_x)*np.sign(electrode_wire[i][j+1].end_y-electrode_wire[i][j+1].start_y)
                #                 electrode_wire[i][j].start_x = electrode_wire[i][j-1].end_x
                #                 electrode_wire[i][j].start_y = electrode_wire[i][j-1].end_y
                #                 electrode_wire[i][j].end_x = electrode_wire[i][j+1].end_x
                #                 electrode_wire[i][j+1].start_x = electrode_wire[i][j+1].end_x

                # for j in range(len(electrode_wire[i])-1):
                #     if (electrode_wire[i][j].start_x-electrode_wire[i][j].end_x)==0 and abs(electrode_wire[i][j].start_y-electrode_wire[i][j].end_y)==250:
                #         #dxf.add_circle(center=(electrode_wire[i][j].start_x, -electrode_wire[i][j].start_y), radius = 250.0)
                #         if np.sign(electrode_wire[i][j-1].start_x-electrode_wire[i][j-1].end_x)*np.sign(electrode_wire[i][j+1].start_x-electrode_wire[i][j+1].end_x)==-1:
                #             #dxf.add_circle(center=(electrode_wire[i][j].start_x, -electrode_wire[i][j].start_y), radius = 250.0)
                #             electrode_wire[i][j-1].end_y = electrode_wire[i][j].start_y+abs(electrode_wire[i][j+1].end_x-electrode_wire[i][j].start_x)*np.sign(electrode_wire[i][j].start_y-electrode_wire[i][j].end_y)
                #             electrode_wire[i][j].start_y = electrode_wire[i][j-1].end_y
                #             electrode_wire[i][j-1].end_x = electrode_wire[i][j+1].end_x
                #             electrode_wire[i][j].start_x = electrode_wire[i][j+1].end_x
                #             electrode_wire[i][j].end_x = electrode_wire[i][j+1].end_x
                #             electrode_wire[i][j+1].start_x = electrode_wire[i][j+1].end_x
                #     elif (electrode_wire[i][j].start_x-electrode_wire[i][j].end_x)!=0 and np.sign(electrode_wire[i][j].start_x-electrode_wire[i][j].end_x)*np.sign(electrode_wire[i][j+1].start_x-electrode_wire[i][j+1].end_x)==-1:
                #         electrode_wire[i][j].end_x = electrode_wire[i][j].start_x
                #         electrode_wire[i][j+1].start_x = electrode_wire[i][j].end_x

                ## contact pad wire fix

                if electrode_wire[i][-1].start_x!=electrode_wire[i][-1].end_x:
                    electrode_wire[i][-1].start_y = electrode_wire[i][-1].end_y+np.sign(electrode_wire[i][-1].start_y-electrode_wire[i][-1].end_y)*abs(electrode_wire[i][-1].start_x-electrode_wire[i][-1].end_x)
                    electrode_wire[i][-2].end_y = electrode_wire[i][-1].start_y

                for j in range(len(electrode_wire[i])-5, len(electrode_wire[i])-1):
                    if (electrode_wire[i][j].start_x-electrode_wire[i][j].end_x)!=0 and (electrode_wire[i][j].start_y-electrode_wire[i][j].end_y)!=0 and abs(electrode_wire[i][j].start_x-electrode_wire[i][j].end_x)!=abs(electrode_wire[i][j].start_y-electrode_wire[i][j].end_y):
                        #dxf.add_circle(center=(electrode_wire[i][j].start_x, -electrode_wire[i][j].start_y), radius = 250.0)
                        electrode_wire[i][j].end_y = electrode_wire[i][j].start_y+np.sign(electrode_wire[i][j].end_y-electrode_wire[i][j].start_y)*abs(electrode_wire[i][j+1].start_x-electrode_wire[i][j].start_x)
                    if j == 1:
                        electrode_wire[i][j-1].end_y = electrode_wire[i][j].start_y
                        electrode_wire[i][j-1].end_x = electrode_wire[i][j].start_x
                    if j == len(electrode_wire[i]) - 2:
                        electrode_wire[i][j+1].start_y = electrode_wire[i][j].end_y
                        electrode_wire[i][j+1].start_x = electrode_wire[i][j].end_x

                for j in range(len(electrode_wire[i])-7, len(electrode_wire[i])-2):
                    electrode_wire[i][j].end_x = electrode_wire[i][j+1].start_x
                    electrode_wire[i][j].end_y = electrode_wire[i][j+1].start_y

                ## contact pad wire fix

                # 讓每條線連接一起
                # for j in range(len(electrode_wire[i])-2):
                #     electrode_wire[i][j+1].start_x = electrode_wire[i][j].end_x
                #     electrode_wire[i][j+1].start_y = electrode_wire[i][j].end_y

                # for j in range(len(electrode_wire[i])-2):
                #     if j <= len(electrode_wire[i])-2:
                #         deg1 = Degree.getdegree(electrode_wire[i][j].start_x, electrode_wire[i][j].start_y, electrode_wire[i][j].end_x, electrode_wire[i][j].end_y)
                #         deg2 = Degree.getdegree(electrode_wire[i][j+1].start_x, electrode_wire[i][j+1].start_y, electrode_wire[i][j+1].end_x, electrode_wire[i][j+1].end_y)
                #         if abs(deg1[0] - deg2[0]) == 1 and abs(deg1[1] - deg2[1]):
                #             electrode_wire[i][j+1].start_y = electrode_wire[i][j+1].start_y - (electrode_wire[i][j+1].end_x - electrode_wire[i][j+1].start_x)
                #             electrode_wire[i][j].end_y = electrode_wire[i][j+1].start_y
                #             electrode_wire[i][j].end_x = electrode_wire[i][j+1].start_x

                for j in range(1, len(electrode_wire[i])-2):
                    deg = Degree.getdegree(electrode_wire[i][j].start_x, electrode_wire[i][j].start_y, electrode_wire[i][j].end_x, electrode_wire[i][j].end_y)
                    if abs(deg[0] - deg[1]) != 1:
                        if abs(deg[0]) > 0.7072 or abs(deg[1]) > 0.7072:
                            if electrode_wire[i][j].end_x < electrode_wire[i][j].start_x:
                                c = 1
                                if electrode_wire[i][j].end_y > electrode_wire[i][j].start_y:
                                    c = -1
                                if j < len(electrode_wire[i]) - 2 and j > 1:
                                    dis_x = electrode_wire[i][j].end_x - electrode_wire[i][j].start_x
                                    dis_y = electrode_wire[i][j].end_y - electrode_wire[i][j].start_y
                                    if electrode_wire[i][j+1].start_x == electrode_wire[i][j+1].end_x:
                                        electrode_wire[i][j].end_y = electrode_wire[i][j].start_y + (dis_x * c)
                                        electrode_wire[i][j+1].start_y = electrode_wire[i][j].end_y
                                    else:
                                        electrode_wire[i][j].end_x = electrode_wire[i][j].start_x + (dis_y * c)
                                        electrode_wire[i][j+1].start_x = electrode_wire[i][j].end_x

                                if j < len(electrode_wire[i]) - 2:
                                    dis_x = electrode_wire[i][j].end_x - electrode_wire[i][j].start_x
                                    dis_y = electrode_wire[i][j].end_y - electrode_wire[i][j].start_y
                                    if abs(dis_x) < abs(dis_y):
                                        electrode_wire[i][j].end_y = electrode_wire[i][j].start_y + (dis_x * c)
                                        electrode_wire[i][j+1].start_y = electrode_wire[i][j].end_y
                                    else:
                                        electrode_wire[i][j].end_x = electrode_wire[i][j].start_x + (dis_y * c)
                                        electrode_wire[i][j+1].start_x = electrode_wire[i][j].end_x
                            else:
                                c = -1
                                if electrode_wire[i][j].end_y > electrode_wire[i][j].start_y:
                                    c = 1
                                if j < len(electrode_wire[i]) - 2 and j > 1:
                                    dis_x = electrode_wire[i][j].end_x - electrode_wire[i][j].start_x
                                    dis_y = electrode_wire[i][j].end_y - electrode_wire[i][j].start_y
                                    if electrode_wire[i][j+1].start_x == electrode_wire[i][j+1].end_x:
                                        electrode_wire[i][j].end_y = electrode_wire[i][j].start_y + (dis_x * c)
                                        electrode_wire[i][j+1].start_y = electrode_wire[i][j].end_y
                                    else:
                                        electrode_wire[i][j].end_x = electrode_wire[i][j].start_x + (dis_y * c)
                                        electrode_wire[i][j+1].start_x = electrode_wire[i][j].end_x

                                if j < len(electrode_wire[i]) - 2:
                                    dis_x = electrode_wire[i][j].end_x - electrode_wire[i][j].start_x
                                    dis_y = electrode_wire[i][j].end_y - electrode_wire[i][j].start_y
                                    if abs(dis_x) < abs(dis_y):
                                        electrode_wire[i][j].end_y = electrode_wire[i][j].start_y + (dis_x * c)
                                        electrode_wire[i][j+1].start_y = electrode_wire[i][j].end_y
                                    else:
                                        electrode_wire[i][j].end_x = electrode_wire[i][j].start_x + (dis_y * c)
                                        electrode_wire[i][j+1].start_x = electrode_wire[i][j].end_x

                ####BUG 一直轉彎
                # for j in range(len(electrode_wire[i])-1):
                #     if (electrode_wire[i][j].start_x-electrode_wire[i][j].end_x)!=0 and (electrode_wire[i][j].start_y-electrode_wire[i][j].end_y)!=0 and abs(electrode_wire[i][j].start_x-electrode_wire[i][j].end_x)!=abs(electrode_wire[i][j].start_y-electrode_wire[i][j].end_y):
                #         #dxf.add_circle(center=(electrode_wire[i][j].start_x, -electrode_wire[i][j].start_y), radius = 250.0)
                #         electrode_wire[i][j].end_y = electrode_wire[i][j].start_y+np.sign(electrode_wire[i][j].end_y-electrode_wire[i][j].start_y)*abs(electrode_wire[i][j+1].start_x-electrode_wire[i][j].start_x)
                #         electrode_wire[i][j+1].start_y = electrode_wire[i][j].end_y
                #draw path
                draw_second=0
                for j in range(len(electrode_wire[i])):
                    if j == 0:
                        # if i==0:
                        #     draw_start(electrode_wire[i][j].start_x,electrode_wire[i][j].start_y,electrode_wire[i][j].end_x,electrode_wire[i][j].end_y,electrode_wire[i][j+1].end_x,electrode_wire[i][j+1].end_y,200, dxf)
                        #     dxf.add_polyline_path(	[(electrode_wire[i][j].end_x-200,-(electrode_wire[i][j].end_y-200)),
                        #         (electrode_wire[i][j].end_x-200,-(electrode_wire[i][j].end_y+200)),
                        #         (electrode_wire[i][j].end_x+200,-(electrode_wire[i][j].end_y-200)),
                        #         (electrode_wire[i][j].end_x+200,-(electrode_wire[i][j].end_y+200))])
                        # else:
                        self.draw_start(electrode_wire[i][j].start_x,electrode_wire[i][j].start_y,electrode_wire[i][j].end_x,electrode_wire[i][j].end_y,electrode_wire[i][j+1].end_x,electrode_wire[i][j+1].end_y,self.mini_width, dxf)
                        draw_second+=1
                    elif j == len(electrode_wire[i])-1:
                        # if i==0:
                        #     draw_end(electrode_wire[i][j-1].start_x,electrode_wire[i][j-1].start_y,
                        #           electrode_wire[i][j].start_x,electrode_wire[i][j].start_y,
                        #           electrode_wire[i][j].end_x,electrode_wire[i][j].end_y,200,dxf)
                        # else:
                        self.draw_end(electrode_wire[i][j-1].start_x,electrode_wire[i][j-1].start_y,
                                electrode_wire[i][j].start_x,electrode_wire[i][j].start_y,
                                electrode_wire[i][j].end_x,electrode_wire[i][j].end_y,self.regular_width,dxf, connect)
                    elif draw_second <= 3:
                        # if i==0:
                        #     draw_path(electrode_wire[i][j-1].start_x,electrode_wire[i][j-1].start_y,
                        #         electrode_wire[i][j].start_x,electrode_wire[i][j].start_y,
                        #         electrode_wire[i][j].end_x,electrode_wire[i][j].end_y,
                        #         electrode_wire[i][j+1].end_x,electrode_wire[i][j+1].end_y,200,connect,dxf)

                        # else:
                        self.draw_path(electrode_wire[i][j-1].start_x,electrode_wire[i][j-1].start_y,
                            electrode_wire[i][j].start_x,electrode_wire[i][j].start_y,
                            electrode_wire[i][j].end_x,electrode_wire[i][j].end_y,
                            electrode_wire[i][j+1].end_x,electrode_wire[i][j+1].end_y,self.mini_width,connect,dxf)
                        draw_second+=1
                        connect=1
                    else:
                        # if i==0:
                        #     draw_path(electrode_wire[i][j-1].start_x,electrode_wire[i][j-1].start_y,
                        #           electrode_wire[i][j].start_x,electrode_wire[i][j].start_y,
                        #           electrode_wire[i][j].end_x,electrode_wire[i][j].end_y,
                        #           electrode_wire[i][j+1].end_x,electrode_wire[i][j+1].end_y,200,connect,dxf)
                        # else:
                        self.draw_path(electrode_wire[i][j-1].start_x,electrode_wire[i][j-1].start_y,
                                electrode_wire[i][j].start_x,electrode_wire[i][j].start_y,
                                electrode_wire[i][j].end_x,electrode_wire[i][j].end_y,
                                electrode_wire[i][j+1].end_x,electrode_wire[i][j+1].end_y,self.regular_width,connect,dxf)