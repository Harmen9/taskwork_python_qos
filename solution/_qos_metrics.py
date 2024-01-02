import pandas as pd

def create_product_inventory(
        inventory_curves: pd.DataFrame
) -> pd.DataFrame:
    '''
    Creates for a DataFrame which contains a grid with the inventory (Y) at each of the
    time_points (X) included in the inventory_curves for a locations. X is pivoted so that 
    each row contains the inventory for a specific product at a specific location at a specific
    timepoint. 

    Not every product at a location contains the same time_points. To be able to determine 
    the amount of products in stock at each of the time_points a time_point_grid is created
    with all the time_points at a location. This consumes less memory in cases with many products
    than calculating the inventory at every minute.

    Parameters:
    - inventory_curves: DataFrame containing the qos_curves for CURVE_TYPE = 'inventory'.
    Contains: 'LOCATION', 'PRODUCT', 'INVENTORY_CURVE_ID', 'CONSUMPTION_PROFILE_CURVE_ID',
        'WEEK_START', 'X', 'Y'

    Returns:
    - product_inventory_grid: DataFrame containing a grid with the inventory (Y) at each of the
    time_points (X) for each location.
    Contains: "LOCATION", "WEEK_START", "INVENTORY_CURVE_ID", "PRODUCT",
        "CONSUMPTION_PROFILE_CURVE_ID", "X", "Y"

    Raises:
    - TypeError: If input inventory_curves is not a DataFrame.
    - ValueError: If input inventory_curves does not contain the required columns.
    - ValueError: If a row contains X with a missing timepoint 0 or 10079. This would give problems
        in the forward fill steps in the algorithm.
    '''

    # Check if input datatype is correct
    if not isinstance(inventory_curves, pd.DataFrame):
        raise TypeError("Input 'inventory_curves' should be a pd.DataFrame")

    # Check if required columns are present
    required_columns = [
        'LOCATION',
        'PRODUCT',
        'INVENTORY_CURVE_ID',
        'CONSUMPTION_PROFILE_CURVE_ID',
        'WEEK_START',
        'X',
        'Y'
        ]
    if not set(required_columns) == set(inventory_curves.columns.tolist()):
        raise ValueError("Input DataFrame does not contain the required columns")

    # Check if the minimum and maximum of each X is equal to 0 and 10079
    if inventory_curves[inventory_curves['X'].apply(min) != 0].shape[0] != 0:
        raise ValueError("Input data contains X column with missing timepoint 0")

    if inventory_curves[inventory_curves['X'].apply(max) != 10079].shape[0] != 0:
        raise ValueError("Input data contains X column with missing timepoint 10079")

    # Pivot the lists X and Y
    inventory_curves = inventory_curves.explode(list('XY'))

    # Not each curve has all the stock (Y) at all the possible timepoints.
    # Retrieve a grid with all the timepoints for each week and join this on the full data.
    curve_ids: pd.DataFrame = (
        inventory_curves[['LOCATION', 'INVENTORY_CURVE_ID', 'PRODUCT', 'WEEK_START']]
        .drop_duplicates()
    )

    time_points: pd.DataFrame = inventory_curves[['LOCATION', 'WEEK_START', 'X']].drop_duplicates()
    time_point_grid: pd.DataFrame = time_points.merge(
        curve_ids,
        how = 'left',
        left_on=['LOCATION', 'WEEK_START'],
        right_on=['LOCATION', 'WEEK_START']
    )

    product_inventory_grid: pd.DataFrame = time_point_grid.merge(
        inventory_curves,
        how = 'left',
        left_on=['LOCATION', 'INVENTORY_CURVE_ID', 'WEEK_START', 'PRODUCT', 'X'],
        right_on=['LOCATION', 'INVENTORY_CURVE_ID', 'WEEK_START', 'PRODUCT', 'X']
    )

    # Fill the empty Y with the stock at the last timepoint with available data.
    product_inventory_grid = product_inventory_grid.sort_values(by=['INVENTORY_CURVE_ID', 'X'])
    product_inventory_grid['Y'] = product_inventory_grid.groupby('INVENTORY_CURVE_ID')['Y'].ffill()
    product_inventory_grid['CONSUMPTION_PROFILE_CURVE_ID'] = (
        product_inventory_grid
        .groupby(['LOCATION', 'WEEK_START'])
        ['CONSUMPTION_PROFILE_CURVE_ID']
        .ffill()
    )

    return product_inventory_grid

def calc_product_availability_ratio(
        product_inventory_grid: pd.DataFrame,
        time_point_grid: pd.DataFrame
) -> pd.DataFrame:
    '''
    This function calculates the product availability ratio per time instant and location 
    for each of the timepoints in the time_point_grid.

    distinct_products calculates the total distinct products for each LOCATION and WEEK_START.
    PRODUCT_IN_STOCK is added to determine if a product is in stock for each time instant
    products_in_stock contains the distinct amount of products in stock for each time instant
    Dividing products_in_stock with distinct_products determines the product_availability_ratio.
    The result is merged with the time_point_grid and forward filled to get the product availability
    at every minute.

    Parameters: 
    - product_inventory_grid: DataFrame containing a grid with the inventory (Y) at each of the
    time_points (X) for each location. Retrieved from function 'create_product_inventory'.
    Contains: "LOCATION", "WEEK_START", "INVENTORY_CURVE_ID", "PRODUCT",
        "CONSUMPTION_PROFILE_CURVE_ID", "X", "Y"
    - time_point_grid: DataFrame containing all the locations at a certain week, with
    all the minute timepoints. Retrieved from function create_full_time_grid.

    Returns:
    - product_availability: DataFrame containing the product availability ratio at each minute at 
    each location.
    Contains: "LOCATION", "CONSUMPTION_PROFILE_CURVE_ID", "WEEK_START", "X", "PA_RATIO"

     Raises:
    - TypeError: If input inventory_curves is not a DataFrame.
    - ValueError: If input inventory_curves does not contain the required columns.
    - MergeError: if multiple 'LOCATION', 'WEEK_START', 'X' in the time point grid match the
        product availability ratio dataframe.
    '''

     # Check if input datatype is correct
    if not isinstance(product_inventory_grid, pd.DataFrame):
        raise TypeError("Input 'product_inventory_grid' should be a pd.DataFrame")
    if not isinstance(time_point_grid, pd.DataFrame):
        raise TypeError("Input 'time_point_grid' should be a pd.DataFrame")

    # Check if required columns are present
    required_columns_pig = [
        'LOCATION',
        'PRODUCT',
        'INVENTORY_CURVE_ID',
        'CONSUMPTION_PROFILE_CURVE_ID',
        'WEEK_START',
        'X',
        'Y'
        ]
    if not set(required_columns_pig) == set(product_inventory_grid.columns.tolist()):
        raise ValueError("Input product_inventory_grid does not contain the required columns")

    required_columns_tpg= [
        'LOCATION',
        'CONSUMPTION_PROFILE_CURVE_ID',
        'WEEK_START',
        'X'
        ]
    if not set(required_columns_tpg) == set(time_point_grid.columns.tolist()):
        raise ValueError("Input product_inventory_grid does not contain the required columns")

    # Get DataFrame with the amount of distinct products at each LOCATION and WEEK_START.
    distinct_products: pd.DataFrame = (
        product_inventory_grid
        .groupby(['WEEK_START', 'LOCATION'])['PRODUCT']
        .nunique()
        .reset_index()
    )
    distinct_products.rename(columns={'PRODUCT': 'TOTAL_PRODUCT_COUNT'}, inplace=True)

    # Calculate for each LOCATION WEEK_START AND time_point (X) the amount of products in stock.
    product_inventory_grid['PRODUCT_IN_STOCK'] = (product_inventory_grid['Y'] >= 1).astype(int)
    products_in_stock: pd.DataFrame = (
        product_inventory_grid
        .groupby(['LOCATION', 'WEEK_START', 'X'])
        ['PRODUCT_IN_STOCK']
        .sum()
        .reset_index()
    )

    # Calcualate product availability ratio
    par_data: pd.DataFrame = products_in_stock.merge(
        distinct_products,
        how='left',
        left_on=['LOCATION', 'WEEK_START'],
        right_on=['LOCATION', 'WEEK_START'],
        validate='many_to_one'
    )
    par_data['PA_RATIO'] = par_data['PRODUCT_IN_STOCK'] / par_data['TOTAL_PRODUCT_COUNT']

    # Create product availability ratio for all interpolated time points by forward fill.
    par_data = time_point_grid.merge(
        par_data,
        how='left',
        left_on=['LOCATION', 'WEEK_START', 'X'],
        right_on=['LOCATION', 'WEEK_START', 'X'],
        validate='one_to_one'
    )
    columns_to_drop: list = ['PRODUCT_IN_STOCK', 'TOTAL_PRODUCT_COUNT']
    par_data.drop(columns=columns_to_drop, inplace=True)

    # Fill the empty Y with the stock at the last timepoint with available data.
    product_availability_ratio: pd.DataFrame = par_data.sort_values(
        by=['LOCATION', 'WEEK_START', 'X']
    )
    product_availability_ratio['PA_RATIO'] = (
        product_availability_ratio
        .groupby(['LOCATION', 'WEEK_START'])['PA_RATIO']
        .ffill()
    )

    return product_availability_ratio

def calc_quality_of_service(
        consumption_curves_interp: pd.DataFrame,
        product_availability_ratio: pd.DataFrame
    ) -> pd.DataFrame:
    '''
    Calculates the quality of service for each WEEK_START and at each location.

    Parameters:
    - consumption_curves_interp: Interpolated consumption curve including a linearly interpolated
    value for CONSUMPTION_Y for the missing values. Retrieved from interpolate_consumption_curves.
    Contains: "LOCATION", "CONSUMPTION_PROFILE_CURVE_ID", "WEEK_START", "X", "CONSUMPTION_Y"
    - product_availability: DataFrame containing the product availability ratio at each minute at 
    each location. Retrieved from function calc_product_availability_ratio.
    Contains: "LOCATION", "CONSUMPTION_PROFILE_CURVE_ID", "WEEK_START", "X", "PA_RATIO"

    Returns:
    - qos: Dataframe containing the quality of service at each location at each week.
    Contains: "LOCATION", "WEEK_START", "QOS".

    Raise:
    - MergeError if 'LOCATION', 'CONSUMPTION_PROFILE_CURVE_ID', 'WEEK_START', 'X' of
        consumption_curves_interp doesn't match one-to-one on product_availability_ratio.
    - TypeError: If input data is not a DataFrame.
    - ValueError: If input data does not contain the required columns.
    '''

    if not isinstance(consumption_curves_interp, pd.DataFrame):
        raise TypeError("Input 'consumption_curves_interp' should be a pd.DataFrame")
    if not isinstance(product_availability_ratio, pd.DataFrame):
        raise TypeError("Input 'product_availability_ratio' should be a pd.DataFrame")

    # Check if required columns are present
    required_columns_cci = [
        'LOCATION', 'CONSUMPTION_PROFILE_CURVE_ID', 'WEEK_START', 'X', 'CONSUMPTION_Y'
        ]
    required_columns_par = [
        'LOCATION', 'CONSUMPTION_PROFILE_CURVE_ID', 'WEEK_START', 'X', 'PA_RATIO'
        ]

    if not set(required_columns_cci) == set(consumption_curves_interp.columns.tolist()):
        raise ValueError("Input consumption_curves_interp does not contain the required columns")
    if not set(required_columns_par) == set(product_availability_ratio.columns.tolist()):
        raise ValueError("Input product_availability_ratio does not contain the required columns")

    par_consum_data: pd.DataFrame = consumption_curves_interp.merge(
        product_availability_ratio,
        how='left',
        left_on=['LOCATION', 'CONSUMPTION_PROFILE_CURVE_ID', 'WEEK_START', 'X'],
        right_on=['LOCATION', 'CONSUMPTION_PROFILE_CURVE_ID', 'WEEK_START', 'X'],
        validate='one_to_one'
    )
    par_consum_data['QOS'] = par_consum_data['PA_RATIO'] * par_consum_data['CONSUMPTION_Y']
    qos: pd.Series = par_consum_data.groupby(['LOCATION', 'WEEK_START'])['QOS'].sum()
    qos: pd.DataFrame = pd.DataFrame(qos)

    return qos
