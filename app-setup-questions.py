from flask import Flask, render_template, request, redirect, url_for
import json
import os
import yaml
import requests
import subprocess

app = Flask(__name__)

# Ensure directories exist for storing files
os.makedirs('./questions', exist_ok=True)
os.makedirs('./targets', exist_ok=True)
os.makedirs('./answers', exist_ok=True)
os.makedirs('./config', exist_ok=True)

def load_connect_owui(file_path):
    with open(file_path, 'r', encoding="utf-8") as file:
        return yaml.safe_load(file)

# Configuration paths and settings
CONFIG_PATH = './config/config.yaml'
config_file = './config/connect-owui.yaml'
config = load_connect_owui(config_file)
API_KEY = config['open_webui']['api_key']
BASE_URL = config['open_webui']['location']
API_URL = f"{BASE_URL}/api/models"

def save_connect_owui(config, file_path):
    with open(file_path, 'w') as file:
        yaml.dump(config, file)


# Question management functions
def save_question(nom_question, question_content):
    question_path = f'./questions/{nom_question}.q'
    with open(question_path, 'w', encoding="utf-8") as file:
        file.write(question_content)

def save_target(nom_question, target_data):
    target_path = f'./targets/{nom_question}.t'
    with open(target_path, 'w', encoding="utf-8") as file:
        json.dump(target_data, file, indent=4)

def load_question(nom_question):
    question_path = f'./questions/{nom_question}.q'
    if os.path.exists(question_path):
        with open(question_path, 'r', encoding="utf-8") as file:
            return file.read()
    return None

def load_target(nom_question):
    target_path = f'./targets/{nom_question}.t'
    if os.path.exists(target_path):
        with open(target_path, 'r', encoding="utf-8") as file:
            return json.load(file)
    return None

def save_selected_questions(selected_questions):
    config_path = './config/selected_questions.yaml'
    with open(config_path, 'w', encoding='utf-8') as file:
        yaml.dump(selected_questions, file)

def load_selected_questions():
    config_yaml_path = './config/selected_questions.yaml'
    try:
        with open(config_yaml_path, 'r', encoding='utf-8') as stream:
            return yaml.safe_load(stream) or []
    except (FileNotFoundError, yaml.YAMLError):
        return []

def list_questions():
    return [f[:-2] for f in os.listdir('./questions') if f.endswith('.q')]

def save_manual_answer(question_name, answer_content, source):
    answer_path = f'./answers/{question_name}.a'
    manual_entry = {source: {'choices': [{'message': {'content': answer_content}}]}}
    existing_answers = {}
    if os.path.exists(answer_path):
        with open(answer_path, 'r', encoding='utf-8') as file:
            existing_answers = json.load(file)
    existing_answers.update(manual_entry)
    with open(answer_path, 'w', encoding='utf-8') as file:
        json.dump(existing_answers, file, indent=2)

# Model management functions
def fetch_models():
    config = load_connect_owui(config_file)
    API_KEY = config['open_webui']['api_key']
    BASE_URL = config['open_webui']['location']
    API_URL = f"{BASE_URL}/api/models"

    if test_connection(True):
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
                    # Perplexity-specific details
                    elif 'perplexity' in enriched_model['name']:
                        enriched_model['model_type'] = 'Perplexity'
                        enriched_model['details'] = {
                            'family': 'online',
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
                return ["{e}"]
        else:
            print(f"Failed to fetch models: {response.content}")
            return ["{response.content}"]
    else:
        print(f"Failed to fetch models: connection to API failed")
        return []

def load_analysis_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r', encoding="utf-8") as file:
            try:
                return yaml.safe_load(file) or {}
            except yaml.YAMLError:
                print("Error reading YAML configuration")
                return {}
    return {}

def save_analysis_model(selected_model):
    current_config = load_analysis_config()
    current_config['analysis_model'] = selected_model
    with open(CONFIG_PATH, 'w', encoding="utf-8") as file:
        yaml.dump(current_config, file)

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

# Routes
@app.route('/')
def index():
    config = load_connect_owui(config_file)
    return render_template('index_q.html')

@app.route('/select_comparator', methods=['GET', 'POST'])
def select_comparator():
    models = fetch_models()
    if request.method == 'POST':
        selected_model = request.form.get('model')
        save_analysis_model(selected_model)
        return redirect(url_for('select_comparator'))
    current_config = load_analysis_config()
    selected_model = current_config.get('analysis_model', None)
    return render_template('select_comparator.html', models=models, selected_model=selected_model)

@app.route('/add_q', methods=['GET', 'POST'])
def add_q():
    if request.method == 'POST':
        nom_question = request.form.get('nom_question')
        question_content = request.form.get('question_content')
        reponse_cible = request.form.get('reponse_cible')
        infos_cruciales = request.form.get('infos_cruciales')
        infos_a_eviter = request.form.get('infos_a_eviter')
        if not nom_question or ' ' in nom_question:
            return "Nom de la question doit être un seul mot", 400
        save_question(nom_question, question_content)
        target_data = {
            "reponse_cible": reponse_cible,
            "infos_cruciales": infos_cruciales,
            "infos_a_eviter": infos_a_eviter
        }
        save_target(nom_question, target_data)
        return redirect(url_for('add_q'))
    return render_template('add_q.html')

@app.route('/questions')
def questions():
    question_files = os.listdir('./questions')
    questions = []
    for filename in question_files:
        nom_question = filename.split('.')[0]
        question_content = load_question(nom_question)
        target_data = load_target(nom_question)
        first_paragraph = question_content.split('\n')[0] if question_content else ''
        questions.append({
            'nom_question': nom_question,
            'question_content': question_content,
            'target_data': target_data,
            'first_paragraph': first_paragraph
        })
    questions.sort(key=lambda x: x['nom_question'].lower())
    return render_template('questions.html', questions=questions)

@app.route('/delquestion')
def delquestion():
    question_files = os.listdir('./questions')
    questions = []
    for filename in question_files:
        nom_question = filename.split('.')[0]
        question_content = load_question(nom_question)
        target_data = load_target(nom_question)
        first_paragraph = question_content.split('\n')[0] if question_content else ''
        questions.append({
            'nom_question': nom_question,
            'question_content': question_content,
            'target_data': target_data,
            'first_paragraph': first_paragraph
        })
    questions.sort(key=lambda x: x['nom_question'].lower())
    return render_template('delquestion.html', questions=questions)

@app.route('/edit', methods=['GET'])
def edit():
    question_files = os.listdir('./questions')
    questions = []
    for filename in question_files:
        nom_question = filename.split('.')[0]
        question_content = load_question(nom_question)
        target_data = load_target(nom_question)
        questions.append({
            'nom_question': nom_question,
            'question_content': question_content,
            'target_data': target_data
        })
    questions.sort(key=lambda x: x['nom_question'].lower())
    return render_template('edit.html', questions=questions)

@app.route('/edit/<nom_question>', methods=['GET', 'POST'])
def edit_question(nom_question):
    if request.method == 'POST':
        question_content = request.form.get('question_content')
        reponse_cible = request.form.get('reponse_cible')
        infos_cruciales = request.form.get('infos_cruciales')
        infos_a_eviter = request.form.get('infos_a_eviter')
        save_question(nom_question, question_content)
        target_data = {
            "reponse_cible": reponse_cible,
            "infos_cruciales": infos_cruciales,
            "infos_a_eviter": infos_a_eviter
        }
        save_target(nom_question, target_data)
        return redirect(url_for('edit'))
    question_content = load_question(nom_question)
    target_data = load_target(nom_question)
    return render_template('edit_question.html', nom_question=nom_question, question_content=question_content, target_data=target_data)

@app.route('/select_questions', methods=['GET', 'POST'])
def select_questions():
    if request.method == 'POST':
        selected_questions = request.form.getlist('selected_questions')
        save_selected_questions(selected_questions)
        return redirect(url_for('select_questions'))
    question_files = os.listdir('./questions')
    questions = [filename.split('.')[0] for filename in question_files]
    questions.sort(key=lambda x: x.lower())
    selected_questions = load_selected_questions()
    return render_template('select_questions.html', questions=questions, selected_questions=selected_questions)

@app.route('/manual_entry', methods=['GET', 'POST'])
def manual_entry():
    if request.method == 'POST':
        question_name = request.form.get('question_name')
        answer_content = request.form.get('answer_content')
        source = request.form.get('source')
        save_manual_answer(question_name, answer_content, source)
        return redirect(url_for('manual_entry'))
    questions = list_questions()
    questions.sort(key=lambda x: x.lower())
    return render_template('manual_entry.html', questions=questions)

@app.route('/models', methods=['GET', 'POST'])
def models():
    """Main route for the application, handling both displaying models and saving user's selection."""
    models = fetch_models()
    # Organize models by provider
    providers = {
        'Google': [],
        'Anthropic': [],
        'OpenAI': [],
        'Perplexity': [],
        'Ollama': [],
        'Other':[]
    }
    for model in models:
        model_name = model['name'].lower()
        if 'google' in model_name or 'gemini' in model_name:
            providers['Google'].append(model)
        elif 'anthropic' in model_name or 'claude' in model_name:
            providers['Anthropic'].append(model)
        elif 'perplexity' in model_name or 'sonar' in model_name:
            providers['Perplexity'].append(model)
        elif model.get('model_type') == 'OpenAI' or 'gpt' in model_name:
            providers['OpenAI'].append(model)
        elif model.get('model_type') == 'Ollama':
            providers['Ollama'].append(model)
        else:
            providers['Other'].append(model)
    if request.method == 'POST':
        selected_models = request.form.getlist('models')
        save_to_yaml(selected_models)
        return redirect(url_for('models'))
    selected_models = load_selected_models()
    return render_template('index.html', models=models, providers=providers, selected_models=selected_models)


@app.route('/run_compare')
def run_compare():
    try:
        result = subprocess.run(["python", "app-compare.py", "--verbose"], capture_output=True, text=True, check=True)
        output = result.stdout
        return render_template('output.html', output=output, script_name="app-compare.py")
    except subprocess.CalledProcessError as e:
        return f"Error executing app-compare.py: {e}", 500

@app.route('/run_anal')
def run_anal():
    try:
        result = subprocess.run(["python", "app-anal.py", "--verbose"], capture_output=True, text=True, check=True)
        output = result.stdout
        return render_template('output.html', output=output, script_name="app-anal.py")
    except subprocess.CalledProcessError as e:
        return f"Error executing app-anal.py: {e}", 500

@app.route('/delete_questions', methods=['POST'])
def delete_questions():
    selected_questions = request.form.getlist('selected_questions')
    for nom_question in selected_questions:
        question_path = f'./questions/{nom_question}.q'
        answer_path = f'./answers/{nom_question}.a'
        target_path = f'./targets/{nom_question}.t'
        if os.path.exists(question_path):
            os.remove(question_path)
        if os.path.exists(answer_path):
            os.remove(answer_path)
        if os.path.exists(target_path):
            os.remove(target_path)
    return redirect(url_for('delquestion'))

@app.route('/test_connection', methods=['POST'])
def test_connection(local = False):
    config = load_connect_owui(config_file)
    API_KEY = config['open_webui']['api_key']
    BASE_URL = config['open_webui']['location']

    if not API_KEY or not BASE_URL:
        return {'status': 'error', 'message': 'API key and location are required.'}, 400

    try:
        response = requests.get(f"{BASE_URL}/api/models", headers={'Authorization': f'Bearer {API_KEY}'})
        if response.status_code == 200:
            if not local:
                return {'status': 'success', 'message': 'Connexion réussie!'}
            else:
                return True
        else:
            if not local:
                return {'status': 'error', 'message': f"Failed to connect: {response.status_code} - {response.text}"}, response.status_code
            else:
                return False
    except requests.RequestException as e:
        if not local:
            return {'status': 'error', 'message': str(e)}, 500
        else:
            return False

@app.route('/edit_config', methods=['GET', 'POST'])
def edit_config():
    config = load_connect_owui(config_file)
    message = None
    category = None

    if request.method == 'POST':
        new_config = {
            'open_webui': {
                'api_key': request.form.get('api_key'),
                'location': request.form.get('location')
            }
        }
        save_connect_owui(new_config, config_file)
        config = load_connect_owui(config_file)
        message = 'Configuration sauvegardée avec succès!'
        category = 'success'

    return render_template('edit_config.html', config=config, message=message, category=category)

if __name__ == '__main__':
    app.run(debug=True)
