import requests
import yaml
import json
import os
import argparse

MODELS_SUPPORTING_CITATIONS = ["perplexity", "claude"]

def load_connect_owui(file_path):
    """Load the configuration file and return the active configuration"""
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

# Constants
CONFIG_PATH = './config/config.yaml'
QUESTIONS_FOLDER = './questions'
ANSWERS_FOLDER = './answers'
n_questions = 0
n_models = 0

def load_models(config_path, verbose):
    """Load model names from a YAML configuration file."""
    try:
        with open(config_path, 'r', encoding="utf-8") as file:
            config = yaml.safe_load(file)
        models = config.get('selected_models', [])
        n_models = len(models)
        if verbose:
            print(f"Loaded {n_models} models: {models}")
        return models
    except Exception as e:
        print(f"Error loading models from config: {e}")
        return []

def read_question(file_name, verbose, q, n_questions):
    """Read the question from the specified file."""
    try:
        with open(file_name, 'r', encoding="utf-8") as file:
            question = file.read().strip()
        if verbose:
            print("*-*-*-*-*-*-*-*-*")
            print(f"Question {q}/{n_questions} read from '{file_name}'")
            #print(f"{question}")
        return question
    except FileNotFoundError:
        print(f"Error: The file {file_name} was not found.")
        return None

def format_token(token):
    """Ensure token is in the correct format."""
    if not token.startswith('sk-'):
        token = f'sk-{token}'
    return token

def generate_answer(question, model_name, verbose, api_key, base_url):
    """Generate an answer using a model hosted on Open WebUI."""
    if not question:
        print("No question to process.")
        return None
        
    # Check if API credentials are available
    if not api_key or not base_url:
        print("Error: API key or base URL is missing in the configuration.")
        return None
        
    # Format token and prepare request
    token = format_token(api_key)
    url = f"{base_url}/api/chat/completions"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    if any(name in model_name.lower() for name in MODELS_SUPPORTING_CITATIONS):
        payload = {
            'model': model_name,
            'messages': [{'role': 'user', 'content': question}],
            'stream': False,
            'return_citations': True,
        }
    else:
        payload = {
            'model': model_name,
            'messages': [{'role': 'user', 'content': question}],
            'stream': False,
        }
        
    if verbose:
        print("*-*-*-*-*-*-*-*-*")
        print(f"Making request to: {url}")
        print(f"Using model: {model_name}")
        # print(f"Headers: {headers}")
        # print(f"Payload: {json.dumps(payload, indent=2)}")
        
    try:
        response = requests.post(url, headers=headers, json=payload)
        if verbose:
            print("*-*-*-*-*-*-*-*-*")
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
        response.raise_for_status()
        response_data = response.json()
        
        # if verbose:
            # print("*-*-*-*-*-*-*-*-*")
            # print(f"Response data: {json.dumps(response_data, indent=2)}\n")
            
        return response_data
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occurred: {e.response.text}")
        if verbose:
            print(f"Full error details: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        if verbose:
            print(f"Full error details: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
        if verbose:
            print(f"Full error details: {e}")
            
    return None

def write_answers(file_name, answers, verbose):
    """Write the collected answers to a specified file as JSON."""
    try:
        with open(file_name, 'w', encoding="utf-8") as file:
            json.dump(answers, file, indent=2)
        if verbose:
            print("*-*-*-*-*-*-*-*-*")
            print(f"Answers written to '{file_name}'")
    except Exception as e:
        print(f"Error writing answers to file '{file_name}': {e}")

def process_question_files(verbose, api_key, base_url):
    """Process all question files with all models."""
    os.makedirs(ANSWERS_FOLDER, exist_ok=True)
    
    # Load the list of selected questions from the YAML file
    config_yaml_path = './config/selected_questions.yaml'
    try:
        with open(config_yaml_path, 'r', encoding='utf-8') as stream:
            selected_questions = yaml.safe_load(stream) or []
            n_questions = len(selected_questions)
            if verbose:
                print("*-*-*-*-*-*-*-*-*")
                print(f"There are {n_questions} questions loaded : {selected_questions}")
    except (FileNotFoundError, yaml.YAMLError) as e:
        if verbose:
            print(f"YAML file not found or error reading YAML file: {e}. Defaulting to all questions.")
        selected_questions = None
        
    # Load models
    models = load_models(CONFIG_PATH, verbose)
    n_models = len(models)
    if not models:
        print("No models found in configuration.")
        return
        
    if verbose:
        print("*-*-*-*-*-*-*-*-*")
        print(f"Looking for questions in: {QUESTIONS_FOLDER}")
        print(f"Will save answers in: {ANSWERS_FOLDER}")
        
    # Process each model
    n = 0
    for model_name in models:
        n = n + 1
        if verbose:
            print("*-*-*-*-*-*-*-*-*")
            print(f"Processing all {n_questions} questions for model {n}/{n_models}:'{model_name}'")
            
        # Process each question file
        q = 0
        for q_file in os.listdir(QUESTIONS_FOLDER):
            if q_file.endswith('.q'):
                q_name = os.path.splitext(q_file)[0]
                
                # Check if this question is listed in the YAML file, if it exists
                if selected_questions is not None and q_name not in selected_questions:
                    if verbose:
                        print(f"Skipping question '{q_name}' as it is not listed in selected questions")
                    continue
                    
                q = q + 1
                if verbose:
                    print("*-*-*-*-*-*-*-*-*")
                    print(f"Processing question {q}/{n_questions}: {q_file}")
                    
                q_path = os.path.join(QUESTIONS_FOLDER, q_file)
                question = read_question(q_path, verbose, q, n_questions)
                
                if question:
                    output_file = os.path.join(ANSWERS_FOLDER, f"{os.path.splitext(q_file)[0]}.a")
                    
                    # Load existing answers if any
                    existing_answers = {}
                    if os.path.exists(output_file):
                        try:
                            with open(output_file, 'r', encoding="utf-8") as file:
                                existing_answers = json.load(file)
                            if verbose:
                                print("*-*-*-*-*-*-*-*-*")
                                print(f"Loaded existing answers from other models for question {q}/{n_questions} from {output_file}")
                        except Exception as e:
                            print(f"Error loading existing answers from '{output_file}': {e}")
                            
                    # Generate and save new answer
                    answer = generate_answer(question, model_name, verbose, api_key, base_url)
                    if answer is not None:
                        existing_answers[model_name] = answer
                        if verbose:
                            print("*-*-*-*-*-*-*-*-*")
                            print(f"Saving answers for question {q}/{n_questions}-'{q_file}' with model {n}/{n_models}-'{model_name}'")
                        write_answers(output_file, existing_answers, verbose)
                    else:
                        print(f"No answer generated for question {q}-'{q_file}' with model {n} '{model_name}'.")

def main():
    parser = argparse.ArgumentParser(description="Process question files and generate complete responses.")
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    args = parser.parse_args()
    
    # Load the configuration
    config = load_connect_owui('./config/connect-owui.yaml')
    
    # Extract API credentials from the selected configuration
    if 'open_webui' in config:
        API_KEY = config['open_webui'].get('api_key', '')
        BASE_URL = config['open_webui'].get('location', '')
    else:
        print("Warning: Invalid configuration format. Missing 'open_webui' section.")
        API_KEY = ''
        BASE_URL = ''
    
    
    # Process all questions
    process_question_files(args.verbose, API_KEY, BASE_URL)

if __name__ == "__main__":
    main()