# SENIOR MACHINE LEARNING AND DATA ENGINEER - TASK WORK

## Task description

### Introduction
Your goal is to design an ETL pipeline that combines inventory and consumption data from our fridges to produce a metric that measures the quality of our service. Your task is to create database models, seed the data, and run one pass to compute the metric for all provided locations and weeks.

### Background
Our clients are at the core of our operations and understanding their satisfaction with the services we provide is of great importance to us. We evaluate their happiness through a metric called Quality of Service (QoS). It is defined as <b>a number between 0% and 100%, where 0% means that the fridge was completely empty for all the customers and 100% means that it was full for all the customers willing to make a purchase</b>.

### Data description
In the `raw_data` folder you can find two datasets: `qos_data.csv` and `qos_curves.csv`.

The datasets consist of the following information:

<u>`qos_data.csv`</u>  

| Column name | Data type | Description |
|----------|-------------|------|
| DATE | date | A date for which PRODUCT is in the menu at LOCATION |
| LOCATION | string | Location name |
| PRODUCT | string | Product name |
| INVENTORY_CURVE_ID | integer (fk) | ID of the curve representing inventory levels of PRODUCT at LOCATION in the week of DATE |
| CONSUMPTION_PROFILE_CURVE_ID | integer (fk)| ID of the curve representing consumption at LOCATION in the week of DATE|

<u>`qos_curves.csv`</u>  

| Column name | Data type | Description |
|----------|-------------|------|
| CURVE_ID | integer (pk) | Curve ID |
| CURVE_TYPE | string | Curve type (inventory or consumption profile) |
| WEEK_START | date | Date representing start of the week for which the curve was computed |
| X | array | Array containing minutes elapsed since midnight on WEEK_START |
| Y | array | Array containing values of inventory of consumption percentage corresponding to the values of X|

NOTE: The consumption profiles represent a consumption share at a given location in a given week, calculated on a minute basis. The sum of the area under the consumption profile curve for the entire week is 1. In the data provided for the purpose of this task work, we included only some of the points (not every minute of the week - for storage considerations), but if you interpolate the provided values (e.g., linearly) and sum them up, the sum should be somewhere around 1 (not exactly 1 due to approximation).

### Computation of the QoS metric
Below we explain how the QoS metric itself is computed using an example. Please, note that the figures below do not represent the actual data we provided, but are merely examples.

The QoS metric is computed in the following steps:
1. First, we look at all the products that are on the menu at the given location for the given week. For these products we look at the inventory levels over the full 7 days: <br> ![alt text](https://github.com/felfel-tech/recruiting/blob/main/taskwork_python_qos/images/img_1.png "Plot1")

2. Then, based on the above inventory levels, we compute - for each time instant of the week - the availability ratio according to the formula below: <br> $`product\_availability\_ratio_t = {n\_available_t \over n\_products_t}`$ <br> We don't look at how many items of each product are available, we only care about product variety.

3. After that we compare the product availability ratio with consumption profile for the given location. The consumption profile gives an indication when during the day and week most purchases happen. The availability ratio at times when many purchases happen is more important than the availability ratio at times when almost no purchases happen. <br> In the plot below:
   - the blue line represents product availability ratio calculated based on the inventory data for individual products from the previous plot,
   - the orange line represents consumption profile,
   - both curves belong to the same location and week,
   - the values on the x-axis represent the product availability ratio and the consumption profiles were scaled (normalized) such that  they can be visualized in the same plot - the plot doesn't represent their actual values,
   - the dashed line determines the QoS value of 75% which is typically considered to indicate good quality of service (which is not directly revelant for this task work). <br> ![alt text](https://github.com/felfel-tech/recruiting/blob/main/taskwork_python_qos/images/img_2.png "Plot 2")

5. In the next step, we use a cumulative distribution of the consumption profiles to map absolute time into percentages in the x-axis. We do it to give more importance to those moments where many purchases happen and less to those times of the week when almost no purchases happen. ![alt text](https://github.com/felfel-tech/recruiting/blob/main/taskwork_python_qos/images/img_3.png "Plot 3")

6. In order to compute our QoS metric from the blue curve above, we calculate the area under it resulting in a number between 0% and 100%.

## Your deliverables
1. **Implement and unit test computation of the QoS metric according to the description above, run it for all the given locations and weeks and save the results (e.g., as a csv file).** For time reasons, you don’t have to write very extensive unit tests – it’s enough if you implement a few of them and describe what other aspects of the algorithm you would test. The more the merrier, though :wink:
2. (Optional) Set a database structure using a technology of your choice, ingest the provided data into it and adjust your algorithm such that it reads the data from this database and saves the results in a dedicated table there.
3. (Optional) Implement a web server to serve the final information over HTTP using a RESTful architecture.
4. Consider areas for improvement in this algorithm and list them, along with any other suggestions that occurred to you while working on this task.
