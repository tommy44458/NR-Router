from electrode import Electrode

def set_grid_by_electrode_edge_opt(list_electrodes, num_electrode, electrodes, shape, shape_scope):
        for electrode in list_electrodes:
            for i in range (len(shape)):
                if electrode[2] == shape[i]:
                    true_x = electrode[1]
                    true_y = electrode[0]
                    new_electrode = Electrode(true_x, true_y, i, num_electrode)
                    # print(new_electrode.to_dict())
                    electrodes.append(new_electrode)
                    boundary_U=true_y
                    boundary_D=true_y
                    boundary_L=true_x
                    boundary_R=true_x
                    electrode_shape_path = shape_scope[i]
                    for j in range(len(electrode_shape_path)-1):
                        x1 = true_x+electrode_shape_path[j][0]
                        y1 = true_y+electrode_shape_path[j][1]
                        x2 = true_x+electrode_shape_path[j+1][0]
                        y2 = true_y+electrode_shape_path[j+1][1]
                        E_grid_x1 = (x1-self.block2_shift[0]) // self.Tile_Unit
                        E_grid_x2 = (x2-self.block2_shift[0]) // self.Tile_Unit
                        E_grid_y1 = (y1-self.block2_shift[1]) // self.Tile_Unit
                        E_grid_y2 = (y2-self.block2_shift[1]) // self.Tile_Unit

                        # print('grid:', E_grid_x1, E_grid_y1, E_grid_x2, E_grid_y2)
                        # print('addr:', x1, y1, x2, y2)
                        if x1>boundary_R:
                            boundary_R=x1
                        if x1<boundary_L:
                            boundary_L=x1
                        if y1<boundary_U:
                            boundary_U=y1
                        if y1>boundary_D:
                            boundary_D=y1


                        ang = self.clockwise_angle([0, -1], [x2-x1, y2-y1])
                        deg = Degree.getdegree(x2, y2, x1, y1)
                        # print(ang, deg)

                        ######### 有角度
                        if ang % 90 != 0:
                            if x1>x2:
                                # |
                                #  \ _
                                if y1>y2:
                                    points = self.get_points_lines(x1, y1, x2, y2, (self.contact_line_width/2) + self.contact_line_width_gap)
                                    # print('point = ', [x1, y1], [x2, y2], 'contact points = ', points)
                                    for p in points:
                                        if points.index(p) == 0:
                                            E_grid_x = (x1-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y1-self.block2_shift[1]) // self.Tile_Unit
                                            if self.grid_is_available(self.grids2, E_grid_x, E_grid_y+1, self.num_electrode):
                                                self.grid_set_electrode(self.grids2, E_grid_x, E_grid_y+1, self.num_electrode, p[0], p[1])
                                            # internal 1,0
                                            else:
                                                self.grid_conflict(self.grids2, E_grid_x, E_grid_y+1)
                                                self.grids2[E_grid_x+1][E_grid_y] = self.grids4[E_grid_x+1][E_grid_y]
                                                # self.grid_set_electrode(self.grids2, E_grid_x+1, E_grid_y, self.num_electrode, p[0], p[1])
                                        if points.index(p) == len(points) - 1:
                                            E_grid_x = (x2-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y2-self.block2_shift[1]) // self.Tile_Unit
                                            if self.grid_is_available(self.grids2, E_grid_x, E_grid_y+1, self.num_electrode):
                                                self.grid_set_electrode(self.grids2, E_grid_x, E_grid_y+1, self.num_electrode, p[0], p[1])
                                            # internal 1,0
                                            else:
                                                self.grid_conflict(self.grids2, E_grid_x, E_grid_y+1)
                                                self.grids2[E_grid_x+1][E_grid_y] = self.grids4[E_grid_x+1][E_grid_y]
                                                # self.grid_set_electrode(self.grids2, E_grid_x+1, E_grid_y, self.num_electrode, p[0], p[1])
                                        E_grid_x = (p[0]-self.block2_shift[0]) // self.Tile_Unit
                                        E_grid_y = (p[1]-self.block2_shift[1]) // self.Tile_Unit
                                        if self.grid_is_available(self.grids2, E_grid_x, E_grid_y+1, self.num_electrode):
                                            self.grid_set_electrode(self.grids2, E_grid_x, E_grid_y+1, self.num_electrode, p[0], p[1])
                                        # internal 1,0
                                        else:
                                            self.grid_conflict(self.grids2, E_grid_x, E_grid_y+1)
                                            self.grids2[E_grid_x+1][E_grid_y] = self.grids4[E_grid_x+1][E_grid_y]
                                            # self.grid_set_electrode(self.grids2, E_grid_x+1, E_grid_y, self.num_electrode, p[0], p[1])

                                #  |
                                # /
                                else:
                                    points = self.get_points_lines(x1, y1, x2, y2, (self.contact_line_width/2) + self.contact_line_width_gap)
                                    # print('point = ', [x1, y1], [x2, y2], 'contact points = ', points)
                                    for p in points:
                                        if points.index(p) == 0:
                                            E_grid_x = (x1-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y1-self.block2_shift[1]) // self.Tile_Unit
                                            if self.grid_is_available(self.grids2, E_grid_x+1, E_grid_y+1, self.num_electrode):
                                                self.grid_set_electrode(self.grids2, E_grid_x+1, E_grid_y+1, self.num_electrode, p[0], p[1])
                                            # internal 0,0
                                            else:
                                                self.grid_conflict(self.grids2, E_grid_x+1, E_grid_y+1)
                                                self.grids2[E_grid_x][E_grid_y] = self.grids4[E_grid_x][E_grid_y]
                                                # self.grid_set_electrode(self.grids2, E_grid_x, E_grid_y, self.num_electrode, p[0], p[1])
                                        if points.index(p) == len(points) - 1:
                                            E_grid_x = (x2-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y2-self.block2_shift[1]) // self.Tile_Unit
                                            if self.grid_is_available(self.grids2, E_grid_x+1, E_grid_y+1, self.num_electrode):
                                                self.grid_set_electrode(self.grids2, E_grid_x+1, E_grid_y+1, self.num_electrode, p[0], p[1])
                                            # internal 0,0
                                            else:
                                                self.grid_conflict(self.grids2, E_grid_x+1, E_grid_y+1)
                                                self.grids2[E_grid_x][E_grid_y] = self.grids4[E_grid_x][E_grid_y]
                                                # self.grid_set_electrode(self.grids2, E_grid_x, E_grid_y, self.num_electrode, p[0], p[1])
                                        E_grid_x = (p[0]-self.block2_shift[0]) // self.Tile_Unit
                                        E_grid_y = (p[1]-self.block2_shift[1]) // self.Tile_Unit
                                        if self.grid_is_available(self.grids2, E_grid_x+1, E_grid_y+1, self.num_electrode):
                                            self.grid_set_electrode(self.grids2, E_grid_x+1, E_grid_y+1, self.num_electrode, p[0], p[1])
                                        # internal 0,0
                                        else:
                                            self.grid_conflict(self.grids2, E_grid_x+1, E_grid_y+1)
                                            self.grids2[E_grid_x+1][E_grid_y] = self.grids4[E_grid_x+1][E_grid_y]
                                            # self.grid_set_electrode(self.grids2, E_grid_x, E_grid_y, self.num_electrode, p[0], p[1])

                            elif x1<x2:
                                # \
                                #  |
                                if y1<y2:
                                    points = self.get_points_lines(x1, y1, x2, y2, (self.contact_line_width/2) + self.contact_line_width_gap)
                                    # print('point = ', [x1, y1], [x2, y2], 'contact points = ', points)
                                    for p in points:
                                        if points.index(p) == 0:
                                            E_grid_x = (x1-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y1-self.block2_shift[1]) // self.Tile_Unit
                                            if self.grid_is_available(self.grids2, E_grid_x+1, E_grid_y, self.num_electrode):
                                                self.grid_set_electrode(self.grids2, E_grid_x+1, E_grid_y, self.num_electrode, p[0], p[1])
                                            # internal 0,1
                                            else:
                                                self.grid_conflict(self.grids2, E_grid_x+1, E_grid_y)
                                                self.grids2[E_grid_x, E_grid_y+1] = self.grids4[E_grid_x, E_grid_y+1]
                                                # self.grid_set_electrode(self.grids2, E_grid_x, E_grid_y+1, self.num_electrode, p[0], p[1])
                                        if points.index(p) == len(points) - 1:
                                            E_grid_x = (x2-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y2-self.block2_shift[1]) // self.Tile_Unit
                                            if self.grid_is_available(self.grids2, E_grid_x+1, E_grid_y, self.num_electrode):
                                                self.grid_set_electrode(self.grids2, E_grid_x+1, E_grid_y, self.num_electrode, p[0], p[1])
                                            # internal 0,1
                                            else:
                                                self.grid_conflict(self.grids2, E_grid_x+1, E_grid_y)
                                                self.grids2[E_grid_x, E_grid_y+1] = self.grids4[E_grid_x, E_grid_y+1]
                                                # self.grid_set_electrode(self.grids2, E_grid_x, E_grid_y+1, self.num_electrode, p[0], p[1])
                                        E_grid_x = (p[0]-self.block2_shift[0]) // self.Tile_Unit
                                        E_grid_y = (p[1]-self.block2_shift[1]) // self.Tile_Unit
                                        if self.grid_is_available(self.grids2, E_grid_x+1, E_grid_y, self.num_electrode):
                                            self.grid_set_electrode(self.grids2, E_grid_x+1, E_grid_y, self.num_electrode, p[0], p[1])
                                        # internal 0,1
                                        else:
                                            self.grid_conflict(self.grids2, E_grid_x+1, E_grid_y)
                                            self.grids2[E_grid_x, E_grid_y+1] = self.grids4[E_grid_x, E_grid_y+1]
                                            # self.grid_set_electrode(self.grids2, E_grid_x, E_grid_y+1, self.num_electrode, p[0], p[1])
                                #  /
                                # |
                                else:
                                    points = self.get_points_lines(x1, y1, x2, y2, (self.contact_line_width/2) + self.contact_line_width_gap)
                                    # print('point = ', [x1, y1], [x2, y2], 'contact points = ', points)
                                    for p in points:
                                        if points.index(p) == 0:
                                            E_grid_x = (x1-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y1-self.block2_shift[1]) // self.Tile_Unit
                                            if self.grid_is_available(self.grids2, E_grid_x, E_grid_y, self.num_electrode):
                                                self.grid_set_electrode(self.grids2, E_grid_x, E_grid_y, self.num_electrode, p[0], p[1])
                                                # print(self.grids2[E_grid_x, E_grid_y].to_dict())
                                            # internal 1,1
                                            else:
                                                self.grid_conflict(self.grids2, E_grid_x, E_grid_y)
                                                self.grids2[E_grid_x+1, E_grid_y+1] = self.grids4[E_grid_x+1, E_grid_y+1]
                                                # print(self.grids2[E_grid_x, E_grid_y].to_dict())
                                                # self.grid_set_electrode(self.grids2, E_grid_x+1, E_grid_y+1, self.num_electrode, p[0], p[1])
                                        if points.index(p) == len(points) - 1:
                                            E_grid_x = (x2-self.block2_shift[0]) // self.Tile_Unit
                                            E_grid_y = (y2-self.block2_shift[1]) // self.Tile_Unit
                                            if self.grid_is_available(self.grids2, E_grid_x, E_grid_y, self.num_electrode):
                                                self.grid_set_electrode(self.grids2, E_grid_x, E_grid_y, self.num_electrode, p[0], p[1])
                                            # internal 1,1
                                            else:
                                                self.grid_conflict(self.grids2, E_grid_x, E_grid_y)
                                                self.grids2[E_grid_x+1, E_grid_y+1] = self.grids4[E_grid_x+1, E_grid_y+1]
                                                # self.grid_set_electrode(self.grids2, E_grid_x+1, E_grid_y+1, self.num_electrode, p[0], p[1])
                                        E_grid_x = (p[0]-self.block2_shift[0]) // self.Tile_Unit
                                        E_grid_y = (p[1]-self.block2_shift[1]) // self.Tile_Unit
                                        if self.grid_is_available(self.grids2, E_grid_x, E_grid_y, self.num_electrode):
                                            self.grid_set_electrode(self.grids2, E_grid_x, E_grid_y, self.num_electrode, p[0], p[1])
                                        # internal 1,1
                                        else:
                                            self.grid_conflict(self.grids2, E_grid_x, E_grid_y)
                                            self.grids2[E_grid_x+1, E_grid_y+1] = self.grids4[E_grid_x+1, E_grid_y+1]
                                            # self.grid_set_electrode(self.grids2, E_grid_x+1, E_grid_y+1, self.num_electrode, p[0], p[1])
                        # check_corner=0
                        ######### 直線
                        else:
                            ## ->
                            if ang == 90:
                                for k in range(E_grid_x2 - (E_grid_x1) + 1):
                                    # if self.grids4[E_grid_x1+1+k][E_grid_y1].electrode_index < 0:
                                    if self.grid_is_available(self.grids2, E_grid_x1+1+k, E_grid_y1, self.num_electrode):
                                            # if self.grids2[E_grid_x1+1+k][E_grid_y1+1].electrode_index < 0:
                                        self.grid_set_electrode(self.grids2, E_grid_x1+1+k, E_grid_y1, self.num_electrode, self.grids2[E_grid_x1+1+k][E_grid_y1].real_x, y1)
                                    # internal 1,1
                                    else:
                                        self.grid_conflict(self.grids2, E_grid_x1+1+k, E_grid_y1)
                                        # self.grid_set_electrode(self.grids2, E_grid_x1+1+k, E_grid_y1+1, self.num_electrode, self.grids2[E_grid_x1+1+k][E_grid_y1+1].real_x, y1)
                            ## | down
                            elif ang == 180:
                                for k in range(E_grid_y2 - (E_grid_y1 + 1) + 1):
                                    if self.grid_is_available(self.grids2, E_grid_x1+1, E_grid_y1+1+k, self.num_electrode):
                                        # if self.grids2[E_grid_x1, E_grid_y1+1+k].electrode_index < 0:
                                        self.grid_set_electrode(self.grids2, E_grid_x1+1, E_grid_y1+1+k, self.num_electrode, x1, self.grids2[E_grid_x1+1][E_grid_y1+1+k].real_y)
                                    # internal 0,1
                                    else:
                                        self.grid_conflict(self.grids2, E_grid_x1+1, E_grid_y1+1+k)
                                        # self.grid_set_electrode(self.grids2, E_grid_x1, E_grid_y1+1+k, self.num_electrode, x1, self.grids2[E_grid_x1][E_grid_y1+1+k].real_y)
                            ## <-
                            elif ang == 270:
                                for k in range(E_grid_x1 - E_grid_x2):
                                    if self.grid_is_available(self.grids2, E_grid_x1-k, E_grid_y1+1, self.num_electrode):
                                        # if self.grids2[E_grid_x1-k, E_grid_y1].electrode_index < 0:
                                        self.grid_set_electrode(self.grids2, E_grid_x1-k, E_grid_y1+1, self.num_electrode, self.grids2[E_grid_x1-k][E_grid_y1+1].real_x, y1)
                                    # internal 0,0
                                    else:
                                        self.grid_conflict(self.grids2, E_grid_x1-k, E_grid_y1+1)
                                        # self.grid_set_electrode(self.grids2, E_grid_x1-k, E_grid_y1, self.num_electrode, self.grids2[E_grid_x1-k][E_grid_y1].real_x, y1)
                            ## | up
                            elif ang == 360:
                                for k in range(E_grid_y1 - (E_grid_y2 + 1) + 1):
                                    if self.grid_is_available(self.grids2, E_grid_x1, E_grid_y1-k, self.num_electrode):
                                        # if self.grids2[E_grid_x1+1, E_grid_y1-k].electrode_index < 0:
                                        self.grid_set_electrode(self.grids2, E_grid_x1, E_grid_y1-k, self.num_electrode, x1, self.grids2[E_grid_x1][E_grid_y1-k].real_y)
                                    # internal 1,0
                                    else:
                                        self.grid_conflict(self.grids2, E_grid_x1, E_grid_y1-k)
                                            # self.grid_set_electrode(self.grids2, E_grid_x1+1, E_grid_y1-k, self.num_electrode, x1, self.grids2[E_grid_x1+1][E_grid_y1-k].real_y)
                    self.electrodes[-1].boundary_U=boundary_U
                    self.electrodes[-1].boundary_D=boundary_D
                    self.electrodes[-1].boundary_L=boundary_L
                    self.electrodes[-1].boundary_R=boundary_R
            self.num_electrode+=1