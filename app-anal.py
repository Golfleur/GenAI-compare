import os
import json
import argparse
import requests
import yaml
import re
import datetime

THINK_MARKER_TO_BE_IGNORED = True
DO_NOT_ADD_A_SYSTEM_PROMPT = True
ADD_CITATIONS_TO_ANSWER = False

def load_connect_owui(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

CONFIG_PATH = './config/config.yaml'
config = load_connect_owui('./config/connect-owui.yaml')
API_KEY = config['open_webui']['api_key']
BASE_URL = config['open_webui']['location']
API_URL = f"{BASE_URL}/api/chat/completions"
config_yaml_path = './config/selected_questions.yaml'

questions_dir = './questions'
answers_dir = './answers'
targets_dir = './targets'
analysis_dir = './analysis'

n_questions = 0
n_models = 0

def load_config():
    """Load existing configuration from the YAML file."""
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file) or {}
    except yaml.YAMLError:
        print("Error reading YAML configuration")
    return {}

def load_analysis_model():
    """Load the selected model for analysis from the configuration."""
    config = load_config()
    return config.get('analysis_model', 'GPT-4o')  # default to GPT-4o

def read_file_content(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read().strip()

def read_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def get_analysis_response(question, candidate_answer, target_answer, infos_cruciales, infos_a_eviter, analysis_model, verbose):
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    prompt = (
        f"--------------------------------------------------------\n"
        f"Question qui a été posée au modèle d'IA:\n {question}\n"
        f"--------------------------------------------------------\n"
        f"Réponse obtenue du modèle:\n {candidate_answer}\n"
        f"--------------------------------------------------------\n"
        f"Nos experts juridiques ont déterminé que la bonne réponse est:\n {target_answer}\n"
        f"--------------------------------------------------------\n"
        f"Informations cruciales attendues:\n {infos_cruciales}\n"
        f"--------------------------------------------------------\n"
        f"Informations à éviter:\n {infos_a_eviter}."
        f"--------------------------------------------------------\n"
    )

    if DO_NOT_ADD_A_SYSTEM_PROMPT:
        data = {
            'model': analysis_model,
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'stream':False,
        }
    else:
        data = {
            'model': analysis_model,
            'messages': [
                {'role': 'system', 'content': "Tu fournis une évaluation en français de la qualité de la réponse par rapport à la cible."},
                {'role': 'user', 'content': prompt}
            ],
            'stream':False,
        }

    if verbose:
        print("*-*-*-*-*-*-*-*-*")
        print(f"Making request to: {API_URL}")
        print(f"Using model: {analysis_model}")
        # print(f"Headers: {headers}")
        print(f"Response data: {json.dumps(data, indent=2)}")
        
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        if verbose:
            print("*-*-*-*-*-*-*-*-*")
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        print(f"Error with API request: {e}")
        return "Error in API request"

def main(verbose=False):
    os.makedirs(analysis_dir, exist_ok=True)
    analysis_model = load_analysis_model()
    if verbose:
        print("*-*-*-*-*-*-*-*-*")
        print(f"Analysis to be performed by {analysis_model}")
        
    try:
        with open(config_yaml_path, 'r', encoding='utf-8') as stream:
            selected_questions = yaml.safe_load(stream) or []
            n_questions = len(selected_questions)
            if verbose:
                print("*-*-*-*-*-*-*-*-*")
                print(f"Loaded {n_questions} questions: {selected_questions}")
                
    except (FileNotFoundError, yaml.YAMLError) as e:
        if verbose:
            print(f"YAML file not found or error reading YAML file: {e}. Defaulting to all answered questions.")
        selected_questions = None
    q=0
    for question_file in os.listdir(questions_dir):
        if question_file.endswith('.q'):
            base_name = question_file[:-2]
            question_path = os.path.join(questions_dir, question_file)
            answer_path = os.path.join(answers_dir, question_file.replace('.q', '.a'))

            if selected_questions is not None and base_name not in selected_questions:
                    if verbose:
                        print(f"Skipping question '{base_name}' as it is not listed in selected questions")
                    continue
            
            if not os.path.exists(answer_path):
                if verbose:
                    print(f"Skipping {base_name} because the answer file {answer_path} does not exist.")
                continue
            
            q=q+1
            target_path = os.path.join(targets_dir, question_file.replace('.q', '.t'))

            question = read_file_content(question_path)
            target_data = read_json_file(target_path)
            target_answer = target_data['reponse_cible']
            infos_cruciales = target_data.get('infos_cruciales', '')
            infos_a_eviter = target_data.get('infos_a_eviter', '')

            #report = "(c) 2025 Lavery De Billy S.E.N.C.R.L.\n"
            report = ""
            report += f"*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*\n"
            report += f"Analyse pour {base_name}\n"
            report += f"Question:\n"
            report += f"-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_\n"
            report += f"\n{question}\n"
            report += f"-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯\n"
            report += f"Réponse attendue pour {base_name}\n"
            report += f"-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_\n"
            report += f"{target_answer}\n"
            report += f"-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯\n"
            report += f"Informations cruciales attendues pour {base_name}:\n"
            report += f"-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_\n"
            report += f"{infos_cruciales}\n"
            report += f"-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯\n"
            report += f"Informations à éviter pour {base_name}:\n"
            report += f"-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_\n"
            report += f"{infos_a_eviter}\n"
            report += f"-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯\n"
            report += f"--------------------------------------------------------\n"

            answers_data = read_json_file(answer_path)
            n=0
            n_models = len(answers_data)
            for model, model_data in answers_data.items():
                n=n+1
                
                if verbose:
                    print("*-*-*-*-*-*-*-*-*")
                    print(f"Processing response from model {n}/{n_models}-{model} for question {q}/{n_questions}-{base_name}")
                
                answer_text = model_data['choices'][0]['message']['content']
                
                if 'created' in model_data:
                    answer_date_unix = model_data['created']
                else:
                    answer_date_unix = None
                
                if ADD_CITATIONS_TO_ANSWER:
                    answer_citations = ""
                    c=0
                    if 'citations' in model_data:
                        for citation_text in model_data['citations']:
                            c=c+1
                            answer_citations = answer_citations + "\n" + f"citation[{c}]: "+ citation_text
                        answer_citations = answer_citations + "\n"
                    else:
                        answer_citations = "\n"
                    answer_text = answer_text + answer_citations

                if THINK_MARKER_TO_BE_IGNORED:
                    answer_text = re.sub(r'<think>.*?</think>', '', answer_text, flags=re.DOTALL)

                api_response = get_analysis_response(
                    question,
                    answer_text,
                    target_answer,
                    infos_cruciales,
                    infos_a_eviter,
                    analysis_model,
                    verbose
                )

                report += f"Réponse du modèle {model} pour {base_name}:\n"
                if answer_date_unix: report += f"Date de la réponse: {convert_unix_timestamp_to_human_readable(answer_date_unix)}\n"
                report += f"|-_-|---|-¯-|---|-_-|---|-¯-|---|-_-|---|-¯-|---|-_-|\n\n"
                report += f"{answer_text}\n"
                report += f"|-_-|---|-¯-|---|-_-|---|-¯-|---|-_-|---|-¯-|---|-_-|\n\n"
                report += f"Analyse de la réponse du modèle {model} pour {base_name}:\n"
                report += f"-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_\n"
                report += f"{api_response}\n"
                report += f"-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯\n"
                report += f"*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*\n\n"

                if verbose:
                    print("*-*-*-*-*-*-*-*-*")
                    print(f"Processed response from model {n}/{n_models}-{model} for question {q}/{n_questions}-{base_name}")

            #report += "(c) 2025 Lavery De Billy S.E.N.C.R.L."
            analysis_filename = os.path.join(analysis_dir, question_file.replace('.q', '.txt'))
            with open(analysis_filename, 'w', encoding='utf-8') as f:
                f.write(report)

            if verbose:
                print("*-*-*-*-*-*-*-*-*")
                print(f"Completed analysis for {q}/{n_questions}-{base_name}\nSaved in {analysis_dir} under the name {analysis_filename}")
                

def convert_unix_timestamp_to_human_readable(unix_timestamp):
    createdDateTime = datetime.datetime.fromtimestamp(unix_timestamp)
    year = createdDateTime.year
    month = createdDateTime.month
    day = createdDateTime.day
    hour = createdDateTime.hour
    minute = createdDateTime.minute
    second = createdDateTime.second

    return f"{year}-{(month < 10 and '0' or '')}{month}-{(day < 10 and '0' or '')}{day} {(hour < 10 and '0' or '')}{hour}:{(minute < 10 and '0' or '')}{minute}:{(second < 10 and '0' or '')}{second}"

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run model answer analysis.")
    parser.add_argument('--verbose', action='store_true', help="Enable verbose mode")
    args = parser.parse_args()
    main(verbose=args.verbose)