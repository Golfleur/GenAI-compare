from flask import Flask, render_template, request, redirect, url_for
import requests
import yaml
import os

app = Flask(__name__)

def load_connect_owui(file_path):
    with open(file_path, 'r', encoding="utf-8") as file:
        return yaml.safe_load(file)
config = load_connect_owui('./config/connect-owui.yaml')

# Configuration Paths
CONFIG_PATH = './config/config.yaml'
API_KEY = config['open_webui']['api_key']
BASE_URL = config['open_webui']['location']
API_URL = f"{BASE_URL}/api/models"

def fetch_models():
    """Fetch the list of models from the server using the API."""
    headers = {'Authorization': f'Bearer {API_KEY}'}
    response = requests.get(API_URL, headers=headers)
    if response.status_code == 200:
        try:
            response_data = response.json()
            models_data = response_data.get('data', [])
            return [model.get('name', model.get('id', 'Unnamed Model')) for model in models_data]
        except ValueError as e:
            print(f"Error parsing JSON: {e}")
            return []
    else:
        print(f"Failed to fetch models: {response.content}")
        return []

def load_analysis_config():
    """Load existing configuration from the YAML file."""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r', encoding="utf-8") as file:
            try:
                return yaml.safe_load(file) or {}
            except yaml.YAMLError:
                print("Error reading YAML configuration")
                return {}
    return {}

def save_analysis_model(selected_model):
    """Save the selected model for analysis to the YAML configuration file."""
    current_config = load_analysis_config()
    current_config['analysis_model'] = selected_model
    with open(CONFIG_PATH, 'w', encoding="utf-8") as file:
        yaml.dump(current_config, file)

@app.route('/', methods=['GET', 'POST'])
def index():
    models = fetch_models()
    if request.method == 'POST':
        selected_model = request.form.get('model')
        save_analysis_model(selected_model)
        return redirect(url_for('index'))
    
    current_config = load_analysis_config()
    selected_model = current_config.get('analysis_model', None)
    return render_template('select_comparator.html', models=models, selected_model=selected_model)

if __name__ == '__main__':
    app.run(debug=True)
