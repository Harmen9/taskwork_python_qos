import logging
from pathlib import Path
from datetime import datetime
import traceback
import pandas as pd

from _db_connection import PgConnection
from _logger import CustomLogger
from _qos_read_write import (
    read_qos_data,
    read_config,
    write_data
)
from _qos_transformations import (
    transform_qos_data,
    create_full_time_grid,
    interpolate_consumption_curves
)
from _qos_metrics import (
    create_product_inventory,
    calc_product_availability_ratio,
    calc_quality_of_service
)

def main():
    base_path: Path = Path(__file__).parent.parent
    config_path = base_path / 'solution' / 'qos_config.json'

    logging.info('Read config file.')
    config = read_config(base_path, config_path)

    if config['use_db']:
        logging.info('Read input from database.')
        db_connect = PgConnection(**config['db'])
        db_connect.establish_connection()
        qos_data, qos_curves = db_connect.db_read_qos_data(
            qos_data_table=config['db_qos_data_table'],
            qos_curves_table=config['db_qos_curves_table']
        )
        db_connect.close_connection()

    else:
        logging.info('Read input csvs.')
        qos_data, qos_curves = read_qos_data(input_folder=config['paths']['input'])

    number_of_locations = qos_data['LOCATION'].unique().shape[0]
    number_of_weeks = qos_curves['WEEK_START'].unique().shape[0]

    logging.info(f'qos_data contains {number_of_locations} Locations and {number_of_weeks} weeks')

    logging.info('Transform qos data.')
    inventory_curves, consumption_curves = transform_qos_data(
        qos_data=qos_data, qos_curves=qos_curves)

    logging.info('Create product inventory.')
    product_inventory_grid = create_product_inventory(inventory_curves)

    logging.info('Create full time grid.')
    time_point_grid = create_full_time_grid(consumption_curves)

    logging.info('Calculate product availability ratio.')
    product_availability_ratio = calc_product_availability_ratio(
        product_inventory_grid,
        time_point_grid
    )

    logging.info('Interpolate consumption curves datapoints.')
    consumption_curves_interp = interpolate_consumption_curves(
        consumption_curves,
        time_point_grid
    )

    logging.info('Calculate quality of service.')    
    qos = calc_quality_of_service(
        consumption_curves_interp,
        product_availability_ratio
    )

    if config['use_db']:
        logging.info('Write data to database.')
        db_connect.establish_connection()
        db_connect.db_write_data(
            data=qos,
            target_table=config['db_output_table'],
            target_schema=config['db_output_schema']
        )
        db_connect.close_connection()

    else:
        logging.info('Write output data to csv file.')
        write_data(
            data=qos,
            filename='qos_output',
            output_path=config['paths']['output']
        )

    logging.info('Quality of Service calculation finished succesfully.')

if __name__ == '__main__':
    current_date = datetime.now().strftime("%Y%m%d")
    logger = CustomLogger(log_file=f"qos_{current_date}.log")

    try:
        main()
    except pd.errors.MergeError as me:
        logging.error(f'MergeError occurred: {me}\n{traceback.format_exc()}')
        # Custom handling or logging for MergeError
        raise me  # Raise the exception again if needed
    except ValueError as ve:
        logging.error(f'ValueError occurred: {ve}\n{traceback.format_exc()}')
        # Custom handling or logging for ValueError
        raise ve  # Raise the exception again if needed
    except TypeError as te:
        logging.error(f'TypeError occurred: {te}\n{traceback.format_exc()}')
        # Custom handling or logging for TypeError
        raise te  # Raise the exception again if needed
    except Exception as e:
        logging.error(f'{e}\n{traceback.format_exc()}')
        raise
