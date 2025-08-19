# Project README

## Overview

This project is designed to assist with your PhD assignment. It is implemented in Python and includes all necessary dependencies for a smooth setup and execution.

## Environment Setup

This project requires Python 3.10 (or your version) and the following dependencies.

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

Alternatively, you can install dependencies manually:
```bash
pip install -r requirements.txt
```

## Usage

After setting up the environment, run the utils script:
```bash
python utils.py
```

## Project Structure

- [`utils.py`](./utils.py) - Entry point for the project
- `environment.yml` - Conda environment specification
- `requirements.txt` - Python dependencies
- [`assignement.ipynb`](./assignement.ipynb) - Jupyter that explains the usage of utils classes
