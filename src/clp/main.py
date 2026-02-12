from __future__ import annotations

import argparse
import base64
import os
import sys
from pathlib import Path

IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".tiff",
    ".tif",
    ".webp",
    ".heic",
    ".heif",
}
CLIPBOARD_MODES = ("auto", "local", "osc52")


def is_ssh_session() -> bool:
    return any(os.getenv(var) for var in ("SSH_CONNECTION", "SSH_CLIENT", "SSH_TTY"))


def build_osc52_sequence(text: str) -> str:
    encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
    base = f"\033]52;c;{encoded}\a"

    if os.getenv("TMUX"):
        return f"\033Ptmux;\033{base}\033\\"

    if "screen" in (os.getenv("TERM") or ""):
        return f"\033P{base}\033\\"

    return base


def write_to_terminal(sequence: str) -> None:
    try:
        with open("/dev/tty", "w", encoding="utf-8") as terminal:
            terminal.write(sequence)
            terminal.flush()
            return
    except OSError:
        if sys.stderr.isatty():
            sys.stderr.write(sequence)
            sys.stderr.flush()
            return

    raise RuntimeError("no interactive terminal found for osc52 clipboard transfer")


def copy_image_to_clipboard(file_path: Path) -> None:
    if sys.platform != "darwin":
        raise RuntimeError("image clipboard support is currently macos-only")

    from AppKit import NSImage, NSPasteboard, NSPasteboardTypeTIFF

    image = NSImage.alloc().initWithContentsOfFile_(str(file_path))
    if image is None:
        raise RuntimeError(f"failed to read image: {file_path}")

    image_data = image.TIFFRepresentation()
    if image_data is None:
        raise RuntimeError(f"failed to encode image for clipboard: {file_path}")

    pasteboard = NSPasteboard.generalPasteboard()
    pasteboard.clearContents()
    if not pasteboard.setData_forType_(image_data, NSPasteboardTypeTIFF):
        raise RuntimeError("failed to write image to clipboard")

    print(f"copied image from {file_path} to clipboard")


def should_use_osc52(mode: str) -> bool:
    if mode == "osc52":
        return True
    if mode == "local":
        return False
    return is_ssh_session()


def copy_text_to_clipboard(file_path: Path, mode: str) -> None:
    text = file_path.read_text(encoding="utf-8")
    use_osc52 = should_use_osc52(mode)
    if use_osc52:
        write_to_terminal(build_osc52_sequence(text))
        print(f"copied {len(text)} characters from {file_path} to client clipboard (osc52)")
        return

    import pyperclip

    pyperclip.copy(text)
    print(f"copied {len(text)} characters from {file_path} to clipboard")


def copy_file_to_clipboard(file_path: Path, mode: str) -> None:
    if file_path.suffix.lower() in IMAGE_EXTENSIONS:
        if should_use_osc52(mode):
            raise RuntimeError("image clipboard over ssh (osc52) is not supported yet")
        copy_image_to_clipboard(file_path)
        return

    copy_text_to_clipboard(file_path, mode)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="clp")
    parser.add_argument(
        "--clipboard-mode",
        choices=CLIPBOARD_MODES,
        default="auto",
        help="clipboard backend: auto (default), local, or osc52",
    )
    parser.add_argument("file_path", type=Path, help="path to the file to copy")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv if argv is not None else sys.argv[1:])
        copy_file_to_clipboard(args.file_path, args.clipboard_mode)
        return 0
    except ModuleNotFoundError as exc:
        if exc.name == "pyperclip":
            print("error: missing dependency 'pyperclip' (run `uv sync`)", file=sys.stderr)
            return 1
        if exc.name == "AppKit":
            print(
                "error: missing dependency 'pyobjc-framework-cocoa' (run `uv sync`)",
                file=sys.stderr,
            )
            return 1
        print(f"error: missing dependency '{exc.name}'", file=sys.stderr)
        return 1
    except UnicodeDecodeError:
        print("error: file is not valid utf-8 text", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
