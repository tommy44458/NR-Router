import os
from typing import Any, Callable, Dict, List, NoReturn, Optional, Tuple, Union

try:
    __location__ = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__)))
except:
    __location__ = '/Users/tommy/Documents/tommy/nr-router'


class Chip():
    def __init__(self, ewd_name: str, ewd_content=None):
        self.ewd_name = ewd_name
        self.ewd_content = ewd_content
        self.ewd_config_end = 0
        self.radius = 0
        self.electrode_shape_library = {}
        self.electrode_shape_count = 0

        # contactpad_list = [[x, y], etc.]
        self.contactpad_list: List[list] = []
        # electrode_list = [[shape, x, y], etc.]
        self.electrode_list: List[list] = []

    def setup(self):
        if self.ewd_content is None:
            self.ewd_content = self.read_ewd()
        else:
            self.ewd_content: str = self.ewd_content.split('\n')
        self.get_config()
        self.get_position()
        pass

    def read_ewd(self):
        ewd_input = []
        dir = os.path.join(__location__, 'ewd/' + self.ewd_name)
        readfile = open(dir, "r")
        for line in readfile:
            ewd_input.append(line)
        return ewd_input

    def get_config(self):
        content: List[str] = self.ewd_content
        for line in content:
            if line.split()[0] == "#ENDOFDEFINITION#":
                self.ewd_config_end = content.index(line)
                break
            elif line.split()[0] == "contactpad" and line.split()[1] == "circle":
                self.radius = int(line.split()[3])
            elif len(line.split()) > 1 and line.split()[1] == "path":
                shape_name = line.split()[0]
                shape_scope = []
                for i in range(2, len(line.split())-1, 2):
                    t_x = int(line.split()[i][1:])
                    t_y = int(line.split()[i+1])
                    shape_scope.append((t_x, t_y))
                shape_scope.append((int(line.split()[2][1:]), int(line.split()[3])))

                self.electrode_shape_library[shape_name] = shape_scope
        self.electrode_shape_count = len(self.electrode_shape_library.keys())

    def get_position(self):
        content: List[str] = self.ewd_content[self.ewd_config_end + 1:]
        for line in content:
            if line.split()[0] == "#ENDOFLAYOUT#":
                break
            true_x = int(float(line.split()[1]))
            true_y = int(float(line.split()[2]))
            # contact pad
            if line.split()[0] == "contactpad":
                self.contactpad_list.append([true_x, true_y])
            # electrodes
            elif line.split()[0] in self.electrode_shape_library:
                self.electrode_list.append([line.split()[0], true_x, true_y])
