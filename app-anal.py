import os
import json
import argparse
import requests
import yaml

def load_connect_owui(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

config = load_connect_owui('./config/connect-owui.yaml')
API_KEY = config['open_webui']['api_key']
BASE_URL = config['open_webui']['location']
API_URL = f"{BASE_URL}/api/chat/completions"

questions_dir = './questions'
answers_dir = './answers'
targets_dir = './targets'
analysis_dir = './analysis'

def read_file_content(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read().strip()

def read_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def get_analysis_response(question, candidate_answer, target_answer, infos_cruciales, infos_a_eviter):
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    prompt = (
        f"Question: {question}\n"
        f"Réponse du modèle: {candidate_answer}\n\n"
        f"Attentes:\n Réponse attendue: {target_answer}\n"
        f"Informations cruciales attendues: {infos_cruciales}\n"
        f"Informations à éviter: {infos_a_eviter}\n"
        f"Veuillez évaluer si la réponse du modèle inclut les informations cruciales attendues et omet le contenu à éviter, tout en évaluant la similarité globale."
    )
    data = {
        'model': 'gpt-4o',
        'messages': [
            {'role': 'system', 'content': "Tu fournis une évaluation en français de la qualité de la réponse par rapport à la cible."},
            {'role': 'user', 'content': prompt}
        ]
    }
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        print(f"Error with API request: {e}")
        return "Error in API request"

def main(verbose=False):
    os.makedirs(analysis_dir, exist_ok=True)

    for question_file in os.listdir(questions_dir):
        if question_file.endswith('.q'):
            base_name = question_file[:-2]
            question_path = os.path.join(questions_dir, question_file)
            answer_path = os.path.join(answers_dir, question_file.replace('.q', '.a'))
            target_path = os.path.join(targets_dir, question_file.replace('.q', '.t'))

            question = read_file_content(question_path)
            target_data = read_json_file(target_path)
            target_answer = target_data['reponse_cible']
            infos_cruciales = target_data.get('infos_cruciales', '')
            infos_a_eviter = target_data.get('infos_a_eviter', '')

            # Prepare the report for each question analyzed
            report = f"Analyse pour {base_name}\n"
            report += f"Question: {question}\n"
            report += f"Réponse attendue: {target_answer}\n"
            report += f"Informations cruciales attendues: {infos_cruciales}\n"
            report += f"Informations à éviter: { infos_a_eviter}\n\n"

            # Load answers from the JSON structure
            answers_data = read_json_file(answer_path)

            for model, model_data in answers_data.items():
                answer_text = model_data['choices'][0]['message']['content']

                # Use GPT-4o to analyze the answer
                api_response = get_analysis_response(
                    question, answer_text, target_answer, infos_cruciales, infos_a_eviter
                )

                # Constructing report for the model's performance
                report += f"\nModèle: {model}\n"
                report += f"Réponse du modèle: {answer_text}\n"
                report += f"Analyse de la réponse: {api_response}\n"

                if verbose:
                    print(f"Processed model {model} for question {base_name}")

            # Save the report
            analysis_filename = os.path.join(analysis_dir, question_file.replace('.q', '.txt'))
            with open(analysis_filename, 'w', encoding='utf-8') as f:
                f.write(report)

            if verbose:
                print(f"Completed analysis for {base_name}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run model answer analysis.")
    parser.add_argument('--verbose', action='store_true', help="Enable verbose mode")
    args = parser.parse_args()

    main(verbose=args.verbose)
