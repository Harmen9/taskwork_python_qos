'''
This script launches a simple api webserver to serve the Quality of Service output.
It will run locally on http://127.0.0.1:8000
This is run in development mode. To run it in production a WSGI server should be used.
In addition additional measures such as security and authentication should be added.

Contains the following endpoints:
    - /qos serves as a general endpoint to get all QoS data.
    - /qos/location/<location> allows filtering QoS data by location.
    - /qos/week/week_start provides filtering by date. The week_start should be in format: dd.mm.yyyy.
    - /qos/location/<location>/<week_start> offers combined filtering by both location and date.
'''

from flask import Flask, jsonify
from pathlib import Path
from _qos_read_write import read_config
import csv

app = Flask(__name__)

base_path: Path = Path(__file__).parent.parent
config_path = base_path / 'solution' / 'qos_config.json'
config = read_config(base_path, config_path)
output_file = config['paths']['output'] / 'qos_output.csv'
# Example data (replace this with your actual QoS data)
qos_data = []

with open(output_file, encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        qos_data.append(row)

@app.route('/qos', methods=['GET'])
def get_qos_data():
    '''Endpoint to get all QoS data'''
    return jsonify(qos_data)

@app.route('/qos/location/<location>', methods=['GET'])
def get_qos_by_location(location):
    '''Endpoint to get QoS data by location'''
    result = [i for i in qos_data if i['LOCATION'] == location]
    return jsonify(result)

@app.route('/qos/location/<location>/<week_start>', methods=['GET'])
def get_qos_by_location_and_date(location, week_start):
    '''Endpoint to get QoS data by location and date'''
    location = [i for i in qos_data if i['LOCATION'] == location]
    result = [i for i in location if i['WEEK_START'] == week_start]
    return jsonify(result)


@app.route('/qos/week/<week_start>', methods=['GET'])
def get_qos_by_date(week_start):
    '''Endpoint to get QoS data by week_start'''
    result = [i for i in qos_data if i['WEEK_START'] == week_start]
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)