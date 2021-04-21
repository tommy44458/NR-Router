import numpy as np
import math
import sys
import os
from ezdxf.r12writer import r12writer
from operator import itemgetter, attrgetter
from math import atan2,degrees

from degree import Degree

class Draw():

    def __init__(self, MaxFlowWithMinCost, min_cost_flow, block2_shift, Tile_Unit, electrode_wire, shape_scope):
        self.MaxFlowWithMinCost = MaxFlowWithMinCost
        self.min_cost_flow = min_cost_flow
        self.block2_shift = block2_shift
        self.Tile_Unit = Tile_Unit
        self.electrode_wire = electrode_wire
        self.shape_scope = shape_scope

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
        if width==50:
            Tan=(Tan/2)

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

        if y2 == y3 and width!=50:
            degree1 = (1,0)
            degree2 = (1,0)
        elif x2 == x3 and width!=50:
            degree1 = (0,1)
            degree2 = (0,1)

        if y3 == y4 and x2!=x3 and width!=50:
            degree2 = (1,0)
        elif x3 == x4 and y2!=y3 and width!=50:
            degree2 = (0,1)
        # 1/\4
        # 2\/3
        #45 angle
        if x2!=x3 and y2!=y3 and width!=50:
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
        if (x3 == x4 and y2==y3) and width!=50:
            deg_90_UD = 1
        if (y3 == y4 and x2==x3) and width!=50:
            deg_90_RL = 1
        if y1 == y2 and x2!=x3 and width!=50:
            degree1 = (1,0)
        position_s1 = [x2-width*degree1[1],y2+width*degree1[0],Degree.inner_degree(x2-width*degree1[1],y2+width*degree1[0],(x2+x3)/2,(y2+y3)/2)]
        position_s2 = [x2+width*degree1[1],y2-width*degree1[0],Degree.inner_degree(x2-width*degree1[1],y2+width*degree1[0],(x2+x3)/2,(y2+y3)/2)]
        if width==50:
            if x1!=x2 and y1!=y2:
                if x2==x3:
                    if x1>x2:
                        if y2>y3:
                            position_s1=[x2+width,y2,1]
                            position_s2=[x2-width,y2,2]
                        elif y2<y3:
                            position_s1=[x2+width,y2,1]
                            position_s2=[x2-width,y2,2]
                    elif x1<x2:
                        if y2>y3:
                            position_s1=[x2-width,y2,1]
                            position_s2=[x2+width,y2,2]
                        elif y2<y3:
                            position_s1=[x2-width,y2,1]
                            position_s2=[x2+width,y2,2]
                elif y2==y3:
                    if y1>y2:
                        if x2>x3:
                            position_s1=[x2,y2-width,1]
                            position_s2=[x2,y2+width,2]
                        elif x2<x3:
                            position_s1=[x2,y2-width,1]
                            position_s2=[x2,y2+width,2]
                    elif y1<y2:
                        if x2>x3:
                            position_s1=[x2,y2+width,1]
                            position_s2=[x2,y2-width,2]
                        elif x2<x3:
                            position_s1=[x2,y2+width,1]
                            position_s2=[x2,y2-width,2]
        if abs(position_s1[2]-position_s2[2])>90:
            if min(position_s1[2],position_s2[2]) == position_s1[2]:
                position_s2[2]-=360
            else:
                position_s1[2]-=360

        if deg_45!=0:# and connect!=1:
            #dxf.add_solid([(x2+width/2,y2+width/2),(x2-width/2,y2+width/2),(x2+width/2,y2-width/2),(x2-width/2,y2-width/2)])

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
        position1.sort(key=lambda k: [k[2]])
        position_e1 = [x3+width*degree2[1],y3-width*degree2[0],Degree.inner_degree(x3+width*degree2[1],y3-width*degree2[0],(x2+x3)/2,(y2+y3)/2)]
        position_e2	= [x3-width*degree2[1],y3+width*degree2[0],Degree.inner_degree(x3-width*degree2[1],y3+width*degree2[0],(x2+x3)/2,(y2+y3)/2)]
        if deg_45!=0 :

            # dxf.add_solid([(x3,y3+width),(x3-width,y3),(x3+width,y3),(x3,y3-width)])
            # print('***************', [(x3,y3+width),(x3-width,y3),(x3+width,y3),(x3,y3-width)])
            # print('***************', [(x3+(width/2),y3+(width*Tan/100)),(x3+(width/2),y3+(width*Tan/100)),(x3+(width/2),y3-(width*Tan/100)),(x3-(width/2),y3-(width*Tan/100))])
            # dxf.add_solid([(x3+(width/2),y3+(width*Tan/100)),(x3+(width/2),y3+(width*Tan/100)),(x3+(width/2),y3-(width*Tan/100)),(x3-(width/2),y3-(width*Tan/100))])

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
        if width==50:
            if x2!=x3 and y2!=y3:
                if x3==x4:
                    position_e1[0]=x3+70.7
                    position_e1[1]=y3
                    position_e2[0]=x3-70.7
                    position_e2[1]=y3
                elif y3==y4:
                    position_e1[0]=x3
                    position_e1[1]=y3+70.7
                    position_e2[0]=x3
                    position_e2[1]=y3-70.7
        if abs(position_e1[2]-position_e2[2])>90:
            if min(position_e1[2],position_e2[2]) == position_e1[2]:
                position_e2[2]-=360
            else:
                position_e1[2]-=360
        position2.append(position_e1)
        position2.append(position_e2)
        position2.sort(key=lambda k: [k[2]],reverse=True)

        dxf.add_solid([(position1[0][0],position1[0][1]),(position1[1][0],position1[1][1]),
                        (position2[0][0],position2[0][1]),(position2[1][0],position2[1][1])])    

        dxf.add_solid([(position1[0][0],position1[0][1]),(position1[1][0],position1[1][1]),
                        (position2[1][0],position2[1][1]),(position2[0][0],position2[0][1])])
        
    def draw_path(self, x1,y1,x2,y2,x3,y3,x4,y4,width,connect,dxf):
        y1 = -1*y1
        y2 = -1*y2
        y3 = -1*y3
        y4 = -1*y4
        if width==50:
            dxf.add_arc(center=(x3,y3),radius=100,start=0, end=359)
        self.draw_orthogonal_path(x1,y1,x2,y2,x3,y3,x4,y4,width,connect,dxf)
        
    def draw_start(self, x1,y1,x2,y2,x3,y3,width,dxf):
        y1 = -y1
        y2 = -y2
        y3 = -y3
        degree1 = Degree.getdegree(x1,y1,x2,y2)
        Tan = 0.41421356237 * width
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
            dxf.add_solid(	[S1,S2,E1,E2,S1])
            dxf.add_solid(	[S1,S2,E2,E1,S1])
        else:
            dxf.add_solid(	[(x1-width*degree1[1],y1+width*degree1[0]),
                            (x1+width*degree1[1],y1-width*degree1[0]),
                            (x2-width*degree1[1],y2+width*degree1[0]),
                            (x2+width*degree1[1],y2-width*degree1[0]),
                            (x1-width*degree1[1],y1+width*degree1[0])])

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
        if degree1[0] == degree2[0] and degree1[1] == degree2[1] and width==50:
            dxf.add_solid(	[(x3-width,y3),
                            (x3,y3+width),
                            (x3,y3-width),
                            (x3+width,y3)])
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
            # dxf.add_solid([(x2,y2+width),(x2-width,y2),(x2+width,y2),(x2,y2-width)])
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
        position2.sort(key=lambda k: [k[2]],reverse=True)
        dxf.add_solid([(position1[0][0],position1[0][1]),(position1[1][0],position1[1][1]),
                        (position2[0][0],position2[0][1]),(position2[1][0],position2[1][1])])
        dxf.add_solid([(position1[0][0],position1[0][1]),(position1[1][0],position1[1][1]),
                        (position2[1][0],position2[1][1]),(position2[0][0],position2[0][1])])
        
    def draw_tmp(self, x1,y1,x2,y2,dxf):
        width=100
        degree1 = Degree.getdegree(x1,y1,x2,y2)
        dxf.add_solid([(x1+width*degree1[1],-y1+width*degree1[0]),(x1-width*degree1[1],-y1-width*degree1[0]),
                    (x2+width*degree1[1],-y2+width*degree1[0]),(x2-width*degree1[1],-y2-width*degree1[0])])

    def draw_contact_pads(self, contactpads, dxf):
        for i in range(len(contactpads)):
            dxf.add_circle(center=(contactpads[i][0], -contactpads[i][1]), radius = 750.0)
            
    def draw_electrodes(self, electrodes, dxf):
        for i in range(len(electrodes)):
            x = electrodes[i].real_x
            y = -electrodes[i].real_y
            type = electrodes[i].shape
            vertices = []
            for k,l in self.shape_scope[type]:
                #vertices.append((x+k, y+l))
                vertices.append((x+k, y-l))#mirrow
            dxf.add_polyline(vertices)
            
    def draw_grid(self, start_x, start_y, unit_length, grids_x, grids_y,dxf):
        for i in range(grids_x):
            dxf.add_line((start_x+unit_length*i, -start_y),(start_x+unit_length*i,-(start_y+unit_length*(grids_y-1))))
        for i in range(grids_y):
            dxf.add_line((start_x, -(start_y+unit_length*i)),(start_x+unit_length*(grids_x-1),-(start_y+unit_length*i)))

    def draw_all_path(self, dxf, grids2):
        MaxFlowWithMinCost = self.MaxFlowWithMinCost
        min_cost_flow = self.min_cost_flow
        block2_shift = self.block2_shift
        Tile_Unit = self.Tile_Unit
        electrode_wire = self.electrode_wire

        connect = 0
        if MaxFlowWithMinCost == min_cost_flow.OPTIMAL:
            for i in range(len(electrode_wire)):
                #tune path start 
                ## reduce change way
                if abs(electrode_wire[i][0].start_x-electrode_wire[i][0].end_x)!=0 and abs(electrode_wire[i][0].start_y-electrode_wire[i][0].end_y)!=0 and (np.sign(electrode_wire[i][0].start_x-electrode_wire[i][0].end_x)!=np.sign(electrode_wire[i][1].start_x-electrode_wire[i][1].end_x)) and (electrode_wire[i][2].start_x==electrode_wire[i][2].end_x):
                    electrode_wire[i][0].end_x = electrode_wire[i][1].end_x
                    electrode_wire[i][0].end_y = electrode_wire[i][0].start_y+abs(electrode_wire[i][2].start_x-electrode_wire[i][0].start_x)*np.sign(electrode_wire[i][2].start_y-electrode_wire[i][0].start_y)
                    electrode_wire[i][2].start_y=electrode_wire[i][0].start_y+abs(electrode_wire[i][2].start_x-electrode_wire[i][0].start_x)*np.sign(electrode_wire[i][2].start_y-electrode_wire[i][0].start_y)
                    del electrode_wire[i][1]

                if abs(electrode_wire[i][1].start_x-electrode_wire[i][1].end_x)!=abs(electrode_wire[i][1].start_y-electrode_wire[i][1].end_y) and abs(electrode_wire[i][1].start_x-electrode_wire[i][1].end_x)!=0 and abs(electrode_wire[i][1].start_y-electrode_wire[i][1].end_y)!=0:
                    if abs(electrode_wire[i][2].end_x-electrode_wire[i][1].start_x)>abs(electrode_wire[i][2].end_y-electrode_wire[i][1].start_y):
                        electrode_wire[i][1].end_x = electrode_wire[i][1].start_x+abs(electrode_wire[i][2].end_y-electrode_wire[i][1].start_y)*np.sign(electrode_wire[i][2].end_x-electrode_wire[i][1].start_x)
                        electrode_wire[i][1].end_y = electrode_wire[i][2].end_y
                        electrode_wire[i][2].start_x = electrode_wire[i][1].start_x+abs(electrode_wire[i][2].end_y-electrode_wire[i][1].start_y)*np.sign(electrode_wire[i][2].end_x-electrode_wire[i][1].start_x)
                        electrode_wire[i][2].start_y = electrode_wire[i][2].end_y
                    else:
                        electrode_wire[i][1].end_x = electrode_wire[i][2].end_x
                        electrode_wire[i][1].end_y = electrode_wire[i][1].start_y+abs(electrode_wire[i][2].end_x-electrode_wire[i][1].start_x)*np.sign(electrode_wire[i][2].end_y-electrode_wire[i][1].start_y)
                        electrode_wire[i][2].start_x = electrode_wire[i][2].end_x
                        electrode_wire[i][2].start_y = electrode_wire[i][1].start_y+abs(electrode_wire[i][2].end_x-electrode_wire[i][1].start_x)*np.sign(electrode_wire[i][2].end_y-electrode_wire[i][1].start_y)

                for j in range(len(electrode_wire[i])-2):
                    if np.sign(electrode_wire[i][j].start_x-electrode_wire[i][j].end_x)!=np.sign(electrode_wire[i][j+1].start_x-electrode_wire[i][j+1].end_x) and (electrode_wire[i][j].start_x-electrode_wire[i][j].end_x)!=0:
                        if abs(electrode_wire[i][j+1].end_x-electrode_wire[i][j].start_x)>abs(electrode_wire[i][j+1].end_y-electrode_wire[i][j].start_y):
                            electrode_wire[i][j].end_x = electrode_wire[i][j].start_x+abs(electrode_wire[i][j+1].end_y-electrode_wire[i][j].start_y)*np.sign(electrode_wire[i][j+1].end_x-electrode_wire[i][j].start_x)
                            electrode_wire[i][j].end_y = electrode_wire[i][j+1].end_y
                            electrode_wire[i][j+1].start_x = electrode_wire[i][j].start_x+abs(electrode_wire[i][j+1].end_y-electrode_wire[i][j].start_y)*np.sign(electrode_wire[i][j+1].end_x-electrode_wire[i][j].start_x)
                            electrode_wire[i][j+1].start_y = electrode_wire[i][j+1].end_y
                        else:
                            electrode_wire[i][j].end_x = electrode_wire[i][j+1].end_x
                            electrode_wire[i][j].end_y = electrode_wire[i][j].start_y+abs(electrode_wire[i][j+1].end_x-electrode_wire[i][j].start_x)*np.sign(electrode_wire[i][j+1].end_y-electrode_wire[i][j].start_y)
                            electrode_wire[i][j+1].start_x = electrode_wire[i][j+1].end_x
                            electrode_wire[i][j+1].start_y = electrode_wire[i][j].start_y+abs(electrode_wire[i][j+1].end_x-electrode_wire[i][j].start_x)*np.sign(electrode_wire[i][j+1].end_y-electrode_wire[i][j].start_y)

                for j in range(len(electrode_wire[i])-2):	
                    if abs(electrode_wire[i][j].start_x-electrode_wire[i][j].end_x) == 0 and abs(electrode_wire[i][j+1].start_y-electrode_wire[i][j+1].end_y) == 0:
                        electrode_wire[i][j].end_x = electrode_wire[i][j].start_x+abs(electrode_wire[i][j].end_y-electrode_wire[i][j].start_y)*np.sign(electrode_wire[i][j+1].end_x-electrode_wire[i][j+1].start_x)
                        electrode_wire[i][j+1].start_x = electrode_wire[i][j].end_x
                    if abs(electrode_wire[i][j].start_y-electrode_wire[i][j].end_y) == 0 and abs(electrode_wire[i][j+1].start_x-electrode_wire[i][j+1].end_x) == 0:
                        electrode_wire[i][j].end_y = electrode_wire[i][j].start_y+abs(electrode_wire[i][j].end_x-electrode_wire[i][j].start_x)*np.sign(electrode_wire[i][j+1].end_y-electrode_wire[i][j+1].start_y)
                        electrode_wire[i][j+1].start_y = electrode_wire[i][j].end_y

                for j in range(len(electrode_wire[i])):
                    if (electrode_wire[i][j].start_x-electrode_wire[i][j].end_x)==0 and abs(electrode_wire[i][j].start_y-electrode_wire[i][j].end_y)==250:
                        #dxf.add_circle(center=(electrode_wire[i][j].start_x, -electrode_wire[i][j].start_y), radius = 250.0)
                        if np.sign(electrode_wire[i][j-1].start_x-electrode_wire[i][j-1].end_x)*np.sign(electrode_wire[i][j+1].start_x-electrode_wire[i][j+1].end_x)==-1:
                            #dxf.add_circle(center=(electrode_wire[i][j].start_x, -electrode_wire[i][j].start_y), radius = 250.0)
                            electrode_wire[i][j-1].end_y = electrode_wire[i][j].start_y+abs(electrode_wire[i][j+1].end_x-electrode_wire[i][j].start_x)*np.sign(electrode_wire[i][j].start_y-electrode_wire[i][j].end_y)
                            electrode_wire[i][j].start_y = electrode_wire[i][j-1].end_y
                            electrode_wire[i][j-1].end_x = electrode_wire[i][j+1].end_x
                            electrode_wire[i][j].start_x = electrode_wire[i][j+1].end_x
                            electrode_wire[i][j].end_x = electrode_wire[i][j+1].end_x
                            electrode_wire[i][j+1].start_x = electrode_wire[i][j+1].end_x
                        if electrode_wire[i][j-1].start_x!=electrode_wire[i][j-1].end_x and electrode_wire[i][j+1].start_x!=electrode_wire[i][j+1].end_x:
                            #dxf.add_circle(center=(electrode_wire[i][j].start_x, -electrode_wire[i][j].start_y), radius = 250.0)
                            electrode_wire[i][j-1].end_x = electrode_wire[i][j+1].end_x
                            electrode_wire[i][j-1].end_y = electrode_wire[i][j-1].end_y+abs(electrode_wire[i][j+1].end_x-electrode_wire[i][j+1].start_x)*np.sign(electrode_wire[i][j+1].end_y-electrode_wire[i][j+1].start_y)
                            electrode_wire[i][j].start_x = electrode_wire[i][j-1].end_x
                            electrode_wire[i][j].start_y = electrode_wire[i][j-1].end_y
                            electrode_wire[i][j].end_x = electrode_wire[i][j+1].end_x
                            electrode_wire[i][j+1].start_x = electrode_wire[i][j+1].end_x

                    if electrode_wire[i][j].end_y > block2_shift[1] and electrode_wire[i][j].end_y < block2_shift[1]+46000:
                        S_grid_x = (electrode_wire[i][j].start_x-block2_shift[0])//Tile_Unit
                        S_grid_y = (electrode_wire[i][j].start_y-block2_shift[1])//Tile_Unit
                        T_grid_x = (electrode_wire[i][j].end_x-block2_shift[0])//Tile_Unit
                        T_grid_y = (electrode_wire[i][j].end_y-block2_shift[1])//Tile_Unit
                        grids2[S_grid_x,S_grid_y].flow=1
                        grids2[T_grid_x,T_grid_y].flow=1

                #|      |    j-1        |       \   j+1
                #\  ->  |    j     or   \  ->    |  j
                # |      \   j+1         |       |  j-1

                for j in range(3,len(electrode_wire[i])):		
                    if electrode_wire[i][j].end_y > block2_shift[1]+Tile_Unit and electrode_wire[i][j].end_y < block2_shift[1]+46000-Tile_Unit:
                        if electrode_wire[i][j-1].start_x==electrode_wire[i][j-1].end_x and abs(electrode_wire[i][j].start_x-electrode_wire[i][j].end_x)==abs(electrode_wire[i][j].start_y-electrode_wire[i][j].end_y):
                            check_grid_x = (electrode_wire[i][j].start_x-block2_shift[0])//Tile_Unit
                            check_grid_y = (electrode_wire[i][j].end_y-block2_shift[1])//Tile_Unit
                            if grids2[check_grid_x,check_grid_y].flow == 0 and grids2[check_grid_x,check_grid_y].safe_distance==0 and grids2[check_grid_x,check_grid_y].safe_distance2==0:
                                k=1
                                no_path=0
                                while j+k < len(electrode_wire[i]) and electrode_wire[i][j+k].start_x!=electrode_wire[i][j+k].end_x:
                                    check_grid_x = (electrode_wire[i][j+k].start_x-block2_shift[0])//Tile_Unit
                                    check_grid_y = (electrode_wire[i][j+k].end_y-block2_shift[1])//Tile_Unit
                                    try:
                                        if grids2[check_grid_x,check_grid_y].flow != 0:
                                        # or grids2[check_grid_x,check_grid_y].safe_distance2==1 or grids2[check_grid_x,check_grid_y].safe_distance==1:
                                            no_path=1
                                        if electrode_wire[i][j+k].start_y < block2_shift[1]+Tile_Unit*2 or electrode_wire[i][j+k].start_y > block2_shift[1]+46000-Tile_Unit*2:
                                            no_path=1
                                    except:
                                        break
                                    finally:
                                        k+=1
                                if no_path==0:
                                    #check_grid_flow=0
                                    grids2[check_grid_x,check_grid_y].flow=1
                                    grids2[check_grid_x+np.sign(electrode_wire[i][j].end_x-electrode_wire[i][j].start_x),check_grid_y].flow=0
                                    electrode_wire[i][j].end_x = electrode_wire[i][j].start_x
                                    k=1
                                    while j+k < len(electrode_wire[i]) and electrode_wire[i][j+k].start_x!=electrode_wire[i][j+k].end_x:# and check_grid_flow==0:
                                        check_grid_x = (electrode_wire[i][j+k].start_x-block2_shift[0])//Tile_Unit
                                        check_grid_y = (electrode_wire[i][j+k].end_y-block2_shift[1])//Tile_Unit	
                                        grids2[check_grid_x,check_grid_y].flow=1
                                        grids2[check_grid_x+np.sign(electrode_wire[i][j+k].end_x-electrode_wire[i][j+k].start_x),check_grid_y].flow=0
                                        electrode_wire[i][j+k].end_x = electrode_wire[i][j+k].start_x
                                        electrode_wire[i][j+k].start_x = electrode_wire[i][j+k-1].end_x	
                                        k+=1
                                        if (j+k)>=(len(electrode_wire[i])-1):
                                            break
                                        if electrode_wire[i][j+k].start_y < block2_shift[1]+Tile_Unit*2 or electrode_wire[i][j+k].start_y > block2_shift[1]+46000-Tile_Unit*2:
                                            break
                                    electrode_wire[i][j+k].start_x = electrode_wire[i][j+k-1].end_x	

                #|     |    j+1           | 	 |
                #\  -> |    j      or     /  ->  |
                # |     \   j-1          | 		/

                for j in range(len(electrode_wire[i])):
                    if (electrode_wire[i][j].start_x-electrode_wire[i][j].end_x)==0 and abs(electrode_wire[i][j].start_y-electrode_wire[i][j].end_y)==250:
                        if electrode_wire[i][j-1].start_x!=electrode_wire[i][j-1].end_x and electrode_wire[i][j+1].start_x!=electrode_wire[i][j+1].end_x and np.sign(electrode_wire[i][j-1].end_x-electrode_wire[i][j-1].start_x)==np.sign(electrode_wire[i][j+1].end_x-electrode_wire[i][j+1].start_x):
                            if grids2[(((electrode_wire[i][j].start_x-block2_shift[0])//Tile_Unit)+np.sign(electrode_wire[i][j-1].end_x-electrode_wire[i][j-1].start_x)), ((electrode_wire[i][j].start_y-block2_shift[1])//Tile_Unit)].flow==0:
                                #dxf.add_circle(center=(electrode_wire[i][j].start_x, -electrode_wire[i][j].start_y), radius = 250.0)
                                electrode_wire[i][j-1].end_x = electrode_wire[i][j+1].end_x
                                electrode_wire[i][j-1].end_y = electrode_wire[i][j-1].end_y+abs(electrode_wire[i][j+1].end_x-electrode_wire[i][j+1].start_x)*np.sign(electrode_wire[i][j+1].end_y-electrode_wire[i][j+1].start_y)
                                electrode_wire[i][j].start_x = electrode_wire[i][j-1].end_x
                                electrode_wire[i][j].start_y = electrode_wire[i][j-1].end_y
                                electrode_wire[i][j].end_x = electrode_wire[i][j+1].end_x
                                electrode_wire[i][j+1].start_x = electrode_wire[i][j+1].end_x

                for j in range(len(electrode_wire[i])-1):
                    if (electrode_wire[i][j].start_x-electrode_wire[i][j].end_x)==0 and abs(electrode_wire[i][j].start_y-electrode_wire[i][j].end_y)==250:
                        #dxf.add_circle(center=(electrode_wire[i][j].start_x, -electrode_wire[i][j].start_y), radius = 250.0)
                        if np.sign(electrode_wire[i][j-1].start_x-electrode_wire[i][j-1].end_x)*np.sign(electrode_wire[i][j+1].start_x-electrode_wire[i][j+1].end_x)==-1:
                            #dxf.add_circle(center=(electrode_wire[i][j].start_x, -electrode_wire[i][j].start_y), radius = 250.0)
                            electrode_wire[i][j-1].end_y = electrode_wire[i][j].start_y+abs(electrode_wire[i][j+1].end_x-electrode_wire[i][j].start_x)*np.sign(electrode_wire[i][j].start_y-electrode_wire[i][j].end_y)
                            electrode_wire[i][j].start_y = electrode_wire[i][j-1].end_y
                            electrode_wire[i][j-1].end_x = electrode_wire[i][j+1].end_x
                            electrode_wire[i][j].start_x = electrode_wire[i][j+1].end_x
                            electrode_wire[i][j].end_x = electrode_wire[i][j+1].end_x
                            electrode_wire[i][j+1].start_x = electrode_wire[i][j+1].end_x
                    elif (electrode_wire[i][j].start_x-electrode_wire[i][j].end_x)!=0 and np.sign(electrode_wire[i][j].start_x-electrode_wire[i][j].end_x)*np.sign(electrode_wire[i][j+1].start_x-electrode_wire[i][j+1].end_x)==-1:
                        electrode_wire[i][j].end_x = electrode_wire[i][j].start_x
                        electrode_wire[i][j+1].start_x = electrode_wire[i][j].end_x

                if electrode_wire[i][-1].start_x!=electrode_wire[i][-1].end_x:
                    electrode_wire[i][-1].start_y = electrode_wire[i][-1].end_y+np.sign(electrode_wire[i][-1].start_y-electrode_wire[i][-1].end_y)*abs(electrode_wire[i][-1].start_x-electrode_wire[i][-1].end_x)
                    electrode_wire[i][-2].end_y = electrode_wire[i][-1].start_y

                for j in range(len(electrode_wire[i])-1):
                    if (electrode_wire[i][j].start_x-electrode_wire[i][j].end_x)!=0 and (electrode_wire[i][j].start_y-electrode_wire[i][j].end_y)!=0 and abs(electrode_wire[i][j].start_x-electrode_wire[i][j].end_x)!=abs(electrode_wire[i][j].start_y-electrode_wire[i][j].end_y):
                        #dxf.add_circle(center=(electrode_wire[i][j].start_x, -electrode_wire[i][j].start_y), radius = 250.0)
                        electrode_wire[i][j].end_y = electrode_wire[i][j].start_y+np.sign(electrode_wire[i][j].end_y-electrode_wire[i][j].start_y)*abs(electrode_wire[i][j+1].start_x-electrode_wire[i][j].start_x)
                        electrode_wire[i][j+1].start_y = electrode_wire[i][j].end_y
                #draw path
                for j in range(len(electrode_wire[i])):
                    if j == 0:
                        # if i==0:
                        #     draw_start(electrode_wire[i][j].start_x,electrode_wire[i][j].start_y,electrode_wire[i][j].end_x,electrode_wire[i][j].end_y,electrode_wire[i][j+1].end_x,electrode_wire[i][j+1].end_y,200, dxf)
                        #     dxf.add_solid(	[(electrode_wire[i][j].end_x-200,-(electrode_wire[i][j].end_y-200)),
                        #         (electrode_wire[i][j].end_x-200,-(electrode_wire[i][j].end_y+200)),
                        #         (electrode_wire[i][j].end_x+200,-(electrode_wire[i][j].end_y-200)),
                        #         (electrode_wire[i][j].end_x+200,-(electrode_wire[i][j].end_y+200))])
                        # else:
                        self.draw_start(electrode_wire[i][j].start_x,electrode_wire[i][j].start_y,electrode_wire[i][j].end_x,electrode_wire[i][j].end_y,electrode_wire[i][j+1].end_x,electrode_wire[i][j+1].end_y,50, dxf)
                        draw_second=1
                    elif j == len(electrode_wire[i])-1:
                        # if i==0:
                        #     draw_end(electrode_wire[i][j-1].start_x,electrode_wire[i][j-1].start_y,
                        #           electrode_wire[i][j].start_x,electrode_wire[i][j].start_y,
                        #           electrode_wire[i][j].end_x,electrode_wire[i][j].end_y,200,dxf)
                        # else:
                        self.draw_end(electrode_wire[i][j-1].start_x,electrode_wire[i][j-1].start_y,
                                electrode_wire[i][j].start_x,electrode_wire[i][j].start_y,
                                electrode_wire[i][j].end_x,electrode_wire[i][j].end_y,100,dxf, connect)
                    elif draw_second==1:
                        # if i==0:
                        #     draw_path(electrode_wire[i][j-1].start_x,electrode_wire[i][j-1].start_y,
                        #         electrode_wire[i][j].start_x,electrode_wire[i][j].start_y,
                        #         electrode_wire[i][j].end_x,electrode_wire[i][j].end_y,
                        #         electrode_wire[i][j+1].end_x,electrode_wire[i][j+1].end_y,200,connect,dxf)

                        # else:
                        self.draw_path(electrode_wire[i][j-1].start_x,electrode_wire[i][j-1].start_y,
                            electrode_wire[i][j].start_x,electrode_wire[i][j].start_y,
                            electrode_wire[i][j].end_x,electrode_wire[i][j].end_y,
                            electrode_wire[i][j+1].end_x,electrode_wire[i][j+1].end_y,50,connect,dxf)
                        draw_second=0
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
                                electrode_wire[i][j+1].end_x,electrode_wire[i][j+1].end_y,100,connect,dxf)