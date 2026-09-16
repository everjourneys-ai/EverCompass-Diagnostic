import unittest

from api_helpers import make_client


class HealthTests(unittest.TestCase):
    def test_health_returns_ok(self):
        client = make_client()
        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


if __name__ == "__main__":
    unittest.main()
