
# Quality of Service algorithm

## Description

This algorithm calculates the Quality of Service metric as described in TAKS_DESCRIPTION.md. The result is written to a csv file in the output folder or written to a postgres database.

It contains the following steps:
* `read_qos_data`: Data is read (from database or csvs) and converted to the correct data type.
* `transform_qos_data`: The input data is transformed into 2 dataframes:
    * `inventory_curves`: DataFrame containing the qos_curves for CURVE_TYPE = 'inventory'. Including the corresponding location and CONSUMPTION_PROFILE_CURVE_ID from qos_data.
    * `consumption_curves`: DataFrame containing the qos_curves for CURVE_TYPE = 'consumption_profile'. Including the corresponding LOCATION from qos_data.
* `create_product_inventory`: A full inventory grid for all the data points at a certain location and week_start is created. This contains the inventory state for all products at all timepoints at a certain location. Similar to step 1 in the TASK_DESCRIPTION.md.
* `create_full_time_grid`: a full grid of all the timepoints in a week is created. This is later used to forward fill and interpolate the data.
* `calc_product_availability_ratio`: The product availability ratio is calculated for all locations at all timepoints during a week. Similar to step 2 in the TASK_DESCRIPTION.md
* `interpolate_consumption_curves`: The consumption_curves are linearly interpolated for all timepoints during the week.
* `calc_quality_of_service`: The quality of service is measured. Similar to step 4 in the TASK_DESCRIPTION.md



## Project structure
* `output` folder will contain the output.
* `logs` folder will contain the logs
* `raw_data` folder contains the input csv'ps `qos_curves.csv` and `qos_data.csv`
* `solution` folder contains the following files and folders:
    * `main.py` the main script. Running this will run the algorithm.
    * `_qos_*.py` These files are used by the `main.py` and contain the functions.
    * `qos_config.json` Contains the configuration for the qos algorithm, such as paths and type of data load.
    * `qos_api.py` Script to run the API.
    * `logger.py` Contains the logger class, used by `main.py` to write logs.
    * `db_initialisation.py` Contains the script to create schemas and tables and load the data to the database.
    * `_db_connection.py` Contains the database scripts to connect to a postgres database.
    * `tests.py` Runs the unit tests. These tests are stored in the `tests` folder.
    * `tests` folder. Contains:
        * `test_*.py` The files that contain the unit tests.
        * `test_data` Folder that contains the csv data, used by the unit tests.


## Running the code
To run the code you can create a venv based on the requirements.txt file and use pip to install the required packages.

* Download or clone the directory `taskwork_python_qos`
* `cd` into the directory
* Initialise a new venv: `python -m venv qos_myenv`
* Activate the venv:
    * Windows: `myenv\Scripts\activate`
    * Linux/Mac: `source myenv/bin/activate`
* Use pip to install the packages: `pip install -r requirements.txt`
* Run the file `main.py` in the `solution` folder using the interpreter of the venv.

To run the tests:
* Use the interpreter of the venv.
* Run `tests.py`. This will run the `test_*.py` files in the `tests` folder. 


## Configuration

The file qos_config.json contains the variables to choose to use a database or the csv.
In addition it contains the output and input paths for the csv's when csvs are used.
The paths support both relative paths (to the qos script base folder) as absolute paths.
```
{
	"use_db": false,
	"db": {
		"host": "",
    	"database": "",
     	"username": "",
     	"password": ""
    },
	"db_qos_data_table": "stg.qos_data",
	"db_qos_curves_table": "stg.qos_curves",
	"db_output_table": "quality_of_service",
	"db_output_schema": "qos",
    "paths": {
        "input": "raw_data",
        "output": "output"
    }
}
```

## API
A simple API is created using Flask to serve the qos_output data. 
It will run locally on http://127.0.0.1:8000
This will run in development mode. To run it in production a WSGI server should be used.
In addition additional measures such as security and authentication should be added to run the api in production.

### Run the API
* Open the file `qos_api.py`
* Run the file using the venv set-up in the `Running the code` section.
* The API will run locally on `http://127.0.0.1:8000` and can be accessed via the browser or api tools like postman.
* example endpoint: `http://127.0.0.1:5000/qos/location/Architecture%20Star%20Research`

## Database
A database connection is integrated using a postgres database. The code for the database is stored in the script `_db_connection.py`
To use load via the database the `use_db` in the config should be set to `true` and the connection credentials should be provided.

The script `db_initialisation` is used to create the schemas and load the data to the postgres database.

### Endpoints
Contains the following endpoints:
    - /qos serves as a general endpoint to get all QoS data.
    - /qos/location/<location> allows filtering QoS data by location.
    - /qos/week/week_start provides filtering by date. The week_start should be in format: dd.mm.yyyy.
    - /qos/location/<location>/<week_start> offers combined filtering by both location and date.

## Unit tests
There are several unit tests implemented. However, due to time constraints it was not possible to implement all of them. A more extensive list of possible unit tests for each function is listed below.

### _qos_metrics
* read_config:
    * Test if the function raises correct error for missing config files.
    * Test if the function raises correct error for missing input folder in config.
    * Test if the function returns a correct config dictionary using absolute paths.
    * Test if the function returns a correct config dictionary using relative paths.
    * Test if the function raises correct error for incorrect json format. This is actually implemented in the json.load() function so is likely already tested by the package. 
* read_qos_data:
    * Test if the function raises correct error for missing input folder.
    * Check if the returned DataFrames (qos_data and qos_curves) contain the expected columns
    * Test if the list_converter convert the column type to list.
    * Test if the list_converter raises a sensible error in case of an incorrect datatype in the columns for the list.
    * Test if the function correctly reads the expected CSV files ('qos_curves.csv' and 'qos_data.csv') from the input folder.
    * Test if the function handles loading big csv's, in a reasonable time. This will become important if the size of the csv's is likely to grow significantly (many GB's).
* write_data:
    * Test whether the function creates the CSV file with the expected name in the correct output location.
    * Test whether a folder is created in case the output folder doesn't exist.

### _qos_transformations
* transform_qos_data:
    * Test if the qos_data and qos_curves is correctly transformed and returns the expected DataFrame.
    * Test if the function correctly Ensure that the resulting inventory_curves DataFrame contains only 'inventory' CURVE_TYPE.
    * Confirm that the consumption_curves DataFrame contains only 'consumption_profile' CURVE_TYPE.
    * Confirm the amount of rows of inventory_curves and consumption_curves is equal to the rows of qos_curves.
    * Test if the function raise errors in case of an empty DataFrame of qos_data or qos_curves.
    * Test if the correct errors are Raised in case of a missing min X = 0 or missing max X = 10079.

* create_full_time_grid:
    * Test if the function runs correctly without any errors with valid input and Check if the time_point_grid has the correct columns. (implemented)
    * Check if the number of rows and columns in the output matches the expected count. (10080 * distinct(LOCATION, WEEK_START)) (implemented)
    * Ensure X is filled for every row and runs from 0 to 10079. (implemented)
    * Test how the function handles scenarios with empty input or invalid data types. Ensure it raises appropriate exceptions or handles such cases gracefully.

* interpolate_consumption_curves:
    * Test if the function runs correctly without any errors with valid input. (implemented)
    * Check if the time_point_grid has the correct columns. (implemented)
    * Test on test data if the sum of the Y values for a certain week and location sum up to approximately 1. (implemented)
    * Test if the output column CONSUMPTION_Y is not NaN. (implemented)
    * Test if the function handles an empty DataFrame with the correct columns
    * Test if the function raise a sensible error when the amount of values in list X for a record doesn't match the amount of values in list Y.
    * Test if the correct ValueError is Raised with a missing minimum timepoint X = 0 or missing maximum timepoint  X = 10079.


### _qos_metrics

* create_product_inventory:
    * Test output data type (implemented).
    * Test output columns structure (implemented).
    * Test correct output on test data (implemented).
    * Test the correct Raises on incorrect input columns or data type (implemented)
    * Test if the function handles an empty DataFrame with the correct columns
    * Test if the function raise a sensible error when the amount of values in list X for a record doesn't match the amount of values in list Y.
    * Test if the correct ValueError is Raised with a missing minimum timepoint X = 0 or missing maximum timepoint  X = 10079.

* calc_product_availability_ratio:
    * Test output data type (implemented).
    * Test output columns structure (implemented).
    * Test correct output on test data.
    * Test the correct amount of rows for output. (implemented)
    * Test no product availability ratio is higher than 1.0 or lower than 0.0 and do not contain NaN. (implemented)
    * Test the correct Raises on incorrect input columns or data type 
    * Test the correct MergeErrors are Raised if multiple 'LOCATION', 'WEEK_START', 'X' in the time point grid match the product availability ratio dataframe.

* calc_quality_of_service:
    * Test if the function correctly shows the output for artificial created data with a known constant product availability ratio (for example a constant 50%). Ensure the QoS will be 50% as well.
    * Test output data type (implemented).
    * Test output columns structure (implemented).
    * Test if the QoS is between 0 and 1 and does not contain NaN (implemented).
    * Test the correct Raises on incorrect input columns or data type 
    * Test the correct MergeErrors are Raised if 'LOCATION', 'CONSUMPTION_PROFILE_CURVE_ID', 'WEEK_START', 'X' of consumption_curves_interp doesn't match one-to-one on product_availability_ratio.

### API
* Test if the endpoints can be accessed succesfully (implemented).
* Test if the data types that are returned are correct.

## Improvements for the algorithm:
#### Data Checks
There are several data checks performed in the algorithm, such as:
* Checks on the uniqueness of the curve id's during a merge.
* Checks for the data types of input data.
* Checks if all X values in the curves data contain a 0 and 10079 value as minimum and maximum.

When these checks fail the algorithm will crash with a sensible exception. While running the algorithm in production this could lead to problems, since a problem at a single location will lead to problems for all other locations. When running the algorithm in production, you would typically want to discover these problems earlier in the data (for example in the database using dbt) and filter the input data in the way that it by definition only receives clean data.

Another option would be to clean potential issues in the data in the algorithm. However, it's important that people would be notified when this is done, so that potential data issues, will not go unnoticed. 

#### Error Handling
The current algorithm raises some errors in case of incorrect data input for the functions or MergeErrors. However, not all errors raised by packages are correctly handled with a custom message. This could be further tested and improved. 
In addition the logging does not contain all the possible error types that could be raised, the others will go to the general exception.
 

### Performance
The algorithm uses vector operations using the pandas package instead of for loops, for performance reasons. The algorithm should therefore also perform when the datasets grows bigger with many locations, products and weeks. However, there are still various areas of improvements:
* Indexes: The current dataframe operations such as `merge` are currently done using regular columns. Using a `join` on indexes would likely improve the performance of the algorithm. However, it would bring the additional complexity and computational of changing the index for different operations.
* Memory optimization: due to the vectorised approach the variables in memory can become rather big. This could cause perfomance issues in cases the data grows. The DataFrame with the biggest risk will be the `product_inventory_grid` which contains all the LOCATIONS, WEEK_START, PRODUCTS for all the timepoints X in the qos_curves. To prevent the DataFrame to become very big, the algorithm only fills the `product_inventory_grid` for all the timepoints X for that specific LOCATIONS and WEEK_START in the qos_curves data. In case the original data would contain the X value for all the minutes in the week, the dataframe will become very big. To make the algorithm more performant, you could first filter the qos_curves on the timepoints X that contain a change. In that case `product_inventory_grid` will also stay small when all the timepoints X are in the data.

### Quality Of Service Metric
There are several potential points of improvements to the calculation metric of the QOS: 

* Apply higher weight to more popular (better selling) items. Currently all the products are rated equally. However in practice it's likely that not every product is equally important for the clients. This could be taken into account by adding a weighted metric to the products based at the sales of the product at a specific client while calculated the product availability ratio. The new formula would in that case be:
<br> ${product\_availability\_ratio}_t = \frac{\sum_{i=1}^{N} \text{importance\_product}_i \times \text{n\_available}_{i, t}}{\sum_{i=1}^{N} \text{importance\_product}_i \times n\_products_t}$  <br> 

* Currently all the products at a customer share the same consumption_curve. However, it is likely that the consumption curve is different for each category of food. For example, breakfast is more consumed in the morning and people won't be unsatisfied when it is not available anymore at 12:00. Based on the product names most Products are main dish, but some products such as the `Spicy Caramel Smoothie` and `Creamy Chocolate Smoothie`, could be popular at a different times of the day than the main dishes. Adding a product category specific consumption_curve could take this into account.

* It is from the description not exactly clear how the consumption profile curves are being determined. If the consumption curves are simply based on the amount of products that are being sold at a certain time for a certain company, it would mean that if there are no products available the consumption would also be very low. This could artificially lead to a better QOS score, since the times when there are no (or no popular) products available, will be weighted less in the metric. A way to adjust for this would be to weigh for each timepoint the moments when there are no items available less at the calculation of the consumer profile curves. In this way the consumer profile curves would be created on a fridge which has enough products available.
