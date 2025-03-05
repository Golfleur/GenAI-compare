import os
import json
import argparse
import requests
import yaml
import re
import datetime
# import markdown
from pathlib import Path

THINK_MARKER_TO_BE_IGNORED = True
DO_NOT_ADD_A_SYSTEM_PROMPT = True
ADD_CITATIONS_TO_ANSWER = False
CONFIG_PATH = './config/config.yaml'

def load_connect_owui(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

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
    CONFIG_PATH = './config/config.yaml'
    config = load_connect_owui('./config/connect-owui.yaml')
    API_KEY = config['open_webui']['api_key']
    BASE_URL = config['open_webui']['location']
    API_URL = f"{BASE_URL}/api/chat/completions"
    
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

def convert_unix_timestamp_to_human_readable(unix_timestamp):
    createdDateTime = datetime.datetime.fromtimestamp(unix_timestamp)
    year = createdDateTime.year
    month = createdDateTime.month
    day = createdDateTime.day
    hour = createdDateTime.hour
    minute = createdDateTime.minute
    second = createdDateTime.second
    return f"{year}-{(month < 10 and '0' or '')}{month}-{(day < 10 and '0' or '')}{day} {(hour < 10 and '0' or '')}{hour}:{(minute < 10 and '0' or '')}{minute}:{(second < 10 and '0' or '')}{second}"

def main(verbose=False):
    CONFIG_PATH = './config/config.yaml'
    config_yaml_path = './config/selected_questions.yaml'
    questions_dir = './questions'
    answers_dir = './answers'
    targets_dir = './targets'
    analysis_dir = './analysis'
    
    os.makedirs(analysis_dir, exist_ok=True)
    analysis_model = load_analysis_model()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
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
    
    # Create a summary report for all questions
    summary_data = {
        "analysis_timestamp": datetime.datetime.now().isoformat(),
        "analysis_model": analysis_model,
        "questions": []
    }
    
    # Create markdown summary
    md_summary = f"# Analysis Report\n\n"
    md_summary += f"**Analysis performed by:** {analysis_model}  \n"
    md_summary += f"**Date:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n\n"
    md_summary += f"## Questions Analyzed\n\n"
    
    # Create HTML summary
    html_summary = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Analysis Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 1200px; margin: 0 auto; padding: 20px; }}
            h1, h2, h3 {{ color: #2c3e50; }}
            .question-card {{ border: 1px solid #ddd; border-radius: 8px; margin-bottom: 20px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .model-response {{ background-color: #f9f9f9; border-left: 4px solid #3498db; padding: 10px; margin: 10px 0; }}
            .analysis {{ background-color: #f0f7ff; border-left: 4px solid #9b59b6; padding: 10px; margin: 10px 0; }}
            .target {{ background-color: #f0fff0; border-left: 4px solid #2ecc71; padding: 10px; margin: 10px 0; }}
            .crucial-info {{ background-color: #fffaf0; border-left: 4px solid #f39c12; padding: 10px; margin: 10px 0; }}
            .avoid-info {{ background-color: #fff0f0; border-left: 4px solid #e74c3c; padding: 10px; margin: 10px 0; }}
            .separator {{ border-top: 1px dashed #ddd; margin: 20px 0; }}
            pre {{ white-space: pre-wrap; }}
        </style>
    </head>
    <body>
        <h1>Analysis Report</h1>
        <p><strong>Analysis performed by:</strong> {analysis_model}</p>
        <p><strong>Date:</strong> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <h2>Questions Analyzed</h2>
    """
    
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
            
            # Create a question data structure for the JSON report
            question_data = {
                "question_id": base_name,
                "question_text": question,
                "target_answer": target_answer,
                "crucial_info": infos_cruciales,
                "avoid_info": infos_a_eviter,
                "model_responses": []
            }
            
            # Create markdown report for this question
            md_report = f"# Analysis for {base_name}\n\n"
            md_report += f"## Question\n\n"
            md_report += f"```\n{question}\n```\n\n"
            md_report += f"## Target Answer\n\n"
            md_report += f"```\n{target_answer}\n```\n\n"
            md_report += f"## Crucial Information\n\n"
            md_report += f"```\n{infos_cruciales}\n```\n\n"
            md_report += f"## Information to Avoid\n\n"
            md_report += f"```\n{infos_a_eviter}\n```\n\n"
            md_report += f"## Model Responses\n\n"
            
            # Create HTML report for this question
            html_report = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Analysis for {base_name}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 1200px; margin: 0 auto; padding: 20px; }}
                    h1, h2, h3 {{ color: #2c3e50; }}
                    .question-card {{ border: 1px solid #ddd; border-radius: 8px; margin-bottom: 20px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                    .model-response {{ background-color: #f9f9f9; border-left: 4px solid #3498db; padding: 10px; margin: 10px 0; }}
                    .analysis {{ background-color: #f0f7ff; border-left: 4px solid #9b59b6; padding: 10px; margin: 10px 0; }}
                    .target {{ background-color: #f0fff0; border-left: 4px solid #2ecc71; padding: 10px; margin: 10px 0; }}
                    .crucial-info {{ background-color: #fffaf0; border-left: 4px solid #f39c12; padding: 10px; margin: 10px 0; }}
                    .avoid-info {{ background-color: #fff0f0; border-left: 4px solid #e74c3c; padding: 10px; margin: 10px 0; }}
                    .separator {{ border-top: 1px dashed #ddd; margin: 20px 0; }}
                    pre {{ white-space: pre-wrap; }}
                </style>
            </head>
            <body>
                <h1>Analysis for {base_name}</h1>
                <div class="question-card">
                    <h2>Question</h2>
                    <pre>{question}</pre>
                    <h2>Target Answer</h2>
                    <div class="target">
                        <pre>{target_answer}</pre>
                    </div>
                    <h2>Crucial Information</h2>
                    <div class="crucial-info">
                        <pre>{infos_cruciales}</pre>
                    </div>
                    <h2>Information to Avoid</h2>
                    <div class="avoid-info">
                        <pre>{infos_a_eviter}</pre>
                    </div>
                </div>
                <h2>Model Responses</h2>
            """
            
            # Create plain text report (keeping your original format for compatibility)
            text_report = ""
            text_report += f"*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*\n"
            text_report += f"Analyse pour {base_name}\n"
            text_report += f"Question:\n"
            text_report += f"-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_\n"
            text_report += f"\n{question}\n"
            text_report += f"-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯\n"
            text_report += f"Réponse attendue pour {base_name}\n"
            text_report += f"-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_\n"
            text_report += f"{target_answer}\n"
            text_report += f"-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯\n"
            text_report += f"Informations cruciales attendues pour {base_name}:\n"
            text_report += f"-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_\n"
            text_report += f"{infos_cruciales}\n"
            text_report += f"-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯\n"
            text_report += f"Informations à éviter pour {base_name}:\n"
            text_report += f"-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_\n"
            text_report += f"{infos_a_eviter}\n"
            text_report += f"-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯\n"
            text_report += f"--------------------------------------------------------\n"
            
            # Add to summary
            md_summary += f"- [{base_name}](./analysis/{base_name}.md)\n"
            html_summary += f'<div class="question-card"><h3>{base_name}</h3><p>{question[:200]}...</p><p><a href="./analysis/{base_name}.html">View detailed analysis</a></p></div>'
            
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
                    answer_date = convert_unix_timestamp_to_human_readable(answer_date_unix)
                else:
                    answer_date_unix = None
                    answer_date = "Unknown"
                
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
                
                # Fix for the think marker regex
                if THINK_MARKER_TO_BE_IGNORED:
                    answer_text = re.sub(r'', '', answer_text, flags=re.DOTALL)
                
                api_response = get_analysis_response(
                    question,
                    answer_text,
                    target_answer,
                    infos_cruciales,
                    infos_a_eviter,
                    analysis_model,
                    verbose
                )
                
                # Add to model responses in JSON
                question_data["model_responses"].append({
                    "model_name": model,
                    "response_date": answer_date,
                    "response_text": answer_text,
                    "analysis": api_response
                })
                
                # Add to markdown report
                md_report += f"### Model: {model}\n\n"
                md_report += f"**Response Date:** {answer_date}\n\n"
                md_report += f"#### Response\n\n"
                md_report += f"```\n{answer_text}\n```\n\n"
                md_report += f"#### Analysis\n\n"
                md_report += f"```\n{api_response}\n```\n\n"
                md_report += f"---\n\n"
                
                # Add to HTML report
                html_report += f"""
                <div class="question-card">
                    <h3>Model: {model}</h3>
                    <p><strong>Response Date:</strong> {answer_date}</p>
                    <h4>Response</h4>
                    <div class="model-response">
                        <pre>{answer_text}</pre>
                    </div>
                    <h4>Analysis</h4>
                    <div class="analysis">
                        <pre>{api_response}</pre>
                    </div>
                </div>
                """
                
                # Add to text report
                text_report += f"Réponse du modèle {model} pour {base_name}:\n"
                if answer_date_unix:
                    text_report += f"Date de la réponse: {answer_date}\n"
                text_report += f"|-_-|---|-¯-|---|-_-|---|-¯-|---|-_-|---|-¯-|---|-_-|\n\n"
                text_report += f"{answer_text}\n"
                text_report += f"|-_-|---|-¯-|---|-_-|---|-¯-|---|-_-|---|-¯-|---|-_-|\n\n"
                text_report += f"Analyse de la réponse du modèle {model} pour {base_name}:\n"
                text_report += f"-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_-_\n"
                text_report += f"{api_response}\n"
                text_report += f"-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯-¯\n"
                text_report += f"*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*\n\n"
                
                if verbose:
                    print("*-*-*-*-*-*-*-*-*")
                    print(f"Processed response from model {n}/{n_models}-{model} for question {q}/{n_questions}-{base_name}")
            
            # Close HTML report
            html_report += """
            </body>
            </html>
            """
            
            # Save all report formats
            # 1. Original text format (for backward compatibility)
            text_filename = os.path.join(analysis_dir, f"{base_name}.txt")
            with open(text_filename, 'w', encoding='utf-8') as f:
                f.write(text_report)
                
            # 2. Markdown format (for better display in Streamlit)
            md_filename = os.path.join(analysis_dir, f"{base_name}.md")
            with open(md_filename, 'w', encoding='utf-8') as f:
                f.write(md_report)
                
            # 3. HTML format (for rich display)
            html_filename = os.path.join(analysis_dir, f"{base_name}.html")
            with open(html_filename, 'w', encoding='utf-8') as f:
                f.write(html_report)
                
            # 4. JSON format (for programmatic access)
            json_filename = os.path.join(analysis_dir, f"{base_name}.json")
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(question_data, f, indent=2, ensure_ascii=False)
            
            # Add to summary
            summary_data["questions"].append(question_data)
            
            if verbose:
                print("*-*-*-*-*-*-*-*-*")
                print(f"Completed analysis for {q}/{n_questions}-{base_name}\nSaved in {analysis_dir}")
    
    # Finish and save summary HTML
    html_summary += """
    </body>
    </html>
    """
    
    # Save summary files
    with open(os.path.join(analysis_dir, f"summary_{timestamp}.md"), 'w', encoding='utf-8') as f:
        f.write(md_summary)
        
    with open(os.path.join(analysis_dir, f"summary_{timestamp}.html"), 'w', encoding='utf-8') as f:
        f.write(html_summary)
        
    with open(os.path.join(analysis_dir, f"summary_{timestamp}.json"), 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    
    if verbose:
        print("*-*-*-*-*-*-*-*-*")
        print(f"Analysis complete. Summary saved to {analysis_dir}/summary_{timestamp}.[md/html/json]")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run model answer analysis.")
    parser.add_argument('--verbose', action='store_true', help="Enable verbose mode")
    args = parser.parse_args()
    main(verbose=args.verbose)