from flask import Flask, render_template, request, redirect, url_for
import json
import os

app = Flask(__name__)

# Ensure the directories for storing files exist
os.makedirs('./questions', exist_ok=True)
os.makedirs('./answers', exist_ok=True)

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