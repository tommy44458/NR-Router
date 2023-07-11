
<p align="center">
  <img width="250px" src="https://github.com/tommy44458/NR-Router/blob/master/logo.png">
</p>

<p align="center">Non-Regular Electrode Routing with Optimal Pin Selection for Electrowetting-on-Dielectric Chips</p>

****

NR-Router is a tool that enables precise routing on glass-based and paper-based digital microfluidic EWOD (Electrowetting on Dielectric) chips with non-regular electrodes. The routing method is based on the minimum-cost maximum-flow network model, and the routing results can be directly provided to the fabrication facility.

The detailed algorithm logic can be referred to in the following paper in ASP-DAC: (https://ieeexplore.ieee.org/document/9712567).

Check out our online web-based CAD tool: http://cad.edroplets.org/

## Getting Started

### Set up a Python virtual environment by running the following command:

```shell
python -m venv venv
```

### Activate the virtual environment:

```shell
source ./venv/bin/activate
```

### Install the necessary Python packages:

```shell
pip install -r requirements.txt
```

### Run the algorithm.

Place the input file for the algorithm in the ./ewd directory. You can specify a specific EWD file by adjusting the INPUT_FILE_NAME variable in ./config.py. The EWD file can be generated using the online DMF CAD tool at http://cad.edroplets.org/.

Execute the following command to run the algorithm:

```shell
python NR-Router.py CHIP_BASE[glass/paper] ELECTRODE_SIZE TILE_UNIT OUTPUT_FORMAT EWD_CONTENT
```

Note: If EWD_CONTENT is set to None, the algorithm will read the file specified by INPUT_FILE_NAME. Otherwise, it will perform routing using the provided EWD_CONTENT.

Here's an example command:

```shell
python NR-Router.py glass 2000 4 file
```

After running the command, the generated file will be located at ./dwg/mask.dxf.
The resulting file can be opened and processed by AutoCAD for direct fabrication.

## Routing Routing

<p align="center">
  <img width="80%" src="https://github.com/tommy44458/NR-Router/blob/master/result.png">
</p>

## Design Rules
The design rules for NR-Router can be flexibly adjusted. You can modify the parameters in RouterConfig() within ./config.py.

