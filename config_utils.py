"""
Configuration utility functions for GenAI-compare application.

This module provides shared configuration loading functionality to avoid code duplication
across multiple scripts (app-compare.py, app-anal.py, app-setup-questions.py).
"""

import os
import yaml
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()


def load_connect_owui(file_path):
    """Load the configuration file and return the active configuration.
    
    Environment variables take precedence over YAML configuration:
    - OPENWEBUI_API_KEY: API key for Open WebUI
    - OPENWEBUI_BASE_URL: Base URL for Open WebUI API
    
    Args:
        file_path (str): Path to the YAML configuration file
        
    Returns:
        dict: Configuration dictionary containing API credentials
    """
    try:
        with open(file_path, 'r', encoding="utf-8") as file:
            config_data = yaml.safe_load(file)
        
        # Check if the file contains the configs list structure
        if isinstance(config_data, dict) and 'configs' in config_data:
            configs = config_data.get('configs', [])
            
            # Look for active configuration
            for config in configs:
                if config.get('active', False):
                    print(f"Using active configuration: {config.get('name', 'Unnamed')}")
                    return config
            
            # If no active config is marked, return the first one
            if configs:
                print(f"Using default configuration: {configs[0].get('name', 'Unnamed')}")
                return configs[0]
            
            print("No configurations found in the config file")
            return {}
        else:
            # Handle old format for backward compatibility
            print("Using legacy config format")
            return config_data
            
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return {}


def get_api_credentials(config_file_path='./config/connect-owui.yaml', verbose=False):
    """Get API credentials from environment variables or configuration file.
    
    Environment variables take precedence over configuration file settings.
    This function centralizes the credential loading logic used across multiple scripts.
    
    Args:
        config_file_path (str): Path to the YAML configuration file (default: './config/connect-owui.yaml')
        verbose (bool): Whether to print verbose messages about credential source
        
    Returns:
        tuple: (API_KEY, BASE_URL) - API credentials as strings
    """
    # Check for environment variables first (takes precedence)
    API_KEY = os.getenv('OPENWEBUI_API_KEY')
    BASE_URL = os.getenv('OPENWEBUI_BASE_URL')
    
    if API_KEY and BASE_URL:
        if verbose:
            print("Using API credentials from environment variables")
        return API_KEY, BASE_URL
    
    # Fall back to configuration file
    config = load_connect_owui(config_file_path)
    
    # Extract API credentials from the selected configuration
    if 'open_webui' in config:
        API_KEY = config['open_webui'].get('api_key', '')
        BASE_URL = config['open_webui'].get('location', '')
        if verbose:
            print(f"Using API credentials from configuration file: {config.get('name', 'Unnamed')}")
    else:
        print("Warning: Invalid configuration format. Missing 'open_webui' section.")
        API_KEY = ''
        BASE_URL = ''
    
    return API_KEY, BASE_URL
