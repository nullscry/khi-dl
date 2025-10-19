# khi-dl

A small command-line utility to download full album pages from KHInsider and save the tracks locally, organizing them into a folder named after the album title. The tool will also download the first album image on the page (if available) and embed it into each downloaded track's metadata (supports MP3 and FLAC).

NOTE: This is currently very poorly tested so expect bugs for now!

Features
- Scrapes a KHInsider album page for track download links
- Downloads tracks concurrently
- Creates an output folder derived from the page title (everything before " - Download")
- Downloads the first image inside `<div class="albumImage">` and embeds it as cover art in MP3 and FLAC files
- Decodes URL-encoded filenames (e.g. `%20` -> space)

Requirements
- Python >=3.10
- The following Python packages (installed automatically if using the provided `pyproject.toml`):
  - requests
  - beautifulsoup4
  - mutagen
  - filetype

Usage

Run the script with a KHInsider album URL:

```bash
python main.py <KHINSIDER_ALBUM_URL> [--format mp3|flac]
```

Configuration
- You can set the `KHINSIDER_OUTPUT` environment variable to change the base output directory. By default files are saved into the current working directory.

License
- License: MIT (see `LICENSE`)

Notes & Limitations
- The script sets a browser-like User-Agent header to avoid simple anti-bot blocks. If KHInsider changes their protections, you may need additional handling.
- Album art embedding uses `mutagen` and supports MP3 and FLAC. Other audio formats are downloaded but won't receive embedded art.
- Use responsibly and follow KHInsider's terms of service and copyright rules.

Contributing
Pull requests and issues welcome.
