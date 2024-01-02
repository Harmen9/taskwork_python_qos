from sqlalchemy import create_engine
from typing import Tuple
from ast import literal_eval
import pandas as pd

class DBConnection:
    """
    Generic class that connects to a database. On exit the connection is closed.
    Using this class, multiple database types can be implemented.
    """
    def __init__(
            self,
            host: str,
            database: str,
            username: str,
            password: str
            ):
        self.host = host
        self.database = database
        self.username = username
        self.password = password
        self.conn = None
        self.cursor = None
        self.engine = None

    def establish_connection(self):
        """Establishes a connection"""
        raise NotImplementedError("Subclasses must implement this method.")

    def close_connection(self):
        """Closes the open connections"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        if self.engine:
            self.engine.dispose()

    def __enter__(self):
        self.engine, self.conn, self.cursor = self.establish_connection()
        return self.engine, self.conn, self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_connection()


class PgConnection(DBConnection):
    """Establishes a pg database connection using psycopg2. \n
    Please note that this connection has not been tested yet.
    The required arguments are config dictionary including the keys:
     * host
     * database
     * username
     * password. \n"""
    def establish_connection(self):
        """Establishes a connection"""
        connection_string = (
            f"postgresql+psycopg2://{self.username}:{self.password}@{self.host}/{self.database}"
        )
        self.engine = create_engine(connection_string, isolation_level="AUTOCOMMIT")
        self.conn = self.engine.connect()
        self.cursor = self.conn.connection.cursor()

        return self.engine, self.conn, self.cursor

    def db_read_qos_data(
            self, qos_data_table: str, qos_curves_table: str
        ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        '''
        Reads the qos_data and qos_curves from the database and converts the columns "X" and
        "Y" in lists of floats.
        
        Parameters:
        - qos_data_table: the postgres table where the qos_data is stored
        - qos_curves_table: the postgres table where the qos_curves data is stored

        Returns:
        - qos_data
        - qos_curves
        '''
        query_qos_data: str = f'SELECT * FROM {qos_data_table}'
        query_qos_curves: str = f'SELECT * FROM {qos_curves_table}'

        qos_data: pd.DataFrame = pd.read_sql(query_qos_data, con=self.engine)
        qos_curves: pd.DataFrame = pd.read_sql(query_qos_curves, con=self.engine)

        # Convert strings to lists of integers
        qos_curves['X'] = qos_curves['X'].apply(
            lambda x: list(map(float, literal_eval(x.replace('{', '[').replace('}', ']'))))
        )
        qos_curves['Y'] = qos_curves['Y'].apply(
            lambda y: list(map(float, literal_eval(y.replace('{', '[').replace('}', ']'))))
        )

        return qos_data, qos_curves

    def db_write_data(self, data: pd.DataFrame, target_table: str, target_schema: str):
        '''
        Writes a dataframe to a target table.
        
        Parameters:
        - data: the data to write to the table.
        - target_table: the postgres table where the output should be written to.
        - target_schema: the schema to write the data to.
        '''
        data.reset_index(inplace=True)
        data.to_sql(
            target_table,
            con=self.engine,
            schema=target_schema,
            if_exists='append',
            index=False
        )
