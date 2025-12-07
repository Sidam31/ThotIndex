"""
Module to interact with Google Gemini API for image transcription.
"""
import os
import logging
from pathlib import Path
import google.generativeai as genai
from PIL import Image

logger = logging.getLogger(__name__)


class GeminiAPI:
    """Handles communication with Google Gemini API."""
    
    def __init__(self, api_key=None, prompt_file="Prompt.txt"):
        """
        Initialize the Gemini API client.
        
        Args:
            api_key (str): Google Gemini API key
            prompt_file (str): Path to the prompt file
        """
        self.api_key = api_key
        self.prompt_file = prompt_file
        self.prompt = None
        self.model = None
        
        if api_key:
            self.configure(api_key)
    
    def configure(self, api_key):
        """
        Configure the API with the given key.
        
        Args:
            api_key (str): Google Gemini API key
        """
        try:
            self.api_key = api_key
            genai.configure(api_key=api_key)
            
            # Initialize the model (using Gemini 3 Pro Preview which supports vision)
            self.model = genai.GenerativeModel('gemini-3-pro-preview')
            
            logger.info("Gemini API configured successfully")
        except Exception as e:
            logger.error(f"Error configuring Gemini API: {e}")
            raise
    
    def load_prompt(self):
        """
        Load the prompt from the prompt file.
        
        Returns:
            str: The prompt text, or None on error
        """
        try:
            if not os.path.exists(self.prompt_file):
                logger.error(f"Prompt file not found: {self.prompt_file}")
                return None
            
            with open(self.prompt_file, 'r', encoding='utf-8') as f:
                self.prompt = f.read()
            
            logger.info("Prompt loaded successfully")
            return self.prompt
            
        except Exception as e:
            logger.error(f"Error loading prompt: {e}")
            return None
    
    def transcribe_image(self, image_path):
        """
        Send an image to Gemini API for transcription.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            str: TSV transcription response, or None on error
        """
        try:
            if not self.model:
                logger.error("API not configured. Please set API key first.")
                return None
            
            if not self.prompt:
                self.load_prompt()
            
            if not self.prompt:
                logger.error("No prompt available")
                return None
            
            # Load the image
            logger.info(f"Loading image: {image_path}")
            img = Image.open(image_path)
            
            # Send to Gemini API
            logger.info("Sending image to Gemini API...")
            response = self.model.generate_content([self.prompt, img])
            
            # Extract the text response
            if response and response.text:
                logger.info("Received transcription from Gemini API")
                return response.text
            else:
                logger.error("No response from Gemini API")
                return None
                
        except Exception as e:
            logger.error(f"Error transcribing image: {e}")
            return None
    
    def save_tsv(self, tsv_content, image_path):
        """
        Save TSV content to a file with the same name as the image.
        
        Args:
            tsv_content (str): TSV content to save
            image_path (str): Path to the image file (used to derive TSV filename)
            
        Returns:
            str: Path to the saved TSV file, or None on error
        """
        try:
            # Generate TSV filename from image path
            image_path_obj = Path(image_path)
            tsv_path = image_path_obj.with_suffix('.tsv')
            
            logger.info(f"Saving TSV to: {tsv_path}")
            
            # Save TSV content
            with open(tsv_path, 'w', encoding='utf-8') as f:
                f.write(tsv_content)
            
            logger.info("TSV saved successfully")
            return str(tsv_path)
            
        except Exception as e:
            logger.error(f"Error saving TSV: {e}")
            return None
    
    def process_image(self, image_path):
        """
        Complete workflow: transcribe image and save TSV.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            str: Path to the saved TSV file, or None on error
        """
        try:
            # Transcribe
            tsv_content = self.transcribe_image(image_path)
            
            if not tsv_content:
                return None
            
            # Save TSV
            tsv_path = self.save_tsv(tsv_content, image_path)
            
            return tsv_path
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return None
