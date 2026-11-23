import tempfile
import unittest
from pathlib import Path

from app.recognition import apply_endpoint_silence, endpoint_conf

CONF = """--min-active=200
--endpoint.rule2.min-trailing-silence=0.5
--endpoint.rule3.min-trailing-silence=0.75
--endpoint.rule4.min-trailing-silence=1.0
"""


class EndpointConfigTests(unittest.TestCase):
    def test_rules_scale_together(self):
        text = endpoint_conf(CONF, 0.3)
        self.assertIn("rule2.min-trailing-silence=0.300", text)
        self.assertIn("rule3.min-trailing-silence=0.450", text)
        self.assertIn("rule4.min-trailing-silence=0.600", text)
        self.assertIn("--min-active=200", text)
        self.assertEqual(endpoint_conf(text, 0.5), endpoint_conf(CONF, 0.5))

    def test_missing_rules_are_not_rewritten(self):
        self.assertIsNone(endpoint_conf("--min-active=200\n", 0.3))

    def test_apply_keeps_one_original_backup(self):
        with tempfile.TemporaryDirectory() as folder:
            conf = Path(folder) / "conf" / "model.conf"
            conf.parent.mkdir()
            conf.write_text(CONF, encoding="utf-8")
            self.assertTrue(apply_endpoint_silence(folder, 0.3))
            self.assertTrue(apply_endpoint_silence(folder, 0.5))
            self.assertEqual((conf.parent / "model.conf.original").read_text(encoding="utf-8"), CONF)
            self.assertIn("rule2.min-trailing-silence=0.500", conf.read_text(encoding="utf-8"))
            self.assertFalse(apply_endpoint_silence(Path(folder) / "missing", 0.3))


if __name__ == "__main__":
    unittest.main()
