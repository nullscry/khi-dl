# khi-dl

A small command-line utility to download full album pages from KHInsider and save the tracks locally, organizing them into a folder named after the album title. The tool will also download the first album image on the page (if available) and embed it into each downloaded track's metadata (supports MP3 and FLAC).

NOTE: This is currently very poorly tested so expect bugs for now!

## Features
- Scrapes a KHInsider album page for track download links
- Downloads tracks concurrently
- Creates an output folder derived from the page title (everything before " - Download")
- Downloads the first image inside `<div class="albumImage">` and embeds it as cover art in MP3 and FLAC files
- Decodes URL-encoded filenames (e.g. `%20` -> space)

## Installation

Currently there is no pypi installation option.

You should set the env variable `KHINSIDER_OUTPUT` if you'd like to set the output directory for the downloads. If it is not set, `khi-dl` will download in your current working directory.

You can either download the main py (or clone the repo if you want) and run it like so:

```bash
python main.py <KHINSIDER_ALBUM_URL> [--format mp3|flac]
```

Or you can install it locally with `pip` or `uv` and run it like so:
```bash
uv tool install .                                 # in same directory as main.py
khi-dl <KHINSIDER_ALBUM_URL> [--format mp3|flac]  # khi-dl will automatically be in your PATH
```

## License
- License: MIT (see `LICENSE`)

## Notes & Limitations
- The script sets a browser-like User-Agent header to avoid simple anti-bot blocks. If KHInsider changes their protections, you may need additional handling.
- Use responsibly and follow KHInsider's terms of service and copyright rules.

## Contributing
Pull requests and issues welcome.
