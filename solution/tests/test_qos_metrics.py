import unittest
from pathlib import Path
from ast import literal_eval
import pandas as pd

from _qos_metrics import (
    create_product_inventory,
    calc_product_availability_ratio,
    calc_quality_of_service
)
from pandas.testing import assert_frame_equal


class TestCreateProductInventory(unittest.TestCase):
    '''
    Contains the unit tests for the function create_product_inventory
    '''
    def setUp(self):
        # Load test data from test_data folder.
        self.test_folder = Path(__file__).parent / 'test_data'
        self.inventory_curves = pd.read_csv(self.test_folder / 'test_inventory_curves.csv')
        # Convert the X and Y columns to lists.
        self.inventory_curves['X'] = [
            literal_eval(item) for item in self.inventory_curves['X']
        ]
        self.inventory_curves['Y'] = [
            literal_eval(item) for item in self.inventory_curves['Y']
        ]

        self.product_inventory_grid = pd.read_csv(
            self.test_folder / 'test_product_inventory_grid.csv'
        )

    def test_output_datatype(self):
        '''test if the output is of datatype DataFrame.'''
        product_inventory_grid = create_product_inventory(self.inventory_curves.copy())
        self.assertIsInstance(product_inventory_grid, pd.DataFrame)

    def test_output_columns(self):
        '''test if the output contains the correct columns'''
        expected_columns = [
            'LOCATION',
            'WEEK_START',
            'X',
            'INVENTORY_CURVE_ID',
            'PRODUCT',
            'CONSUMPTION_PROFILE_CURVE_ID',
            'Y'
        ]
        product_inventory_grid = create_product_inventory(self.inventory_curves.copy())
        output_columns = product_inventory_grid.columns.tolist()
        self.assertEqual(output_columns, expected_columns)

    def test_expected_output(self):
        '''test if the transformation is providing the expected product_inventory_grid.'''
        product_inventory_grid = create_product_inventory(self.inventory_curves.copy())
        product_inventory_grid.reset_index(drop=True, inplace=True)

        assert_frame_equal(
            self.product_inventory_grid,
            product_inventory_grid,
            check_dtype=False
        )

    def test_incorrect_input_type(self):
        '''test if the correct error is raised in case of an incorrect input type.'''
        dict_input = {}
        with self.assertRaises(TypeError):
            create_product_inventory(dict_input)

    def test_incorrect_input_columns(self):
        '''test if the correct error is raised in case of incorrect input columns.'''
        inventory_curves_incorrect = self.inventory_curves.copy()
        inventory_curves_incorrect.drop(columns='LOCATION', inplace=True)
        with self.assertRaises(ValueError):
            create_product_inventory(inventory_curves_incorrect)


class TestCalcProductAvailabilityRatio(unittest.TestCase):
    '''
    Contains the unit tests for the function calc_product_availability_ratio.
    '''
    def setUp(self):
        # Load test data from test_data folder.
        self.test_folder = Path(__file__).parent / 'test_data'
        self.product_inventory_grid = pd.read_csv(self.test_folder / 'test_product_inventory_grid.csv')
        self.time_point_grid = pd.read_csv(self.test_folder / 'test_time_point_grid.csv')

    def test_output_datatype(self):
        '''test if the output is of datatype DataFrame.'''
        product_availability_ratio = calc_product_availability_ratio(
            self.product_inventory_grid.copy(),
            self.time_point_grid.copy()
            )
        self.assertIsInstance(product_availability_ratio, pd.DataFrame)

    def test_output_columns(self):
        '''test if the output contains the correct columns'''
        expected_columns = [
            'LOCATION',
            'CONSUMPTION_PROFILE_CURVE_ID',
            'WEEK_START',
            'X',
            'PA_RATIO'
        ]
        product_availability_ratio = calc_product_availability_ratio(
            self.product_inventory_grid.copy(),
            self.time_point_grid.copy()
            )
        output_columns = product_availability_ratio.columns.tolist()
        self.assertEqual(output_columns, expected_columns)

    def test_amount_of_rows(self):
        '''test if the amount of rows matches the expected amount of rows'''
        product_availability_ratio = calc_product_availability_ratio(
            self.product_inventory_grid.copy(),
            self.time_point_grid.copy()
            )
        self.assertEqual(self.time_point_grid.shape[0], product_availability_ratio.shape[0])

    def test_par_values(self):
        '''test if the par is not NaN, bigger than 1 or smaller than 0'''
        product_availability_ratio = calc_product_availability_ratio(
            self.product_inventory_grid.copy(),
            self.time_point_grid.copy()
            )
        self.assertEqual(
            product_availability_ratio[product_availability_ratio['PA_RATIO']>1].shape[0],
            0
        )
        self.assertEqual(
            product_availability_ratio[product_availability_ratio['PA_RATIO']<0].shape[0],
            0
        )
        self.assertEqual(
            product_availability_ratio[product_availability_ratio['PA_RATIO'].isnull()].shape[0],
            0
        )

class TestCalcQualityOfService(unittest.TestCase):
    def setUp(self):
        # Load test data from test_data folder.
        self.test_folder = Path(__file__).parent / 'test_data'
        self.product_availability_ratio = pd.read_csv(self.test_folder / 'test_product_availability_ratio.csv')
        self.consumption_curves_interp = pd.read_csv(self.test_folder / 'test_consumption_curves_interp.csv')

    def test_output_datatype(self):
        '''test if the output is of datatype DataFrame.'''
        qos = calc_quality_of_service(
            self.consumption_curves_interp.copy(),
            self.product_availability_ratio.copy()
            )
        self.assertIsInstance(qos, pd.DataFrame)

    def test_output_columns(self):
        '''test if the output contains the correct columns'''
        expected_columns = ['QOS']
        expected_index = ['LOCATION', 'WEEK_START']

        qos = calc_quality_of_service(
            self.consumption_curves_interp.copy(),
            self.product_availability_ratio.copy()
            )
        output_columns = qos.columns.tolist()
        self.assertEqual(output_columns, expected_columns)
        self.assertEqual(qos.index.names, expected_index)
    
    def test_qos_values(self):
        '''test if the qos is not NaN, bigger than 1.02 (compensation for interpolated 
        consumption curves) or smaller than 0'''
        qos = calc_quality_of_service(
            self.consumption_curves_interp.copy(),
            self.product_availability_ratio.copy()
            )
        self.assertEqual(
            qos[qos['QOS']>1.02].shape[0],
            0
        )
        self.assertEqual(
            qos[qos['QOS']<0].shape[0],
            0
        )
        self.assertEqual(
            qos[qos['QOS'].isnull()].shape[0],
            0
        )
