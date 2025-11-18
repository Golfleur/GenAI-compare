import os
import json
import argparse
import requests
import yaml
import re
import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

THINK_MARKER_TO_BE_IGNORED = True
DO_NOT_ADD_A_SYSTEM_PROMPT = True
ADD_CITATIONS_TO_ANSWER = False
CONFIG_PATH = './config/config.yaml'

def get_color_for_score(score):
    """Return a color based on the score (red for low, yellow for medium, green for high)"""
    if score < 4:
        return "#e74c3c"  # Red
    elif score < 7:
        return "#f39c12"  # Orange/Yellow
    else:
        return "#2ecc71"  # Green

def load_connect_owui(file_path):
    """Load the configuration file and return the active configuration.
    
    Environment variables take precedence over YAML configuration:
    - OPENWEBUI_API_KEY: API key for Open WebUI
    - OPENWEBUI_BASE_URL: Base URL for Open WebUI API
    """
    try:
        with open(file_path, 'r', encoding="utf-8") as file:
            config_data = yaml.safe_load(file)
        # Check if the file contains the configs list structure
        if isinstance(config_data, dict) and 'configs' in config_data:
            # Look for active configuration
            configs = config_data.get('configs', [])
            for config in configs:
                if config.get('active', False):
                    print(f"Using active configuration: {config.get('name', 'Unnamed')}")
                    return config
            # If no active config is marked, return the first one
            if configs:
                print(f"Using default configuration: {configs[0].get('name', 'Unnamed')}")
                return configs[0]
            print("No configurations found in the config file")
            return {}
        else:
            # Handle old format for backward compatibility
            print("Using legacy config format")
            return config_data
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return {}

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
    # Check for environment variables first (takes precedence)
    API_KEY = os.getenv('OPENWEBUI_API_KEY')
    BASE_URL = os.getenv('OPENWEBUI_BASE_URL')
    
    if API_KEY and BASE_URL:
        if verbose:
            print("Using API credentials from environment variables for analysis")
    else:
        # Fall back to configuration file
        config = load_connect_owui('./config/connect-owui.yaml')
        # Extract API credentials from the selected configuration
        if 'open_webui' in config:
            API_KEY = config['open_webui'].get('api_key', '')
            BASE_URL = config['open_webui'].get('location', '')
        else:
            print("Warning: Invalid configuration format. Missing 'open_webui' section.")
            return "Error: Invalid configuration format"
    
    # Validate credentials
    if not API_KEY or not BASE_URL:
        print("Error: API credentials not found")
        return "Error: Missing API credentials"
    
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
            'stream': False,
        }
    else:
        data = {
            'model': analysis_model,
            'messages': [
                {'role': 'system', 'content': "Tu fournis une évaluation en français de la qualité de la réponse par rapport à la cible."},
                {'role': 'user', 'content': prompt}
            ],
            'stream': False,
        }
    if verbose:
        print("*-*-*-*-*-*-*-*-*")
        print(f"Making request to: {API_URL}")
        print(f"Using model: {analysis_model}")
        # print(f"Response data: {json.dumps(data, indent=2)}")
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        if verbose:
            print("*-*-*-*-*-*-*-*-*")
            print(f"Response status: {response.status_code}")
            # print(f"Response headers: {dict(response.headers)}")
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

def generate_executive_summary(summary_data, analysis_dir, timestamp):
    """
    Generate a one-page executive summary of the analysis results.
    """
    # Extract key metrics
    total_questions = len(summary_data["questions"])
    models_analyzed = list(summary_data["model_performance"].keys())
    
    # Create one-page HTML summary
    one_pager = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Analysis Executive Summary</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.4; max-width: 1000px; margin: 0 auto; padding: 20px; }}
            h1, h2 {{ color: #2c3e50; margin-top: 10px; }}
            .header {{ text-align: center; margin-bottom: 20px; }}
            .summary-box {{ background-color: #f8f9fa; border-radius: 8px; padding: 15px; margin-bottom: 15px; }}
            .model-comparison {{ display: flex; justify-content: space-between; margin: 20px 0; }}
            .model-card {{ flex: 1; margin: 0 10px; padding: 10px; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
            .model-name {{ font-weight: bold; font-size: 1.1em; }}
            .score {{ font-size: 1.8em; font-weight: bold; text-align: center; margin: 10px 0; }}
            .highlights {{ margin-top: 20px; }}
            .chart-container {{ height: 200px; margin: 20px 0; }}
            .footer {{ font-size: 0.8em; text-align: center; margin-top: 20px; color: #7f8c8d; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>AI Model Evaluation: Executive Summary</h1>
            <p>Analysis Date: {datetime.datetime.now().strftime('%Y-%m-%d')}</p>
        </div>
        
        <div class="summary-box">
            <h2>Overview</h2>
            <p><strong>{total_questions}</strong> questions analyzed across <strong>{len(models_analyzed)}</strong> AI models</p>
            <p>Analysis performed by: <strong>{summary_data["analysis_model"]}</strong></p>
        </div>
        
        <h2>Model Performance Comparison</h2>
        <div class="model-comparison">
    """
    
    # Add a card for each model
    for model, data in summary_data["model_performance"].items():
        avg_score = data["average_score"]
        score_color = get_color_for_score(avg_score)
        
        # Get top strength and weakness
        top_strength = data["top_strengths"][0]["text"] if data["top_strengths"] else "None identified"
        top_weakness = data["top_weaknesses"][0]["text"] if data["top_weaknesses"] else "None identified"
        
        one_pager += f"""
            <div class="model-card">
                <div class="model-name">{model}</div>
                <div class="score" style="color: {score_color};">{avg_score:.1f}/10</div>
                <p><strong>Questions:</strong> {data["questions_answered"]}</p>
                <p><strong>Key Strength:</strong> {top_strength}</p>
                <p><strong>Key Weakness:</strong> {top_weakness}</p>
            </div>
        """
    
    # Add top-performing questions section
    one_pager += """
        </div>
        
        <div class="highlights">
            <h2>Key Findings</h2>
            <table>
                <tr>
                    <th>Finding</th>
                    <th>Details</th>
                </tr>
    """
    
    # Generate key findings based on the data
    findings = []
    
    # Find best performing model
    best_model = max(summary_data["model_performance"].items(), 
                     key=lambda x: x[1]["average_score"] if x[1]["questions_answered"] > 0 else 0)
    findings.append({
        "finding": "Best Performing Model",
        "details": f"{best_model[0]} with average score of {best_model[1]['average_score']:.1f}/10"
    })
    
    # Find common strengths across models
    all_strengths = {}
    for model, data in summary_data["model_performance"].items():
        for strength in data["top_strengths"]:
            all_strengths[strength["text"]] = all_strengths.get(strength["text"], 0) + strength["mentions"]
    
    if all_strengths:
        common_strength = max(all_strengths.items(), key=lambda x: x[1])
        findings.append({
            "finding": "Common Strength",
            "details": f"{common_strength[0]} (mentioned {common_strength[1]} times)"
        })
    
    # Find common weaknesses across models
    all_weaknesses = {}
    for model, data in summary_data["model_performance"].items():
        for weakness in data["top_weaknesses"]:
            all_weaknesses[weakness["text"]] = all_weaknesses.get(weakness["text"], 0) + weakness["mentions"]
    
    if all_weaknesses:
        common_weakness = max(all_weaknesses.items(), key=lambda x: x[1])
        findings.append({
            "finding": "Common Weakness",
            "details": f"{common_weakness[0]} (mentioned {common_weakness[1]} times)"
        })
    
    # Add findings to the table
    for finding in findings:
        one_pager += f"""
                <tr>
                    <td><strong>{finding["finding"]}</strong></td>
                    <td>{finding["details"]}</td>
                </tr>
        """
    
    # Complete the HTML
    one_pager += """
            </table>
        </div>
        
        <div class="footer">
            <p>For detailed analysis, please refer to the complete summary report.</p>
        </div>
    </body>
    </html>
    """
    
    # Save the one-pager
    with open(os.path.join(analysis_dir, f"executive_summary_{timestamp}.html"), 'w', encoding='utf-8') as f:
        f.write(one_pager)
    
    print(f"Executive summary saved to {analysis_dir}/executive_summary_{timestamp}.html")

def main(verbose=False):
    CONFIG_PATH = './config/config.yaml'
    config_yaml_path = './config/selected_questions.yaml'
    questions_dir = './questions'
    answers_dir = './answers'
    targets_dir = './targets'
    analysis_dir = './analysis'
    os.makedirs(analysis_dir, exist_ok=True)
    # Load the analysis model
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
        "questions": [],
        "model_performance": {}  # New section to track performance by model
    }

    # Create markdown summary
    md_summary = f"# Analysis Report\n\n"
    md_summary += f"**Analysis performed by:** {analysis_model}  \n"
    md_summary += f"**Date:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n\n"

    # Add model performance section to markdown
    md_summary += f"## Overall Model Performance\n\n"
    md_summary += f"| Model | Questions Answered | Average Score | Key Strengths | Key Weaknesses |\n"
    md_summary += f"|-------|-------------------|---------------|---------------|----------------|\n"

    # Create HTML summary with enhanced model performance section
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
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ padding: 10px; border: 1px solid #ddd; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .model-card {{ background-color: #f8f9fa; border-radius: 8px; padding: 15px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
            .model-stats {{ display: flex; justify-content: space-between; flex-wrap: wrap; }}
            .stat-box {{ flex: 1; min-width: 200px; margin: 10px; padding: 15px; background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
            .progress-bar {{ height: 10px; background: #e0e0e0; border-radius: 5px; margin-top: 5px; }}
            .progress-fill {{ height: 100%; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <h1>Analysis Report</h1>
        <p><strong>Analysis performed by:</strong> {analysis_model}</p>
        <p><strong>Date:</strong> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <h2>Overall Model Performance</h2>
        <div id="model-performance-section">
            <!-- Model performance cards will be inserted here -->
        </div>
        
        <h2>Questions Analyzed</h2>
    """

    # Dictionary to track model performance
    model_performance = {}

    q = 0
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
            q = q + 1
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
            html_summary += f'<div class="question-card"><h3>{base_name}</h3><p>{question[:200]}...</p><p><a href="./{base_name}.html">View detailed analysis</a></p></div>'
            answers_data = read_json_file(answer_path)
            n = 0
            n_models = len(answers_data)
            for model, model_data in answers_data.items():
                n = n + 1
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
                    c = 0
                    if 'citations' in model_data:
                        for citation_text in model_data['citations']:
                            c = c + 1
                            answer_citations = answer_citations + "\n" + f"citation[{c}]: " + citation_text
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
                
                # Track model performance
                if model not in model_performance:
                    model_performance[model] = {
                        "questions_answered": 0,
                        "total_score": 0,
                        "strengths": {},
                        "weaknesses": {},
                        "responses": []
                    }
                
                model_performance[model]["questions_answered"] += 1
                model_performance[model]["responses"].append({
                    "question_id": base_name,
                    "analysis": api_response
                })
                
                # Extract a simple score (this is just an example - implement your own scoring logic)
                # For example, look for phrases like "score: 8/10" or "rating: 7/10" in the analysis
                score_match = re.search(r'(?:score|rating|note|globale)[:\s]+(\d+)(?:/|\s*out\s*of\s*|\s*sur\s*)10', api_response, re.IGNORECASE)
                if score_match:
                    score = int(score_match.group(1))
                    model_performance[model]["total_score"] += score
                
                # Extract strengths and weaknesses (simplified example)
                strengths_section = re.search(r'(?:Forces|Points forts|Strengths)[:\s]+(.*?)(?=Faiblesses|Weaknesses|Points faibles|$)', 
                                            api_response, re.IGNORECASE | re.DOTALL)
                weaknesses_section = re.search(r'(?:Faiblesses|Weaknesses|Points faibles)[:\s]+(.*?)(?=\n\n|$)', 
                                            api_response, re.IGNORECASE | re.DOTALL)
                
                if strengths_section:
                    strengths_text = strengths_section.group(1).strip()
                    # Extract bullet points or key phrases
                    strengths = re.findall(r'[-•*]\s*(.*?)(?=\n[-•*]|\n\n|$)', strengths_text, re.DOTALL)
                    for strength in strengths:
                        strength = strength.strip()
                        if strength:
                            model_performance[model]["strengths"][strength] = model_performance[model]["strengths"].get(strength, 0) + 1
                
                if weaknesses_section:
                    weaknesses_text = weaknesses_section.group(1).strip()
                    # Extract bullet points or key phrases
                    weaknesses = re.findall(r'[-•*]\s*(.*?)(?=\n[-•*]|\n\n|$)', weaknesses_text, re.DOTALL)
                    for weakness in weaknesses:
                        weakness = weakness.strip()
                        if weakness:
                            model_performance[model]["weaknesses"][weakness] = model_performance[model]["weaknesses"].get(weakness, 0) + 1
                
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
    
    # After processing all questions, calculate overall metrics and update the summary
    model_performance_html = ""

    for model, data in model_performance.items():
        questions_answered = data["questions_answered"]
        avg_score = data["total_score"] / questions_answered if questions_answered > 0 and data["total_score"] > 0 else 0
        
        # Get top 3 strengths and weaknesses
        top_strengths = sorted(data["strengths"].items(), key=lambda x: x[1], reverse=True)[:3]
        top_weaknesses = sorted(data["weaknesses"].items(), key=lambda x: x[1], reverse=True)[:3]
        
        strengths_text = "; ".join([f"{s[0]} ({s[1]} mentions)" for s in top_strengths]) if top_strengths else "No clear strengths identified"
        weaknesses_text = "; ".join([f"{w[0]} ({w[1]} mentions)" for w in top_weaknesses]) if top_weaknesses else "No clear weaknesses identified"
        
        # Add to markdown summary
        md_summary += f"| {model} | {questions_answered} | {avg_score:.2f}/10 | {strengths_text} | {weaknesses_text} |\n"
        
        # Add to JSON data
        summary_data["model_performance"][model] = {
            "questions_answered": questions_answered,
            "average_score": avg_score,
            "top_strengths": [{"text": s[0], "mentions": s[1]} for s in top_strengths],
            "top_weaknesses": [{"text": w[0], "mentions": w[1]} for w in top_weaknesses]
        }
        
        # Create HTML card for this model
        score_percent = int(avg_score * 10)
        model_performance_html += f"""
        <div class="model-card">
            <h3>{model}</h3>
            <div class="model-stats">
                <div class="stat-box">
                    <h4>Questions Answered</h4>
                    <p>{questions_answered}</p>
                </div>
                <div class="stat-box">
                    <h4>Average Score</h4>
                    <p>{avg_score:.2f}/10</p>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {score_percent}%; background-color: {get_color_for_score(avg_score)};"></div>
                    </div>
                </div>
            </div>
            <div class="model-stats">
                <div class="stat-box">
                    <h4>Key Strengths</h4>
                    <ul>
                        {"".join([f'<li>{s[0]} <small>({s[1]} mentions)</small></li>' for s in top_strengths]) if top_strengths else '<li>No clear strengths identified</li>'}
                    </ul>
                </div>
                <div class="stat-box">
                    <h4>Key Weaknesses</h4>
                    <ul>
                        {"".join([f'<li>{w[0]} <small>({w[1]} mentions)</small></li>' for w in top_weaknesses]) if top_weaknesses else '<li>No clear weaknesses identified</li>'}
                    </ul>
                </div>
            </div>
        </div>
        """

    # Add model performance section to HTML
    html_summary = html_summary.replace('<!-- Model performance cards will be inserted here -->', model_performance_html)

    # Add questions section to markdown summary
    md_summary += f"\n## Questions Analyzed\n\n"
    for question_data in summary_data["questions"]:
        md_summary += f"- [{question_data['question_id']}](./analysis/{question_data['question_id']}.md)\n"

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

        # Save summary files
    with open(os.path.join(analysis_dir, f"summary_{timestamp}.md"), 'w', encoding='utf-8') as f:
        f.write(md_summary)
    with open(os.path.join(analysis_dir, f"summary_{timestamp}.html"), 'w', encoding='utf-8') as f:
        f.write(html_summary)
    with open(os.path.join(analysis_dir, f"summary_{timestamp}.json"), 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    generate_executive_summary(summary_data, analysis_dir, timestamp)

    if verbose:
        print("*-*-*-*-*-*-*-*-*")
        print(f"Analysis complete. Summary saved to {analysis_dir}/summary_{timestamp}.[md/html/json]")
        print(f"Executive summary saved to {analysis_dir}/executive_summary_{timestamp}.html")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run model answer analysis.")
    parser.add_argument('--verbose', action='store_true', help="Enable verbose mode")
    args = parser.parse_args()
    main(verbose=args.verbose)