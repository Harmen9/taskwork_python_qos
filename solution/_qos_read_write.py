import json
from typing import Tuple
from pathlib import Path
from datetime import datetime
from ast import literal_eval
from _db_connection import PgConnection
import pandas as pd

def read_config(base_path: Path, config_path: Path) -> dict:
    '''
    Reads config file and converts the paths to an absolute path.
    the location of the config file is 
    Parameters:
    - base_path: Base path of the qos algorithm folder.

    Returns:
    - config: dictionary with the configuration variables.

    Raises:
    - FileNotFoundError: If the input folder does not exist.
    - FileNotFoundError: If the config file does not exist.
    '''
    if not config_path.is_file():
        raise FileNotFoundError(f"The config file '{config_path}' does not exist.")

    with open(config_path, 'r', encoding='utf-8') as file:
        config = json.load(file)

    if Path(config['paths']['input']).is_absolute():
        config['paths']['input'] = Path(config['paths']['input'])
    else:
        config['paths']['input'] = base_path / config['paths']['input']

    if Path(config['paths']['output']).is_absolute():
        config['paths']['output'] = Path(config['paths']['output'])
    else:
        config['paths']['output'] = base_path / config['paths']['output']

    if not config['paths']['input'].is_dir():
        raise FileNotFoundError(f"The folder '{config['paths']['input']}' does not exist.")

    return config

def convert_to_list(text):
    '''
    This converter function converts a value to type list.
    Used by pandas read_csv function to convert columns directly at the import.
    '''
    return literal_eval(text)


def read_qos_data(input_folder: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    '''
    Reads the quality of service data scources via the CSV's stored in the input_folder.

    Parameters:
    - input_folder: the input folder which contains the csv's "qos_curves.csv" and "qos_data.csv"
    
    Returns:
    - qos_data: DataFrame read from qos_data.csv.
    See TASK_DESCRIPTION.md for a description of the data.
    - qos_curves: DataFrame read from qos_curves.csv.
    See TASK_DESCRIPTION.md for a description of the data.

    Raises:
    - FileNotFoundError: If the input folder does not exist.
    '''

    if not input_folder.is_dir():
        raise FileNotFoundError(f"The folder '{str(input_folder)}' does not exist.")

    list_converters = {'X': convert_to_list, 'Y': convert_to_list}

    # Read CSVs
    qos_curves: pd.DataFrame = pd.read_csv(
        input_folder / 'qos_curves.csv',
        converters=list_converters
    )
    qos_data: pd.DataFrame = pd.read_csv(
        input_folder / 'qos_data.csv',
        converters=list_converters
    )

    return qos_data, qos_curves

def write_data(data: pd.DataFrame, filename: str, output_path: Path):
    '''
    Writes dataframe to a csv in the output folder.
    If the folder does not exist it will be created including parent folders.
    Adds the current datetime to the filename.
    
    Parameters:
    - data: Data to write in DataFrame format.
    - filename: filename of the output file, without datetime.
    - output_path: output folder in pathlib Path type.
    '''

    # Create the folder if it doesn't exist
    if not output_path.is_dir():
        output_path.mkdir(parents=True)

    current_datetime: datetime = datetime.now()
    datetime_str: str = current_datetime.strftime('%y%m%d%H%M')

    filename = f'{filename}_{datetime_str}.csv'
    data.to_csv(output_path / filename, index=True)
