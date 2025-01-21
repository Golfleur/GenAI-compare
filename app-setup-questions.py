from flask import Flask, render_template, request, redirect, url_for
import json
import os

app = Flask(__name__)

# Ensure directories exist for storing files
os.makedirs('./questions', exist_ok=True)
os.makedirs('./targets', exist_ok=True)

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

@app.route('/', methods=['GET', 'POST'])
def index():
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

        return redirect(url_for('index'))
    
    return render_template('index_q.html')

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

if __name__ == '__main__':
    app.run(debug=True)
