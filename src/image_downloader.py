"""
Module to download images from URLs.
"""
import os
import requests
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ImageDownloader:
    """Downloads images from URLs and saves them with appropriate names."""
    
    def __init__(self, download_dir=None):
        """
        Initialize the image downloader.
        
        Args:
            download_dir (str): Directory to save downloaded images
        """
        self.download_dir = download_dir or os.path.join(os.getcwd(), 'downloaded_images')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def download_image(self, image_url, cote, page):
        """
        Download an image and save it with a clear filename.
        
        Args:
            image_url (str): URL of the image to download
            cote (str): Cote identifier
            page (str): Page number
            
        Returns:
            str: Path to the downloaded image, or None on error
        """
        try:
            # Create download directory if it doesn't exist
            Path(self.download_dir).mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            filename = f"{cote}_{page}.jpg"
            filepath = os.path.join(self.download_dir, filename)
            
            logger.info(f"Downloading image to: {filepath}")
            
            # For IIIF servers, we need to request the full resolution image
            # Remove thumbnail parameters and request full size
            if 'iipsrv.fcgi' in image_url:
                # Add parameters for full resolution JPEG conversion
                if '?' in image_url:
                    # Check if it already has parameters
                    if '&CVT=JPG' not in image_url:
                        image_url += '&CVT=JPG'
                    # Remove size limitations
                    import re
                    image_url = re.sub(r'&HEI=\d+', '', image_url)
                    image_url = re.sub(r'&WID=\d+', '', image_url)
                    image_url = re.sub(r'&SIZE=\d+', '', image_url)
            
            # Download the image
            response = self.session.get(image_url, timeout=60)
            response.raise_for_status()
            
            # Save to file
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Successfully downloaded image: {filename}")
            return filepath
            
        except requests.RequestException as e:
            logger.error(f"Network error downloading image: {e}")
            return None
        except IOError as e:
            logger.error(f"File I/O error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading image: {e}")
            return None
    
    def set_download_directory(self, directory):
        """
        Set the download directory.
        
        Args:
            directory (str): Path to download directory
        """
        self.download_dir = directory
        logger.info(f"Download directory set to: {directory}")
