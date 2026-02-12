# clp

`clp` is a small QOL tool that copies file contents to your clipboard.

## usage

```bash
uv run clp path/to/file.txt
```

works with text files and common image files (`png`, `jpg`, `jpeg`, `gif`, `bmp`, `tiff`, `webp`, `heic`, `heif`).

image clipboard support currently requires macos.

## ssh behavior

for text files, `clp` auto-switches to `osc52` when run in an ssh session, so it can copy to the clipboard of the device you are sshing from.

some terminals disable `osc52` by default. if clipboard copy does not work over ssh, enable `osc52` clipboard support in your terminal/ssh app settings.

you can override backend selection:

```bash
clp --clipboard-mode auto path/to/file.txt
clp --clipboard-mode local path/to/file.txt
clp --clipboard-mode osc52 path/to/file.txt
```

note: image copy over ssh is not supported yet.
