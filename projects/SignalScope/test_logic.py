import unittest
from logic import demo_data, parse_series, flag_anomalies, forecast_seven_days

class TestSignalScope(unittest.TestCase):
    def test_demo_stable(self):
        self.assertTrue(demo_data().equals(demo_data()))
    def test_default_anomalies_detected(self):
        self.assertGreater(flag_anomalies(demo_data(),21,3.2)['alert'].sum(),0)
    def test_forecast(self):
        data = forecast_seven_days(demo_data())
        self.assertEqual(len(data),7)
        self.assertTrue((data['forecast']>=0).all())
    def test_parse(self):
        raw=('date,value\n'+''.join(f'2026-01-{i:02d},{i*3}\n' for i in range(1,16))).encode()
        self.assertEqual(len(parse_series(raw)),15)
    def test_missing_columns(self):
        with self.assertRaises(ValueError):
            parse_series(b'unknown,other\n1,2')

if __name__=='__main__': unittest.main()
