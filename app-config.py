from flask import Flask, render_template, request, redirect, url_for
import requests
import yaml
import os

app = Flask(__name__)


def load_connect_owui(file_path):
    with open(file_path, 'r', encoding="utf-8") as file:
        return yaml.safe_load(file)
    
config = load_connect_owui('./config/connect-owui.yaml')
API_KEY = config['open_webui']['api_key']
BASE_URL = config['open_webui']['location']
API_URL = f"{BASE_URL}/api/models"

CONFIG_PATH = './config/config.yaml'

def load_connect_owui(file_path):
    with open(file_path, 'r', encoding="utf-8") as file:
        return yaml.safe_load(file)

def fetch_models():
    """Fetch and enrich the list of models from the Open WebUI API."""
    headers = {'Authorization': f'Bearer {API_KEY}'}
    response = requests.get(API_URL, headers=headers)
    if response.status_code == 200:
        try:
            response_data = response.json()
            models_data = response_data.get('data', [])
            enriched_models = []
            for model in models_data:
                # Base model information
                enriched_model = {
                    'id': model.get('id', 'Unknown'),
                    'name': model.get('name', model.get('id', 'Unnamed Model')),
                    'owned_by': model.get('owned_by', 'Unknown'),
                    'created': model.get('created', 0),
                    'details': {}  # Initialize details dictionary
                }

                # Detailed description and capabilities
                if 'info' in model and 'meta' in model['info']:
                    meta = model['info']['meta']
                    enriched_model['description'] = meta.get('description', '')
                    enriched_model['profile_image'] = meta.get('profile_image_url', '')

                # Ollama-specific details
                if 'ollama' in model:
                    ollama_details = model['ollama'].get('details', {})
                    enriched_model['model_type'] = 'Ollama'
                    enriched_model['details'] = {
                        'format': ollama_details.get('format', 'Unknown'),
                        'family': ollama_details.get('family', 'Unknown'),
                        'parameter_size': ollama_details.get('parameter_size', 'Unknown'),
                        'quantization_level': ollama_details.get('quantization_level', 'Unknown')
                    }
                    enriched_model['size'] = model['ollama'].get('size', 0)
                    enriched_model['modified_at'] = model['ollama'].get('modified_at', '')

                # OpenAI-specific details
                elif 'openai' in model:
                    enriched_model['model_type'] = 'OpenAI'
                    openai_details = model['openai']
                    enriched_model['details'] = {
                        'family': 'GPT',
                        'parameter_size': 'Variable'
                    }
                    enriched_model['openai_details'] = {
                        'id': openai_details.get('id', ''),
                        'object': openai_details.get('object', ''),
                        'owned_by': openai_details.get('owned_by', '')
                    }

                # Google-specific details
                elif 'Google' in enriched_model['name']:
                    enriched_model['model_type'] = 'Google'
                    enriched_model['details'] = {
                        'family': 'Gemini/PaLM',
                        'parameter_size': 'Variable'
                    }

                # Anthropic-specific details
                elif 'anthropic' in enriched_model['name'].lower() or 'claude' in enriched_model['name'].lower():
                    enriched_model['model_type'] = 'Anthropic'
                    enriched_model['details'] = {
                        'family': 'Claude',
                        'parameter_size': 'Variable'
                    }

                enriched_models.append(enriched_model)
            return enriched_models
        except ValueError as e:
            print(f"Error parsing JSON: {e}")
            return []
    else:
        print(f"Failed to fetch models: {response.content}")
        return []

def load_selected_models():
    """Load selected models from the YAML configuration file."""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r', encoding="utf-8") as file:
            try:
                config = yaml.safe_load(file)
                return config.get("selected_models", [])
            except yaml.YAMLError:
                print("Error reading YAML configuration")
                return []
    return []

#def save_to_yaml(selected_models):
#    """Save the list of selected models to a YAML file."""
#    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
#    with open(CONFIG_PATH, 'w', encoding="utf-8") as file:
#        yaml.dump({"selected_models": selected_models}, file)

def save_to_yaml(selected_models):
    """Save the updated list of selected models to a YAML file, preserving existing configurations."""
    # Load the existing configuration
    current_config = {}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r', encoding="utf-8") as file:
            try:
                current_config = yaml.safe_load(file) or {}
            except yaml.YAMLError:
                print("Error reading YAML configuration")

    # Update the selected models
    current_config['selected_models'] = selected_models

    # Write the updated configuration back to the YAML file
    with open(CONFIG_PATH, 'w', encoding="utf-8") as file:
        yaml.dump(current_config, file)


@app.route('/', methods=['GET', 'POST'])
def index():
    """Main route for the application, handling both displaying models and saving user's selection."""
    models = fetch_models()
    
    # Organize models by provider
    providers = {
        'Google': [],
        'Anthropic': [],
        'OpenAI': [],
        'Ollama': []
    }
    
    for model in models:
        model_name = model['name'].lower()
        if 'google' in model_name or 'gemini' in model_name:
            providers['Google'].append(model)
        elif 'anthropic' in model_name or 'claude' in model_name:
            providers['Anthropic'].append(model)
        elif model.get('model_type') == 'OpenAI' or 'gpt' in model_name:
            providers['OpenAI'].append(model)
        elif model.get('model_type') == 'Ollama':
            providers['Ollama'].append(model)
    
    if request.method == 'POST':
        selected_models = request.form.getlist('models')
        save_to_yaml(selected_models)
        return redirect(url_for('index'))
    
    selected_models = load_selected_models()
    return render_template('index.html', providers=providers, selected_models=selected_models)

if __name__ == '__main__':
    app.run(debug=True)
