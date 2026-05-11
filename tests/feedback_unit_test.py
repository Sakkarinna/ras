import io
import os
import sys
import unittest
from contextlib import redirect_stdout


ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from device.feedback import show_error, show_idle, show_success, show_warning  # noqa: E402


class FeedbackUnitTests(unittest.TestCase):
    def test_feedback_helpers_emit_tagged_console_messages(self):
        stream = io.StringIO()
        with redirect_stdout(stream):
            show_success("ok")
            show_warning("warn")
            show_error("bad")
            show_idle("idle")

        output = stream.getvalue()
        self.assertIn("[SUCCESS] ok", output)
        self.assertIn("[WARNING] warn", output)
        self.assertIn("[ERROR] bad", output)
        self.assertIn("[INFO] idle", output)


if __name__ == "__main__":
    unittest.main()

