import unittest
from qos_api import app  # Assuming the Flask app is in a file named 'app.py'

class TestFlaskAPI(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_get_qos_data(self):
        response = self.app.get('/qos')
        self.assertEqual(response.status_code, 200)

    def test_get_qos_by_location(self):
        location = 'Advanced Building'
        response = self.app.get(f'/qos/location/{location}')
        self.assertEqual(response.status_code, 200)

    def test_get_qos_by_location_and_date(self):
        location = 'Advanced Building'
        week_start = '12.06.2023'
        response = self.app.get(f'/qos/location/{location}/{week_start}')
        self.assertEqual(response.status_code, 200)

    def test_get_qos_by_date(self):
        week_start = '12.06.2023'
        response = self.app.get(f'/qos/week/{week_start}')
        self.assertEqual(response.status_code, 200)
