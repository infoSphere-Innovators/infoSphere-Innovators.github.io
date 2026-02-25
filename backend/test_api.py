import unittest
import requests

BASE = "http://127.0.0.1:5000"

class TestAPI(unittest.TestCase):
    def test_predict(self):
        r = requests.get(f"{BASE}/predict/steel")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("current_price", data)
        self.assertIn("pred_7d", data)
        self.assertIn("pred_30d", data)
        self.assertIn("confidence_pct", data)
        self.assertIn("forecast_prices", data)

    def test_market_insight(self):
        r = requests.get(f"{BASE}/market-insight/steel")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("risk", data)
        self.assertIn("sentiment", data)
        self.assertIn("insight", data)
        self.assertIn("all_insights", data)

    def test_materials_today(self):
        r = requests.get(f"{BASE}/materials-today")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)
        self.assertIn("name", data[0])
        self.assertIn("price", data[0])

    def test_footer_data(self):
        r = requests.get(f"{BASE}/footer-data")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("diesel_price", data)
        self.assertIn("exchange_rate", data)
        self.assertIn("regional_inflation", data)

if __name__ == "__main__":
    unittest.main()
