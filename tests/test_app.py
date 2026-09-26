import unittest
from unittest.mock import MagicMock, patch

from app import app, get_supabase


class SupabaseSetupTests(unittest.TestCase):
    def setUp(self):
        self.config = patch.dict(app.config, {
            "TESTING": True,
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_KEY": "test-key",
        })
        self.config.start()
        self.addCleanup(self.config.stop)

    def test_home_without_credentials(self):
        app.config.update(SUPABASE_URL="", SUPABASE_KEY="")
        self.assertEqual(app.test_client().get("/").location, "/login")

    def test_missing_configuration(self):
        app.config["SUPABASE_KEY"] = ""
        result = app.test_cli_runner().invoke(args=["check-supabase"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Set SUPABASE_URL and SUPABASE_KEY", result.output)

    @patch("app.create_client")
    def test_client_is_not_shared_between_requests(self, create):
        create.side_effect = [MagicMock(), MagicMock()]
        with app.test_request_context():
            first = get_supabase()
            self.assertIs(first, get_supabase())
        with app.test_request_context():
            self.assertIsNot(first, get_supabase())
        self.assertEqual(create.call_count, 2)

    @patch("app.create_client")
    def test_connection_check(self, create):
        result = app.test_cli_runner().invoke(args=["check-supabase"])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("connection succeeded", result.output)
        create.return_value.table.assert_called_once_with("study_sessions")

    @patch("app.create_client")
    def test_invalid_configuration_does_not_expose_details(self, create):
        create.side_effect = ValueError("private-key")
        result = app.test_cli_runner().invoke(args=["check-supabase"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Could not initialize Supabase", result.output)
        self.assertNotIn("private-key", result.output)

    @patch("app.create_client")
    def test_remote_failure_does_not_expose_details(self, create):
        query = create.return_value.table.return_value.select.return_value
        query.limit.return_value.execute.side_effect = RuntimeError("private-key")
        result = app.test_cli_runner().invoke(args=["check-supabase"])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Supabase check failed", result.output)
        self.assertNotIn("private-key", result.output)
