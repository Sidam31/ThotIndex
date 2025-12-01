import requests
import logging
from packaging import version as pkg_version


def check_for_updates(current_version):
    """
    Check GitHub releases for a newer version.
    
    Args:
        current_version (str): Current version string (e.g., "0.1.0")
    
    Returns:
        tuple: (is_newer_available: bool, latest_version: str or None)
    """
    logger = logging.getLogger(__name__)
    
    try:
        # GitHub API endpoint for latest release
        url = "https://api.github.com/repos/Sidam31/ThotIndex/releases/latest"
        
        # Make request with timeout
        response = requests.get(url, timeout=5)
        
        if response.status_code == 404:
            # No releases yet
            logger.info("No releases found on GitHub")
            return (False, None)
        
        response.raise_for_status()
        
        # Parse JSON
        data = response.json()
        latest_tag = data.get("tag_name", "")
        
        # Remove 'v' prefix if present
        latest_version_str = latest_tag.lstrip('v')
        
        # Compare versions
        try:
            current = pkg_version.parse(current_version)
            latest = pkg_version.parse(latest_version_str)
            
            if latest > current:
                logger.info(f"New version available: {latest_version_str} (current: {current_version})")
                return (True, latest_version_str)
            else:
                logger.info(f"Application is up to date: {current_version}")
                return (False, latest_version_str)
                
        except Exception as e:
            logger.error(f"Failed to parse version strings: {e}")
            return (False, None)
            
    except requests.exceptions.Timeout:
        logger.warning("Version check timed out")
        return (False, None)
    except requests.exceptions.RequestException as e:
        logger.warning(f"Version check failed: {e}")
        return (False, None)
    except Exception as e:
        logger.error(f"Unexpected error during version check: {e}")
        return (False, None)
