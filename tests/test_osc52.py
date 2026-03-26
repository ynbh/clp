import os
import unittest
from io import StringIO
from unittest.mock import patch

from clp.main import build_osc52_sequence, main, parse_args, should_read_from_stdin


class FakeStdin(StringIO):
    def __init__(self, value: str, *, is_tty: bool) -> None:
        super().__init__(value)
        self._is_tty = is_tty

    def isatty(self) -> bool:
        return self._is_tty


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


class InputModeTests(unittest.TestCase):
    def test_parse_args_allows_missing_file_path(self) -> None:
        args = parse_args([])
        self.assertIsNone(args.file_path)

    def test_reads_from_stdin_when_dash_is_passed(self) -> None:
        self.assertTrue(should_read_from_stdin(parse_args(["-"]).file_path, FakeStdin("", is_tty=True)))

    def test_reads_from_stdin_when_input_is_piped(self) -> None:
        self.assertTrue(should_read_from_stdin(None, FakeStdin("hello", is_tty=False)))

    def test_requires_file_or_piped_stdin(self) -> None:
        stderr = StringIO()
        with patch("sys.stderr", stderr), patch("sys.stdin", FakeStdin("", is_tty=True)):
            exit_code = main([])

        self.assertEqual(exit_code, 1)
        self.assertIn("missing input", stderr.getvalue())

    def test_copies_piped_stdin(self) -> None:
        stdout = StringIO()
        with (
            patch("pyperclip.copy") as copy_mock,
            patch("sys.stdout", stdout),
            patch("sys.stdin", FakeStdin("hello", is_tty=False)),
        ):
            exit_code = main(["--clipboard-mode", "local"])

        self.assertEqual(exit_code, 0)
        copy_mock.assert_called_once_with("hello")
        self.assertIn("copied 5 characters from stdin to clipboard", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
