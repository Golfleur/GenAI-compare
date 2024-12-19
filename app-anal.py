import yaml
import os
import requests
import json
from collections import defaultdict

def load_connect_owui(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

config = load_connect_owui('./config/connect-owui.yaml')
API_KEY = config['open_webui']['api_key']
BASE_URL = config['open_webui']['location']
API_URL = f"{BASE_URL}/api/chat/completions"

# Directory paths
questions_dir = './questions'
targets_dir = './targets'
analysis_dir = './analysis'
models = ['gemini_test.gemini-1.5-flash-latest', 
            'anthropic.claude-3-5-haiku-latest',
            'gpt-4o-mini',
            'llama3.2:latest']

# Read the content of the file
def read_file_content(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read().strip()
        
def read_json_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

# Function to get response from the Open WebUI API
def get_model_response(model, question):
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        'model': model,
        'messages': [{'role': 'user', 'content': question}]
    }
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        print(f"Error with API request for model {model}: {e}")
        return ""

def analyze_response(response, target):
    score = 0
    analysis = []
    
    # Check for crucial information
    if target['infos_cruciales'].lower() in response.lower():
        score += 2
        analysis.append("Contains crucial information")
    else:
        analysis.append("Missing crucial information")

    # Check for information to avoid
    if target['infos_a_eviter'].lower() in response.lower():
        score -= 1
        analysis.append("Contains information to avoid")
    else:
        score += 1
        analysis.append("Properly avoids incorrect information")

    # Check alignment with target response
    if any(phrase.lower() in response.lower() for phrase in target['reponse_cible'].split()):
        score += 1
        analysis.append("Aligns with target response")

    return {
        'score': score,
        'analysis': analysis
    }


# Run the analysis process
def main():
    os.makedirs(analysis_dir, exist_ok=True)
    overall_scores = defaultdict(int)

    for question_file in os.listdir(questions_dir):
        if question_file.endswith('.q'):
            base_name = question_file[:-2]

            question_path = os.path.join(questions_dir, question_file)
            target_path = os.path.join(targets_dir, question_file.replace('.q', '.t'))
            
            question = read_file_content(question_path)
            target = read_json_file(target_path)
            
            report = f"Analysis for {base_name}\n"
            report += f"Question: {question}\n\n"
            
            model_rankings = []
            for model in models:
                response = get_model_response(model, question)
                analysis_result = analyze_response(response, target)
                
                model_rankings.append((model, analysis_result['score']))
                overall_scores[model] += analysis_result['score']
                
                report += f"\nModel: {model}\n"
                report += f"Score: {analysis_result['score']}\n"
                report += "Analysis:\n"
                for point in analysis_result['analysis']:
                    report += f"- {point}\n"
            
            # Add ranking for this question
            model_rankings.sort(key=lambda x: x[1], reverse=True)
            report += "\nRankings for this question:\n"
            for rank, (model, score) in enumerate(model_rankings, 1):
                report += f"{rank}. {model} (score: {score})\n"
            
            # Save individual question analysis
            analysis_filename = os.path.join(analysis_dir, question_file.replace('.q', '.txt'))
            with open(analysis_filename, 'w', encoding='utf-8') as f:
                f.write(report)
    
    # Generate overall analysis
    overall_report = "Overall Model Performance\n\n"
    sorted_models = sorted(overall_scores.items(), key=lambda x: x[1], reverse=True)
    for rank, (model, score) in enumerate(sorted_models, 1):
        overall_report += f"{rank}. {model}: Total Score {score}\n"
    
    with open(f"{analysis_dir}/overall_analysis.txt", 'w', encoding='utf-8') as f:
        f.write(overall_report)


if __name__ == '__main__':
    main()
