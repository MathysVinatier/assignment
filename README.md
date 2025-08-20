# Project OpenLaneV2

This assignment focuses on **path planning using the OpenLane-V2 dataset**. The goal is to plan a path from the ego vehicle’s initial position to a given goal location using **graph-based search algorithms** such as **A\***, **Dijkstra** or similar.

## Given Task

For each sequence, a **goal location** is given. Starting from the ego vehicle’s initial position, the task is to plan a path to the goal using the provided lane information and a **graph-based search algorithm**.

### Desired Goal Locations

| Sequence | Goal Position (x, y, z) |
|----------|--------------------------|
| `00000`  | (1543, 248, 14)         |
| `00029`  | (738, 2673, -24)        |
| `00388`  | (1101, 86, 15)          |


## Overview

This project is a report repo for the PhD assignment. It includes a python file where the necessary class has been implemented for the task. The Jupyter file is explaining how the file works. Finally, the report.pdf file explain my choices of implementation for the given task.

## Environment Setup

This project requires Conda Python 3.9.23 and the following dependencies.

### Using Conda

1. Create the environment from the YAML file:
    ```bash
    conda env create -f environment.yml
    ```
2. Activate the environment:
    ```bash
    conda activate <env_name>
    ```

### Manual Installation

Alternatively, you can install dependencies manually :
```bash
pip install -r requirements.txt
```

## Usage

After setting up the environment, run the utils script or the assignement.ipynb :
```bash
python utils.py
```

## Project Structure

- [`utils.py`](./utils.py) - Entry point for the project
- `environment.yml` - Conda environment specification
- `requirements.txt` - Python dependencies
- [`assignement.ipynb`](./assignement.ipynb) - Jupyter that explains the usage of utils classes
- [`report.pdf`](./report.pdf) - Report of the assignement
