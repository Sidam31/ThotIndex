"""
Module to fetch image URLs from APHP archive website.
"""
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote
import logging
import json

logger = logging.getLogger(__name__)


class WebFetcher:
    """Fetches image URLs from APHP archive web pages."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_image_url(self, archive_url):
        """
        Fetch the full-resolution image URL from an archive page.
        
        Args:
            archive_url (str): URL of the archive page
            
        Returns:
            tuple: (image_url, cote, page) or (None, None, None) on error
        """
        try:
            logger.info(f"Fetching archive page: {archive_url}")
            response = self.session.get(archive_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Find the Binocle JSON configuration
            # Look for the script tag containing binocle configuration
            script_tags = soup.find_all('script', type='text/javascript')
            binocle_json_url = None
            
            for script in script_tags:
                if script.string and 'binocle' in script.string:
                    # Look for the JSON source URL - handle escaped slashes \/
                    # Pattern matches: "source":"https://...BIN_xxx.json?..."
                    json_match = re.search(r'"source"\s*:\s*"(https?:[^"]+\.json[^"]*)"', script.string)
                    if json_match:
                        # Unescape the slashes
                        binocle_json_url = json_match.group(1).replace('\\/', '/')
                        break
            
            if not binocle_json_url:
                logger.error("Could not find Binocle JSON URL in page")
                return None, None, None
            
            logger.info(f"Found Binocle JSON URL: {binocle_json_url}")
            
            # Fetch the JSON data
            json_response = self.session.get(binocle_json_url, timeout=30)
            json_response.raise_for_status()
            binocle_data = json_response.json()
            
            # Extract page number from URL (e.g., /daogrp/0/16)
            page_match = re.search(r'/daogrp/\d+/(\d+)', archive_url)
            if not page_match:
                logger.error("Could not extract page number from URL")
                return None, None, None
            
            page_index = int(page_match.group(1)) - 1  # Pages are 1-indexed in URL
            
            # Get the items list
            items = binocle_data.get('items', [])
            
            if page_index < 0 or page_index >= len(items):
                logger.error(f"Page index {page_index} out of range (0-{len(items)-1})")
                return None, None, None
            
            # Get the selected item
            item = items[page_index]
            
            # Extract image information
            # Use the 'printable' URL for full-size image, or construct from 'source'
            image_url = item.get('printable')
            if not image_url:
                # Fallback: construct from source
                source_path = item.get('source', '')
                if source_path:
                    # Build IIIF URL for full resolution
                    base_url = "https://aphp-diffusion-prod.ligeo-archives.com/cgi-bin/iipsrv.fcgi"
                    image_url = f"{base_url}?FIF={source_path}&CVT=JPG"
            
            # Extract cote and page from classeur information
            classeur = item.get('classeur', {})
            cote = classeur.get('unitid', 'unknown')
            image_base = classeur.get('strImageBase', '')
            
            # Extract page number from image base name
            # Example: FRAPHP075_001_2009_00016 -> page is 00016
            page_num_match = re.search(r'(\d+)$', image_base)
            page = page_num_match.group(1) if page_num_match else str(page_index + 1).zfill(5)
            
            # Clean up cote for filename (replace / with _)
            cote_clean = cote.replace('/', '_')
            
            logger.info(f"Found image URL: {image_url}")
            logger.info(f"Extracted cote: {cote_clean}, page: {page}")
            
            return image_url, cote_clean, page
            
        except requests.RequestException as e:
            logger.error(f"Network error fetching archive page: {e}")
            return None, None, None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON data: {e}")
            return None, None, None
        except Exception as e:
            logger.error(f"Error parsing archive page: {e}")
            return None, None, None
