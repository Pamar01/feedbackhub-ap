import os
import tempfile
import unittest

from app import create_app

VALID = {
    "name": "Asha",
    "email": "Asha@Example.com",
    "channel": "mobile",
    "rating": 5,
    "message": "Great app, really easy to use",
}


class ApiTests(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".sqlite")
        os.close(fd)
        self.app = create_app({"TESTING": True, "DATABASE": self.path})
        self.client = self.app.test_client()

    def tearDown(self):
        os.remove(self.path)

    def post(self, **overrides):
        return self.client.post("/api/feedback", json={**VALID, **overrides})

    def test_health(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json(), {"status": "ok"})

    def test_create_and_fetch(self):
        res = self.post()
        self.assertEqual(res.status_code, 201)
        body = res.get_json()
        self.assertEqual(body["email"], "asha@example.com")
        self.assertEqual(body["sentiment"], "positive")
        self.assertEqual(res.headers["Location"], f"/api/feedback/{body['id']}")

        fetched = self.client.get(f"/api/feedback/{body['id']}")
        self.assertEqual(fetched.status_code, 200)
        self.assertEqual(fetched.get_json()["name"], "Asha")

    def test_validation_errors(self):
        res = self.post(rating=9, email="nope", message="hi")
        self.assertEqual(res.status_code, 400)
        details = res.get_json()["details"]
        self.assertEqual(set(details), {"rating", "email", "message"})

    def test_rejects_boolean_rating_and_bad_channel(self):
        self.assertEqual(self.post(rating=True).status_code, 400)
        self.assertEqual(self.post(channel="fax").status_code, 400)

    def test_rejects_non_json_body(self):
        res = self.client.post("/api/feedback", data="not json", content_type="text/plain")
        self.assertEqual(res.status_code, 400)

    def test_pagination_and_filters(self):
        for i in range(5):
            self.post(channel="web" if i % 2 else "mobile")
        body = self.client.get("/api/feedback?per_page=2&page=2").get_json()
        self.assertEqual(body["total"], 5)
        self.assertEqual(body["pages"], 3)
        self.assertEqual(len(body["items"]), 2)

        web = self.client.get("/api/feedback?channel=web").get_json()
        self.assertEqual(web["total"], 2)

        self.assertEqual(self.client.get("/api/feedback?page=abc").status_code, 400)
        self.assertEqual(self.client.get("/api/feedback?sentiment=meh").status_code, 400)

    def test_delete(self):
        fid = self.post().get_json()["id"]
        self.assertEqual(self.client.delete(f"/api/feedback/{fid}").status_code, 204)
        self.assertEqual(self.client.get(f"/api/feedback/{fid}").status_code, 404)
        self.assertEqual(self.client.delete(f"/api/feedback/{fid}").status_code, 404)

    def test_summary(self):
        empty = self.client.get("/api/analytics/summary").get_json()
        self.assertEqual(empty["total"], 0)
        self.assertIsNone(empty["average_rating"])

        self.post(rating=5)
        self.post(rating=1, message="Terrible and slow, very frustrating")
        s = self.client.get("/api/analytics/summary").get_json()
        self.assertEqual(s["total"], 2)
        self.assertEqual(s["average_rating"], 3.0)
        self.assertEqual(s["by_sentiment"]["positive"], 1)
        self.assertEqual(s["by_sentiment"]["negative"], 1)
        self.assertEqual(s["rating_distribution"]["5"], 1)

    def test_csv_export_neutralises_formulas(self):
        self.post(name="=cmd()")
        res = self.client.get("/api/feedback/export")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, "text/csv")
        self.assertIn("'=cmd()", res.get_data(as_text=True))

    def test_index_page(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"FeedbackHub", res.data)


if __name__ == "__main__":
    unittest.main()
