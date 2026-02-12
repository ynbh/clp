import os
import unittest
from unittest.mock import patch

from clp.main import build_osc52_sequence


class Osc52Tests(unittest.TestCase):
    def test_builds_plain_sequence(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            sequence = build_osc52_sequence("hello")
        self.assertTrue(sequence.startswith("\033]52;c;"))
        self.assertTrue(sequence.endswith("\a"))

    def test_wraps_for_tmux(self) -> None:
        with patch.dict(os.environ, {"TMUX": "1"}, clear=True):
            sequence = build_osc52_sequence("hello")
        self.assertTrue(sequence.startswith("\033Ptmux;\033\033]52;c;"))
        self.assertTrue(sequence.endswith("\a\033\\"))


if __name__ == "__main__":
    unittest.main()
