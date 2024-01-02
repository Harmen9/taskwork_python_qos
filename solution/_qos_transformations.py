
from typing import Tuple
import pandas as pd

def transform_qos_data(
        qos_data: pd.DataFrame,
        qos_curves: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    '''
    Transforms the input data qos_data and qos_curves to easier handle the data in further steps of
    the quailty of service (qos) algorithm.

    Consists of the following transformations:  
    - The qos_curves are split between the inventory and consumption curves via the CURVE_TYPE.
    - By using a merge on the qos_data the LOCATION column is added to the consuption_curves.
    - By using a merge on the qos_data the LOCATION and CONSUMPTION_PROFILE_CURVE_ID columns are
    added to the consuption_curves.
    The inventory curve will be used for the product availibilty ratio (par) calculations,
    whereas the consumption curve is used together with the par to calculate the qos.


    Parameters:
    - qos_data: DataFrame read from qos_data.csv. 
    See TASK_DESCRIPTION.md for a description of the data.
    - qos_curves: DataFrame read from qos_curves.csv.
    See TASK_DESCRIPTION.md for a description of the data.

    Returns:
    - inventory_curves: DataFrame containing the qos_curves for CURVE_TYPE = 'inventory'.
    Including the corresponding location and CONSUMPTION_PROFILE_CURVE_ID from qos_data.
    - consumption_curves: DataFrame containing the qos_curves for 
        CURVE_TYPE = 'consumption_profile'.
    Including the corresponding LOCATION from qos_data.

    Raises:
    - MergeError the algorithm expects a one-to-one relationship between the qos_curves with
    CURVE_TYPE='inventory' and the distinct LOCATION PRODUCT INVENTORY_CURVE_ID of the qos_data
    if this is not the case a MergeError will be raised. 
    - MergeError the algorithm expects a one-to-one relationship between the qos_curves with
    CURVE_TYPE='consumption_profile' and the distinct 'LOCATION', 'CONSUMPTION_PROFILE_CURVE_ID'
    of the qos_data if this is not the case a MergeError will be raised.  
    '''

    # Drop date from qos_data, we will use the week information from the curves data instead.
    qos_data.drop(columns='DATE', inplace=True)
    qos_data.drop_duplicates(inplace=True)

    # Retrieve the inventory curve
    mask_inventory: pd.Series = qos_curves['CURVE_TYPE'] == 'inventory'
    inventory_curves: pd.DataFrame = qos_curves[mask_inventory]

    inventory_curves = qos_data.merge(
        inventory_curves,
        left_on='INVENTORY_CURVE_ID',
        right_on='CURVE_ID',
        validate='one_to_one'
    )

    # Retrieve consumption profile curve
    mask_consumption: pd.Series = qos_curves['CURVE_TYPE'] == 'consumption_profile'
    consumption_curves: pd.DataFrame = qos_curves[mask_consumption]

    location_consumption: pd.DataFrame = (
        qos_data[['LOCATION', 'CONSUMPTION_PROFILE_CURVE_ID']]
        .drop_duplicates()
    )
    consumption_curves: pd.DataFrame = location_consumption.merge(
        consumption_curves,
        left_on='CONSUMPTION_PROFILE_CURVE_ID',
        right_on='CURVE_ID',
        validate='one_to_one'
    )

    columns_to_drop = [
        'CURVE_TYPE',
        'CURVE_ID'
        ]

    inventory_curves.drop(columns=columns_to_drop, inplace=True)
    consumption_curves.drop(columns=columns_to_drop, inplace=True)

    return inventory_curves, consumption_curves

def create_full_time_grid(consumption_curves: pd.DataFrame) -> pd.DataFrame:
    '''
    Retrieve a time grid with all minute timepoints for each week at each location.
    It only contains the locations that exist at a certain WEEK_START.
    This will be later used to interpolate the consumption_curves data to retrieve
    missing timepoints.

    Parameters:
    - consumption_curves: DataFrame containing the qos_curves for 
        CURVE_TYPE = 'consumption_profile'.
    Contains: "LOCATION", "CONSUMPTION_PROFILE_CURVE_ID, "CURVE_TYPE", "WEEK_START", "X", "Y"

    Returns:
    - time_point_grid: DataFrame containing all the locations at a certain week, with
    all the minute timepoints.
    Contains: "LOCATION", "CONSUMPTION_PROFILE_CURVE_ID", "WEEK_START", "X"
    '''

    # Check if input datatype is correct
    if not isinstance(consumption_curves, pd.DataFrame):
        raise TypeError("Input 'inventory_curves' should be a pd.DataFrame")

    # Check if required columns are present
    required_columns = [
        'LOCATION',
        'CONSUMPTION_PROFILE_CURVE_ID',
        'WEEK_START',
        'X',
        'Y'
        ]
    if not set(required_columns) == set(consumption_curves.columns.tolist()):
        raise ValueError("Input DataFrame consumption_curves does not contain the required columns")

    locations_week: pd.DataFrame = consumption_curves[
        [
            'LOCATION',
            'CONSUMPTION_PROFILE_CURVE_ID',
            'WEEK_START'
        ]
    ]

    time_range: pd.Series = pd.DataFrame(range(10080), columns=['X'])
    time_point_grid = pd.merge(
            locations_week.assign(key=1),
            time_range.assign(key=1),
            on='key'
        ).drop('key', axis=1)

    return time_point_grid


def interpolate_consumption_curves(
        consumption_curves: pd.DataFrame,
        time_point_grid: pd.DataFrame
) -> pd.DataFrame:
    '''
    Linearly interpolates the consumption curves for the missing time points.
    The consumption curves don't contain all the data points for each minutes. This function 
    will linearly interpolate the 'Y' value of the consumption curves.

    Parameters:
    - consumption_curves: DataFrame containing the qos_curves for 
        CURVE_TYPE = 'consumption_profile'. Retrieved from function: transform_qos_data.
    - time_point_grid:  DataFrame containing all the locations at a certain week, with
    all the minute timepoints. Retrieved from function create_full_time_grid.

    Returns:
    - consumption_curves_interp: Interpolated consumption curve including a linearly interpolated
    value for CONSUMPTION_Y for the missing values.
    contains: "LOCATION", "CONSUMPTION_PROFILE_CURVE_ID", "WEEK_START", "X", "CONSUMPTION_Y"
    '''
    # Check if the minimum and maximum of each X is equal to 0 and 10079
    if consumption_curves[consumption_curves['X'].apply(min) != 0].shape[0] != 0:
        raise ValueError("Input consumption_curves contains X column with missing timepoint 0")

    if consumption_curves[consumption_curves['X'].apply(max) != 10079].shape[0] != 0:
        raise ValueError("Input consumption_curves contains X column with missing timepoint 10079")

    consumption_curves = consumption_curves.explode(list('XY'))
    consumption_curves['Y'] = consumption_curves['Y'].astype(float)

    consumption_curves = time_point_grid.merge(
        consumption_curves,
        how='left',
        left_on=['LOCATION', 'CONSUMPTION_PROFILE_CURVE_ID', 'WEEK_START', 'X'],
        right_on=['LOCATION', 'CONSUMPTION_PROFILE_CURVE_ID', 'WEEK_START', 'X']
    )
    consumption_curves_interp: pd.DataFrame = consumption_curves.sort_values(
        by=['LOCATION', 'WEEK_START', 'X']
    )
    consumption_curves_interp['CONSUMPTION_Y'] = consumption_curves_interp['Y'].interpolate(
        method='linear'
    )
    columns_to_drop: list = ['Y']
    consumption_curves_interp.drop(columns=columns_to_drop, inplace=True)

    return consumption_curves_interp
