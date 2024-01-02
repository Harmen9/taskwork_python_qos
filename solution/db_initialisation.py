from pathlib import Path
import pandas as pd
from _db_connection import PgConnection
from _qos_read_write import read_config, read_qos_data

def main():
    '''
    This function initialises the database to create the necessary schemas and
    tables to load the qos data and loads the data to the tables.
    '''
    base_path: Path = Path(__file__).parent.parent
    config_path = base_path / 'solution' / 'qos_config.json'

    config = read_config(base_path, config_path)

    create_schema = "CREATE SCHEMA stg"
    create_schema_qos = "CREATE SCHEMA qos"
    qos_data, qos_curves = read_qos_data(input_folder=config['paths']['input'])

    with PgConnection(**config['db']) as (engine, conn, cursor):
        cursor.execute(create_schema)
        cursor.execute(create_schema_qos)
        qos_data.to_sql('qos_data', con=engine, schema='stg', if_exists='append', index=False)
        qos_curves.to_sql('qos_curves', con=engine, schema='stg', if_exists='append', index=False)

    print("Schemas and tables created")

if __name__ == '__main__':
    main()

