import io
import unittest
from hashlib import sha256
from unittest.mock import Mock, patch

from scripts.verify_deployment import deploy, matches


class DeploymentTests(unittest.TestCase):
    def test_bytes_must_match(self):
        files = {"data/status.json": sha256(b"new").hexdigest()}
        opener = Mock()
        opener.open.return_value = io.BytesIO(b"old")
        self.assertFalse(matches("https://example.pages.dev", files, opener))
        opener.open.return_value = io.BytesIO(b"new")
        self.assertTrue(matches("https://example.pages.dev", files, opener))

    def test_incomplete_configuration_fails(self):
        deploy(None, None)
        with self.assertRaises(ValueError):
            deploy("https://example.pages.dev", "")
        with self.assertRaises(ValueError):
            deploy("http://example.invalid", "invalid")

    @patch("scripts.verify_deployment.time.sleep")
    @patch("scripts.verify_deployment.build_opener")
    @patch("scripts.verify_deployment.matches", side_effect=[False, False, True])
    def test_hook_then_production_check(self, compare, build, sleep):
        http = build.return_value.open.return_value
        http.__enter__.return_value.status = 200
        deploy("https://example.pages.dev", "https://api.cloudflare.com/client/v4/pages/webhooks/deploy_hooks/example")
        self.assertEqual(compare.call_count, 3)
        self.assertEqual(build.return_value.open.call_count, 1)
