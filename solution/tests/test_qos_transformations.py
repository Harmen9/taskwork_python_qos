import unittest
from pathlib import Path
from ast import literal_eval
import pandas as pd

from _qos_transformations import create_full_time_grid, interpolate_consumption_curves

class TestCreateFullTimeGrid(unittest.TestCase):
    '''
    Contains the unit tests for the function create_full_time_grid
    '''
    def setUp(self):
        # Load test data from test_data folder.
        self.test_folder = Path(__file__).parent / 'test_data'
        self.consumption_curves = pd.read_csv(self.test_folder / 'test_consumption_curves.csv')
        # Convert the X and Y columns to lists.
        self.consumption_curves['X'] = [
            literal_eval(item) for item in self.consumption_curves['X']
        ]
        self.consumption_curves['Y'] = [
            literal_eval(item) for item in self.consumption_curves['Y']
        ]

    def test_output_datatype(self):
        '''test if the output is of datatype DataFrame.'''
        time_point_grid = create_full_time_grid(self.consumption_curves.copy())
        self.assertIsInstance(time_point_grid, pd.DataFrame)

    def test_output_columns(self):
        '''test if the output contains the correct columns'''
        expected_columns = [
            'LOCATION',
            'CONSUMPTION_PROFILE_CURVE_ID',
            'WEEK_START',
            'X',
        ]
        time_point_grid = create_full_time_grid(self.consumption_curves.copy())
        output_columns = time_point_grid.columns.tolist()
        self.assertEqual(output_columns, expected_columns)

    def test_amount_of_rows(self):
        '''
        Check if the number of rows and columns in the output matches the expected count.
        (10080 * distinct(LOCATION, WEEK_START))
        '''
        distinct_locations = self.consumption_curves[['LOCATION', 'WEEK_START']].shape[0]
        expected_rows = distinct_locations * 10080
        time_point_grid = create_full_time_grid(self.consumption_curves.copy())
        self.assertEqual(expected_rows, time_point_grid.shape[0])

    def test_output_range_x(self):
        '''
        Ensure X is filled for every row and runs from 0 to 10079.
        distinct(LOCATION, WEEK_START) times.
        '''
        distinct_locations = self.consumption_curves[['LOCATION', 'WEEK_START']].shape[0]
        expected_range = [i for _ in range(distinct_locations) for i in range(10080)]
        time_point_grid = create_full_time_grid(self.consumption_curves.copy())
        self.assertEqual(time_point_grid['X'].tolist(), expected_range)

class TestInterpolateConsumptionCurves(unittest.TestCase):
    '''
    Contains the unit tests for the function interpolate_consumption_curves.
    '''
    def setUp(self):
        # Load test data from test_data folder.
        self.test_folder = Path(__file__).parent / 'test_data'
        self.consumption_curves = pd.read_csv(self.test_folder / 'test_consumption_curves.csv')
        # Convert the X and Y columns to lists.
        self.consumption_curves['X'] = [
            literal_eval(item) for item in self.consumption_curves['X']
        ]
        self.consumption_curves['Y'] = [
            literal_eval(item) for item in self.consumption_curves['Y']
        ]
        self.time_point_grid = pd.read_csv(self.test_folder / 'test_time_point_grid.csv')

    def test_output_datatype(self):
        '''test if the output is of datatype DataFrame.'''
        consumption_curves_interp = interpolate_consumption_curves(
            self.consumption_curves.copy(),
            self.time_point_grid.copy()
        )
        self.assertIsInstance(consumption_curves_interp, pd.DataFrame)

    def test_output_columns(self):
        '''test if the output contains the correct columns'''
        expected_columns = [
            'LOCATION',
            'CONSUMPTION_PROFILE_CURVE_ID',
            'WEEK_START',
            'X',
            'CONSUMPTION_Y'
        ]
        consumption_curves_interp = interpolate_consumption_curves(
            self.consumption_curves.copy(),
            self.time_point_grid.copy()
        )
        output_columns = consumption_curves_interp.columns.tolist()
        self.assertEqual(output_columns, expected_columns)


    def test_sum_consumption_profile(self):
        '''
        Ensure that the sum of the interpolated consumption_profile is not bigger than 1.02
        and smaller than 0.95.
        '''
        consumption_curves_interp = interpolate_consumption_curves(
            self.consumption_curves.copy(),
            self.time_point_grid.copy()
        )
        total_consumption = (
            consumption_curves_interp
            .groupby(['LOCATION', 'WEEK_START'])
            .sum('CONSUMPTION_Y')
        )
        self.assertEqual(
            total_consumption[total_consumption['CONSUMPTION_Y']>1.02].shape[0],
            0
        )
        self.assertEqual(
            total_consumption[total_consumption['CONSUMPTION_Y']<0.98].shape[0],
            0
        )

    def test_consumption_y_not_null(self):
        '''
        Ensure that CONSUMPTION_Y is not NaN.
        '''
        consumption_curves_interp = interpolate_consumption_curves(
            self.consumption_curves.copy(),
            self.time_point_grid.copy()
        )
        self.assertEqual(
            consumption_curves_interp[consumption_curves_interp['CONSUMPTION_Y'].isnull()].shape[0],
            0
        )
