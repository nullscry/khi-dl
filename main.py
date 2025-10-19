import argparse
import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin, unquote
from concurrent.futures import ThreadPoolExecutor
import threading
from pathlib import Path
from mutagen.id3 import ID3, APIC
from mutagen.mp3 import MP3
from mutagen.flac import FLAC, Picture
import filetype

# Thread-local storage for session reuse
thread_local = threading.local()

def get_session():
    """Get a thread-local session"""
    if not hasattr(thread_local, "session"):
        session = requests.Session()
        # Add a User-Agent to make requests look like they're coming from a browser
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
        })
        thread_local.session = session
    return thread_local.session

def get_output_dir(album_title=None):
    """Get the output directory from environment variable or current working directory"""
    base_dir = os.getenv('KHINSIDER_OUTPUT')
    if base_dir:
        base_path = Path(base_dir)
    else:
        base_path = Path.cwd()
    
    if album_title:
        # Get everything before ' - Download' in the title
        clean_title = album_title.split(' - Download')[0].strip()
        path = base_path / clean_title
        path.mkdir(parents=True, exist_ok=True)
        return path
    return base_path

def apply_album_art(file_path, cover_data):
    """Apply album art to an audio file (MP3 or FLAC)"""
    try:
        # Detect image type using filetype
        kind = filetype.guess(cover_data)
        if kind is None:
            print(f"Warning: Could not determine image type for {file_path}")
            mime_type = 'image/jpeg'  # fallback
        else:
            mime_type = kind.mime

        if str(file_path).lower().endswith('.mp3'):
            audio = MP3(file_path, ID3=ID3)
            # Add ID3 tag if it doesn't exist
            if audio.tags is None:
                audio.add_tags()
            audio.tags.add(
                APIC(
                    encoding=3,  # UTF-8
                    mime=mime_type,
                    type=3,  # Cover (front)
                    desc='Cover',
                    data=cover_data
                )
            )
            audio.save()
        elif str(file_path).lower().endswith('.flac'):
            audio = FLAC(file_path)
            # Remove existing pictures if any
            audio.clear_pictures()
            # Create FLAC picture
            picture = Picture()
            picture.type = 3  # Cover (front)
            picture.mime = mime_type
            picture.desc = 'Cover'
            picture.data = cover_data
            audio.add_picture(picture)
            audio.save()
    except Exception as e:
        print(f"Error applying album art to {file_path}: {e}")

def download_file(url, output_dir=None, cover_data=None):
    """Download a file from the given URL."""
    try:
        session = get_session()
        response = session.get(url)
        if response.status_code == 200:
            filename = unquote(url.split('/')[-1])
            output_path = (output_dir or get_output_dir()) / filename
            
            # Create any necessary parent directories
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            # If it's an MP3 or FLAC file and we have cover art, apply it
            if cover_data and (str(filename).lower().endswith('.mp3') or str(filename).lower().endswith('.flac')):
                apply_album_art(output_path, cover_data)
            
            print(f"Successfully downloaded: {output_path}")
        else:
            print(f"Failed to download from {url}: Status {response.status_code}")
    except Exception as e:
        print(f"Error downloading {url}: {e}")

def get_download_link(detail_url, preferred_format='mp3'):
    """Get the actual download link from the detail page"""
    try:
        session = get_session()
        response = session.get(detail_url)
        if response.status_code != 200:
            print(f"Failed to fetch detail page: {detail_url}")
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        download_links = {}
        
        # Find all download links
        for link in soup.find_all('a'):
            if link.find('span', class_='songDownloadLink'):
                href = link.get('href', '')
                if href.endswith('.mp3'):
                    download_links['mp3'] = href
                elif href.endswith('.flac'):
                    download_links['flac'] = href
        
        # Try to get the preferred format, fallback to mp3
        if preferred_format in download_links:
            return download_links[preferred_format]
        elif preferred_format == 'flac' and 'mp3' in download_links:
            print(f"Warning: FLAC not available for {detail_url}, falling back to MP3")
            return download_links['mp3']
        elif 'mp3' in download_links:
            return download_links['mp3']
            
        return None
    except Exception as e:
        print(f"Error processing detail page {detail_url}: {e}")
        return None

def process_download(detail_url, format='mp3', output_dir=None, cover_data=None):
    """Process a single download including fetching detail page and downloading"""
    download_url = get_download_link(detail_url, format)
    if download_url:
        download_file(download_url, output_dir, cover_data)

def get_album_info(soup, base_url):
    """Extract album title and cover image from the page"""
    # Get the title without ' - Download'
    title = soup.title.string if soup.title else None
    
    # Get the first image from albumImage div
    cover_data = None
    album_image_div = soup.find('div', class_='albumImage')
    if album_image_div:
        img = album_image_div.find('img')
        if img and img.get('src'):
            img_url = urljoin(base_url, img['src'])
            try:
                response = get_session().get(img_url)
                if response.status_code == 200:
                    cover_data = response.content
            except Exception as e:
                print(f"Error downloading album art: {e}")
    
    return title, cover_data

def process_html(html_content, base_url, format='mp3'):
    """Process HTML content and extract download links."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Get album info
    title, cover_data = get_album_info(soup, base_url)
    output_dir = get_output_dir(title)
    
    download_cells = soup.find_all('td', class_='playlistDownloadSong')
    
    download_urls = []
    for cell in download_cells:
        link = cell.find('a')
        if link and link.get('href'):
            detail_url = urljoin(base_url, link['href'])
            download_urls.append(detail_url)
    
    # Use ThreadPoolExecutor for concurrent downloads
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [
            executor.submit(lambda url: process_download(url, format, output_dir, cover_data), url)
            for url in download_urls
        ]
        # Wait for all downloads to complete
        for future in futures:
            future.result()


def main():
    parser = argparse.ArgumentParser(description='Download music files from a webpage.')
    parser.add_argument('url', help='URL of the webpage to download from')
    parser.add_argument('--format', choices=['mp3', 'flac'], default='mp3',
                      help='Format of the files to download (default: mp3)')
    
    args = parser.parse_args()
    
    try:
        # Download and parse the webpage using our session with headers
        session = get_session()
        response = session.get(args.url)
        if response.status_code == 200:
            process_html(response.content, args.url, args.format)
        else:
            print(f"Failed to fetch webpage: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
