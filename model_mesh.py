import numpy as np
from typing import Any, Optional, Tuple, Union, List, Dict, Callable, NoReturn
import math

from grid import Grid
from tile import Tile
from hub import Hub
from electrode import Electrode
from chip_section import ChipSection
from pseudo_node import PseudoNode


class ModelMesh():
    def __init__(self, top_section: ChipSection, mid_section: ChipSection, down_section: ChipSection, pseudo_node: PseudoNode):

        self.top_section = top_section
        self.mid_section = mid_section
        self.down_section = down_section

        self.pesudo_node = pseudo_node

        self.num_electrode = 0

        self.electrodes: List[Electrode] = []
        self.contactpads = []

    def get_pseudo_node(self):
        self.electrodes = self.pesudo_node.internal_node()

    def create_pseudo_node_connection(self):
        pass
