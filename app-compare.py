import requests
import yaml
import json
import os
import argparse


def load_connect_owui(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

config = load_connect_owui('./config/connect-owui.yaml')
API_KEY = config['open_webui']['api_key']
BASE_URL = config['open_webui']['location']

# Constants
CONFIG_PATH = './config/config.yaml'
QUESTIONS_FOLDER = './questions'
ANSWERS_FOLDER = './answers'

def load_models(config_path, verbose):
    """Load model names from a YAML configuration file."""
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        models = config.get('selected_models', [])
        if verbose:
            print(f"Loaded models: {models}")
        return models
    except Exception as e:
        print(f"Error loading models from config: {e}")
        return []

def read_question(file_name, verbose):
    """Read the question from the specified file."""
    try:
        with open(file_name, 'r') as file:
            question = file.read().strip()
        if verbose:
            print(f"Question read from '{file_name}': {question}")
        return question
    except FileNotFoundError:
        print(f"Error: The file {file_name} was not found.")
        return None

def format_token(token):
    """Ensure token is in the correct format."""
    if not token.startswith('sk-'):
        token = f'sk-{token}'
    return token

def generate_answer(question, model_name, verbose):
    """Generate an answer using a model hosted on Open WebUI."""
    if not question:
        print("No question to process.")
        return None

    # Format token and prepare request
    token = format_token(API_KEY)
    url = f"{BASE_URL}/api/chat/completions"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    payload = {
        'model': model_name,
        'messages': [{'role': 'user', 'content': question}]
    }

    if verbose:
        print(f"\nMaking request to: {url}")
        print(f"Using model: {model_name}")
        print(f"Headers: {headers}")
        print(f"Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if verbose:
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")

        response.raise_for_status()
        response_data = response.json()
        
        if verbose:
            print(f"Response data: {json.dumps(response_data, indent=2)}\n")
        
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
        with open(file_name, 'w') as file:
            json.dump(answers, file, indent=2)
        if verbose:
            print(f"Answers written to '{file_name}'")
    except Exception as e:
        print(f"Error writing answers to file '{file_name}': {e}")

def process_question_files(verbose):
    """Process all question files with all models."""
    os.makedirs(ANSWERS_FOLDER, exist_ok=True)
    
    # Load models
    models = load_models(CONFIG_PATH, verbose)
    if not models:
        print("No models found in configuration.")
        return

    if verbose:
        print(f"\nStarting processing")
        print(f"Looking for questions in: {QUESTIONS_FOLDER}")
        print(f"Will save answers in: {ANSWERS_FOLDER}")

    # Process each model
    for model_name in models:
        if verbose:
            print(f"\nProcessing all questions for model '{model_name}'")

        # Process each question file
        for q_file in os.listdir(QUESTIONS_FOLDER):
            if q_file.endswith('.q'):
                if verbose:
                    print(f"\nProcessing question file: {q_file}")

                q_path = os.path.join(QUESTIONS_FOLDER, q_file)
                question = read_question(q_path, verbose)

                if question:
                    output_file = os.path.join(ANSWERS_FOLDER, f"{os.path.splitext(q_file)[0]}.a")
                    
                    # Load existing answers if any
                    existing_answers = {}
                    if os.path.exists(output_file):
                        try:
                            with open(output_file, 'r') as file:
                                existing_answers = json.load(file)
                            if verbose:
                                print(f"Loaded existing answers from {output_file}")
                        except Exception as e:
                            print(f"Error loading existing answers from '{output_file}': {e}")

                    # Generate and save new answer
                    answer = generate_answer(question, model_name, verbose)
                    if answer is not None:
                        existing_answers[model_name] = answer
                        if verbose:
                            print(f"Saving answers for question '{q_file}' with model '{model_name}'")
                        write_answers(output_file, existing_answers, verbose)
                    else:
                        print(f"No answer generated for question '{q_file}' with model '{model_name}'.")

def main():
    parser = argparse.ArgumentParser(description="Process question files and generate complete responses.")
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    #parser.add_argument('--token', required=True, help='API token for authentication')
    
    args = parser.parse_args()
    
    # Process all questions
    #process_question_files(args.token, args.verbose)
    process_question_files(args.verbose)

if __name__ == "__main__":
    main()
