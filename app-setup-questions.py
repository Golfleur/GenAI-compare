from flask import Flask, render_template, request, redirect, url_for
import json
import os
import yaml

app = Flask(__name__)

# Ensure directories exist for storing files
os.makedirs('./questions', exist_ok=True)
os.makedirs('./targets', exist_ok=True)
os.makedirs('./answers', exist_ok=True)
os.makedirs('./config', exist_ok=True)  # Ensure the config directory exists

def save_question(nom_question, question_content):
    """Save the question content to a .q file."""
    question_path = f'./questions/{nom_question}.q'
    with open(question_path, 'w', encoding="utf-8") as file:
        file.write(question_content)

def save_target(nom_question, target_data):
    """Save the target information to a .t file in JSON format."""
    target_path = f'./targets/{nom_question}.t'
    with open(target_path, 'w', encoding="utf-8") as file:
        json.dump(target_data, file, indent=4)

def load_question(nom_question):
    """Load the question content from a .q file."""
    question_path = f'./questions/{nom_question}.q'
    if os.path.exists(question_path):
        with open(question_path, 'r', encoding="utf-8") as file:
            return file.read()
    return None

def load_target(nom_question):
    """Load the target information from a .t file."""
    target_path = f'./targets/{nom_question}.t'
    if os.path.exists(target_path):
        with open(target_path, 'r', encoding="utf-8") as file:
            return json.load(file)
    return None

def save_selected_questions(selected_questions):
    """Save the selected question names to a YAML file."""
    config_path = './config/selected_questions.yaml'
    with open(config_path, 'w', encoding='utf-8') as file:
        yaml.dump(selected_questions, file)

def load_selected_questions():
    """Load the list of selected questions from the YAML file."""
    config_yaml_path = './config/selected_questions.yaml'
    try:
        with open(config_yaml_path, 'r', encoding='utf-8') as stream:
            return yaml.safe_load(stream) or []
    except (FileNotFoundError, yaml.YAMLError):
        return []

def list_questions():
    """Return a list of all question names without file extensions."""
    return [f[:-2] for f in os.listdir('./questions') if f.endswith('.q')]

def save_manual_answer(question_name, answer_content, source):
    """Save the manual answer in a .a file such that the source is used as identifier."""
    answer_path = f'./answers/{question_name}.a'
    manual_entry = {source: {'choices': [{'message': {'content': answer_content}}]}}
    # Load existing answers if any
    existing_answers = {}
    if os.path.exists(answer_path):
        with open(answer_path, 'r', encoding='utf-8') as file:
            existing_answers = json.load(file)
    # Add or update the manual answer
    existing_answers.update(manual_entry)
    with open(answer_path, 'w', encoding='utf-8') as file:
        json.dump(existing_answers, file, indent=2)

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index_q.html')

@app.route('/add_q', methods=['GET', 'POST'])
def add_q():
    if request.method == 'POST':
        # Retrieve form data
        nom_question = request.form.get('nom_question')
        question_content = request.form.get('question_content')
        reponse_cible = request.form.get('reponse_cible')
        infos_cruciales = request.form.get('infos_cruciales')
        infos_a_eviter = request.form.get('infos_a_eviter')
        # Validate nom_question for a single word identifier
        if not nom_question or ' ' in nom_question:
            return "Nom de la question doit être un seul mot", 400
        # Save question content
        save_question(nom_question, question_content)
        # Prepare and save target data in JSON
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
    """Display all questions and their target answers."""
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
    return render_template('questions.html', questions=questions)

@app.route('/edit/<nom_question>', methods=['GET', 'POST'])
def edit(nom_question):
    """Edit a selected question and target data."""
    if request.method == 'POST':
        # Update question and target
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
        return redirect(url_for('questions'))
    question_content = load_question(nom_question)
    target_data = load_target(nom_question)
    return render_template('edit.html', nom_question=nom_question, question_content=question_content, target_data=target_data)

@app.route('/select_questions', methods=['GET', 'POST'])
def select_questions():
    """Select a subset of questions and save to a YAML file."""
    if request.method == 'POST':
        selected_questions = request.form.getlist('selected_questions')
        save_selected_questions(selected_questions)
        return redirect(url_for('select_questions'))
    # Get the list of all questions
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
        # Save the manual answer
        save_manual_answer(question_name, answer_content, source)
        return redirect(url_for('manual_entry'))
    
    questions = list_questions()
    questions.sort(key=lambda x: x.lower())
    return render_template('manual_entry.html', questions=questions)

if __name__ == '__main__':
    app.run(debug=True)