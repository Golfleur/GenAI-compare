import streamlit as st
import json
import os
import yaml
import requests
import subprocess
from datetime import datetime
from pathlib import Path
import pandas as pd

# Ensure directories exist for storing files
os.makedirs('./questions', exist_ok=True)
os.makedirs('./targets', exist_ok=True)
os.makedirs('./answers', exist_ok=True)
os.makedirs('./config', exist_ok=True)

# --- Configuration Functions ---
def load_connect_owui(file_path):
    try:
        with open(file_path, 'r', encoding="utf-8") as file:
            return yaml.safe_load(file) or {}
    except (FileNotFoundError, yaml.YAMLError):
        return {}

def save_connect_owui(config, file_path):
    with open(file_path, 'w') as file:
        yaml.dump(config, file)

# Configuration paths and settings
CONFIG_PATH = './config/config.yaml'
config_file = './config/connect-owui.yaml'
config = load_connect_owui(config_file)
API_KEY = config.get('open_webui', {}).get('api_key', '')
BASE_URL = config.get('open_webui', {}).get('location', '')
API_URL = f"{BASE_URL}/api/models" if BASE_URL else ""

# --- Question Management Functions ---
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

# --- Model Management Functions ---
def test_connection(local=False):
    config = load_connect_owui(config_file)
    API_KEY = config.get('open_webui', {}).get('api_key', '')
    BASE_URL = config.get('open_webui', {}).get('location', '')
    if not API_KEY or not BASE_URL:
        if not local:
            return {'status': 'error', 'message': 'API key and location are required.'}
        return False
    try:
        response = requests.get(f"{BASE_URL}/api/models", headers={'Authorization': f'Bearer {API_KEY}'})
        if response.status_code == 200:
            if not local:
                return {'status': 'success', 'message': 'Connexion réussie!'}
            return True
        else:
            if not local:
                return {'status': 'error', 'message': f"Failed to connect: {response.status_code} - {response.text}"}
            return False
    except requests.RequestException as e:
        if not local:
            return {'status': 'error', 'message': str(e)}
        return False

def fetch_models():
    config = load_connect_owui(config_file)
    API_KEY = config.get('open_webui', {}).get('api_key', '')
    BASE_URL = config.get('open_webui', {}).get('location', '')
    API_URL = f"{BASE_URL}/api/models"
    if test_connection(True):
        headers = {'Authorization': f'Bearer {API_KEY}'}
        response = requests.get(API_URL, headers=headers)
        if response.status_code == 200:
            try:
                response_data = response.json()
                models_data = response_data.get('data', [])
                models_data.sort(key=lambda x: x.get('name', ''))
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
                            'family': 'Perplexity',
                            'parameter_size': 'Variable'
                        }                     
                    # Anthropic-specific details
                    elif 'anthropic' in enriched_model['name'].lower() or 'claude' in enriched_model['name'].lower():
                        enriched_model['model_type'] = 'Anthropic'
                        enriched_model['details'] = {
                            'family': 'Claude',
                            'parameter_size': 'Variable'
                        }
                    # Mistral-specific details
                    elif 'mistral' in enriched_model['name'].lower():
                        enriched_model['model_type'] = 'Mistral'
                        enriched_model['details'] = {
                            'family': 'Mistral',
                            'parameter_size': 'Variable'
                        }
                    enriched_models.append(enriched_model)
                return enriched_models
            except ValueError as e:
                print(f"Error parsing JSON: {e}")
                return [f"{e}"]
        else:
            print(f"Failed to fetch models: {response.content}")
            return [f"{response.content}"]
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

# --- Streamlit UI ---
st.set_page_config(
    page_title="LLM Question Management",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Choose a page", 
    ["Home", "Add Question", "View Questions", "Edit Questions", "Delete Questions", 
     "Select Questions", "Manual Entry", "Models", "Select Comparator", "Configuration", "View Analysis"]
)

# --- HOME PAGE ---
if page == "Home":
    st.title("LLM Question Management System")
    st.write("Welcome to the LLM Question Management System. Use the sidebar to navigate.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Run Comparison")
        if st.button("Run Compare Script", key="run_compare"):
            st.info("Running comparison script...")
            output_placeholder = st.empty()
            
            process = subprocess.Popen(
                ["python", "-u", "app-compare.py", "--verbose"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Display output in real-time
            output_text = ""
            while True:
                output_line = process.stdout.readline()
                if output_line == '' and process.poll() is not None:
                    break
                if output_line:
                    output_text += output_line
                    output_placeholder.text_area("Output:", output_text, height=400)
                    
            return_code = process.poll()
            if return_code == 0:
                st.success("Script executed successfully!")
            else:
                st.error(f"Script execution failed with return code {return_code}")
    
    with col2:
        st.subheader("Run Analysis")
        if st.button("Run Analysis Script", key="run_analysis"):
            st.info("Running analysis script...")
            output_placeholder = st.empty()
            
            process = subprocess.Popen(
                ["python", "-u", "app-anal.py", "--verbose"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Display output in real-time
            output_text = ""
            while True:
                output_line = process.stdout.readline()
                if output_line == '' and process.poll() is not None:
                    break
                if output_line:
                    output_text += output_line
                    output_placeholder.text_area("Output:", output_text, height=400)
                    
            return_code = process.poll()
            if return_code == 0:
                st.success("Script executed successfully!")
            else:
                st.error(f"Script execution failed with return code {return_code}")

# --- ADD QUESTION PAGE ---
elif page == "Add Question":
    st.title("Add New Question")
    
    nom_question = st.text_input("Question Name (no spaces)")
    question_content = st.text_area("Question Content", height=200)
    reponse_cible = st.text_area("Target Answer", height=150)
    infos_cruciales = st.text_area("Crucial Information", height=100)
    infos_a_eviter = st.text_area("Information to Avoid", height=100)
    
    if st.button("Save Question"):
        if not nom_question:
            st.error("Question name is required")
        elif ' ' in nom_question:
            st.error("Question name must not contain spaces")
        else:
            save_question(nom_question, question_content)
            target_data = {
                "reponse_cible": reponse_cible,
                "infos_cruciales": infos_cruciales,
                "infos_a_eviter": infos_a_eviter
            }
            save_target(nom_question,  target_data)
            st.success(f"Question '{nom_question}' saved successfully!")
            # Clear the form
            st.rerun()

# --- VIEW QUESTIONS PAGE ---
elif page == "View Questions":
    st.title("View Questions")
    
    question_files = os.listdir('./questions')
    questions = []
    
    for filename in question_files:
        if filename.endswith('.q'):
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
    
    if not questions:
        st.info("No questions found. Add some questions first.")
    else:
        for q in questions:
            with st.expander(f"{q['nom_question']} - {q['first_paragraph'][:100]}..."):
                st.subheader("Question Content")
                st.write(q['question_content'])
                
                if q['target_data']:
                    st.subheader("Target Answer")
                    st.write(q['target_data'].get('reponse_cible', 'No target answer provided'))
                    
                    st.subheader("Crucial Information")
                    st.write(q['target_data'].get('infos_cruciales', 'No crucial information provided'))
                    
                    st.subheader("Information to Avoid")
                    st.write(q['target_data'].get('infos_a_eviter', 'No information to avoid provided'))

# --- EDIT QUESTIONS PAGE ---
elif page == "Edit Questions":
    st.title("Edit Questions")
    
    question_files = [f[:-2] for f in os.listdir('./questions') if f.endswith('.q')]
    question_files.sort()
    
    if not question_files:
        st.info("No questions found. Add some questions first.")
    else:
        selected_question = st.selectbox("Select a question to edit", question_files)
        
        if selected_question:
            question_content = load_question(selected_question)
            target_data = load_target(selected_question) or {}
            
            new_question_content = st.text_area("Question Content", value=question_content, height=200)
            new_reponse_cible = st.text_area("Target Answer", value=target_data.get('reponse_cible', ''), height=150)
            new_infos_cruciales = st.text_area("Crucial Information", value=target_data.get('infos_cruciales', ''), height=100)
            new_infos_a_eviter = st.text_area("Information to Avoid", value=target_data.get('infos_a_eviter', ''), height=100)
            
            if st.button("Save Changes"):
                save_question(selected_question, new_question_content)
                new_target_data = {
                    "reponse_cible": new_reponse_cible,
                    "infos_cruciales": new_infos_cruciales,
                    "infos_a_eviter": new_infos_a_eviter
                }
                save_target(selected_question, new_target_data)
                st.success(f"Question '{selected_question}' updated successfully!")

# --- DELETE QUESTIONS PAGE ---
elif page == "Delete Questions":
    st.title("Delete Questions")
    
    question_files = [f[:-2] for f in os.listdir('./questions') if f.endswith('.q')]
    question_files.sort()
    
    if not question_files:
        st.info("No questions found. Add some questions first.")
    else:
        selected_questions = st.multiselect("Select questions to delete", question_files)
        
        if selected_questions:
            if st.button("Delete Selected Questions", type="primary", help="This action cannot be undone!"):
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
                
                st.success(f"Deleted {len(selected_questions)} question(s) successfully!")
                st.experimental_rerun()

# --- SELECT QUESTIONS PAGE ---
elif page == "Select Questions":
    st.title("Select Questions for Analysis")
    
    question_files = [f[:-2] for f in os.listdir('./questions') if f.endswith('.q')]
    question_files.sort()
    
    if not question_files:
        st.info("No questions found. Add some questions first.")
    else:
        selected_questions = load_selected_questions()
        new_selected_questions = st.multiselect(
            "Select questions for analysis",
            question_files,
            default=selected_questions
        )
        
        if st.button("Save Selection"):
            save_selected_questions(new_selected_questions)
            st.success(f"Selected {len(new_selected_questions)} question(s) for analysis!")

# --- MANUAL ENTRY PAGE ---
elif page == "Manual Entry":
    st.title("Manual Answer Entry")
    
    questions = list_questions()
    questions.sort()
    
    if not questions:
        st.info("No questions found. Add some questions first.")
    else:
        question_name = st.selectbox("Select Question", questions)
        source = st.text_input("Source/Model Name", help="Enter the name of the model or source providing this answer")
        
        if question_name:
            question_content = load_question(question_name)
            st.subheader("Question Content")
            st.write(question_content)
        
        answer_content = st.text_area("Answer Content", height=300)
        
        if st.button("Save Answer"):
            if not source:
                st.error("Source name is required")
            elif not answer_content:
                st.error("Answer content is required")
            else:
                save_manual_answer(question_name, answer_content, source)
                st.success(f"Answer from '{source}' for question '{question_name}' saved successfully!")
                # Clear form
                st.rerun()
# --- MODELS PAGE ---
elif page == "Models":
    st.title("Select Models for Analysis")
    
    # Test connection first
    connection_status = test_connection()
    if connection_status.get('status') == 'error':
        st.error(f"Connection error: {connection_status.get('message')}")
        st.info("Please check your configuration in the Configuration page.")
    else:
        with st.spinner("Fetching models..."):
            models = fetch_models()
        
        if not models:
            st.warning("No models found or connection failed.")
        else:
            # Organize models by provider
            providers = {
                'Ollama - Offline': [],
                'Anthropic': [],
                'Google': [],
                'OpenAI': [],
                'Mistral': [],
                'Perplexity': [],
                'Other': []
            }
            
            for model in models:
                model_name = model['name'].lower()
                if 'google' in model_name or 'gemini' in model_name:
                    providers['Google'].append(model)
                elif 'anthropic' in model_name or 'claude' in model_name:
                    providers['Anthropic'].append(model)
                elif 'perplexity' in model_name:
                    providers['Perplexity'].append(model)
                elif model.get('model_type') == 'OpenAI':
                    providers['OpenAI'].append(model)
                elif model.get('model_type') == 'Ollama':
                    providers['Ollama - Offline'].append(model)
                elif 'mistral' in model_name or model.get('model_type') == 'Mistral':
                    providers['Mistral'].append(model)
                else:
                    providers['Other'].append(model)
            
            # Load currently selected models
            selected_models = load_selected_models()
            all_model_ids = [model['id'] for model in models]
            
            # Create tabs for each provider
            provider_tabs = st.tabs(list(providers.keys()))
            
            # Dictionary to store selected models from each tab
            tab_selections = {}
            
            # Dictionary to store model names for display
            model_id_to_name = {model['id']: model['name'] for model in models}
            
            for i, (provider, provider_models) in enumerate(providers.items()):
                with provider_tabs[i]:
                    if not provider_models:
                        st.info(f"No {provider} models available.")
                    else:
                        # Create a DataFrame for better display
                        model_data = []
                        for model in provider_models:
                            model_data.append({
                                'ID': model['id'],
                                'Name': model['name'],
                                'Family': model.get('details', {}).get('family', 'Unknown'),
                                'Parameters': model.get('details', {}).get('parameter_size', 'Unknown'),
                                'Selected': model['id'] in selected_models
                            })
                        
                        df = pd.DataFrame(model_data)
                        
                        # Use an editable data grid for selection
                        edited_df = st.data_editor(
                            df,
                            column_config={
                                "Selected": st.column_config.CheckboxColumn(
                                    "Select",
                                    help="Select this model for analysis",
                                    default=False,
                                )
                            },
                            hide_index=True,
                            use_container_width=True
                        )
                        
                        # Store selections for this tab
                        tab_selections[provider] = [
                            row['ID'] for _, row in edited_df.iterrows() if row['Selected']
                        ]
            
            # Display currently selected models from all tabs
            st.divider()
            st.subheader("Currently Selected Models")
            
            # Combine all current selections
            current_selections = []
            for selections in tab_selections.values():
                current_selections.extend(selections)
            
            # Display in a nice table
            if current_selections:
                selected_data = []
                for model_id in current_selections:
                    # Find the provider for this model
                    provider = "Unknown"
                    for prov, models_list in providers.items():
                        if any(model['id'] == model_id for model in models_list):
                            provider = prov
                            break
                    
                    selected_data.append({
                        "Model ID": model_id,
                        "Model Name": model_id_to_name.get(model_id, "Unknown"),
                        "Provider": provider
                    })
                
                # Sort by provider and then by name
                selected_data.sort(key=lambda x: (x["Provider"], x["Model Name"]))
                
                # Display as a DataFrame
                st.dataframe(
                    pd.DataFrame(selected_data),
                    use_container_width=True,
                    hide_index=True
                )
                
                # Show count
                st.info(f"Total selected models: {len(current_selections)}")
            else:
                st.info("No models currently selected.")
            
            # Save button
            if st.button("Save Selected Models"):
                save_to_yaml(current_selections)
                st.success(f"Selected {len(current_selections)} model(s) successfully!")
                
                # Display the list of saved models
                if current_selections:
                    st.write("Saved models:")
                    for model_id in current_selections:
                        st.write(f"- {model_id_to_name.get(model_id, model_id)}")

# --- SELECT COMPARATOR PAGE ---
elif page == "Select Comparator":
    st.title("Select Comparator Model")
    
    with st.spinner("Fetching models..."):
        models = fetch_models()
    
    if not models:
        st.warning("No models found or connection failed.")
    else:
        current_config = load_analysis_config()
        selected_model = current_config.get('analysis_model', None)
        
        model_options = [model['id'] for model in models]
        model_options.sort()
        
        new_selected_model = st.selectbox(
            "Select a model for analysis comparison",
            model_options,
            index=model_options.index(selected_model) if selected_model in model_options else 0
        )
        
        if st.button("Save Selection"):
            save_analysis_model(new_selected_model)
            st.success(f"Selected '{new_selected_model}' as the comparator model!")

# --- CONFIGURATION PAGE ---
elif page == "Configuration":
    st.title("Configuration")
    
    config = load_connect_owui(config_file)
    api_key = config.get('open_webui', {}).get('api_key', '')
    location = config.get('open_webui', {}).get('location', '')
    
    new_api_key = st.text_input("API Key", value=api_key, type="password")
    new_location = st.text_input("API Location", value=location)
    
    if st.button("Save Configuration"):
        new_config = {
            'open_webui': {
                'api_key': new_api_key,
                'location': new_location
            }
        }
        save_connect_owui(new_config, config_file)
        st.success("Configuration saved successfully!")
        
        # Test the connection with new settings
        test_result = test_connection()
        if test_result.get('status') == 'success':
            st.success(test_result.get('message'))
        else:
            st.error(test_result.get('message'))
# ANALYSIS
elif page == "View Analysis":
    st.title("View Analysis Results")
    
    # Create analysis directory if it doesn't exist
    analysis_dir = './analysis'
    os.makedirs(analysis_dir, exist_ok=True)
    
    # Define file collections for HTML, MD, and JSON
    html_files = []
    download_files = []

    # Collect files for display/download
    for file in os.listdir(analysis_dir):
        file_path = os.path.join(analysis_dir, file)
        
        if file.endswith('.html'):
            # Add HTML files for viewing
            html_files.append({
                'name': file,
                'path': file_path,
                'modified': os.path.getmtime(file_path),
            })
        
        elif file.endswith(('.md', '.json')):
            # Add Markdown and JSON files for download
            download_files.append({
                'name': file,
                'path': file_path,
                'modified': os.path.getmtime(file_path),
            })
        
    # Sort files 
    html_files.sort(key=lambda x: x['name'], reverse=True)
    download_files.sort(key=lambda x: x['name'], reverse=True)
    
    # Display HTML files with rendering
    if not html_files:
        st.info("No HTML analysis files found.")
    else:
        for file in html_files:
            with st.expander(f"{file['name']} - Last Modified: {datetime.fromtimestamp(file['modified']).strftime('%Y-%m-%d %H:%M:%S')}"):
                with open(file['path'], 'r', encoding='utf-8') as f:
                    html_content = f.read()
                st.components.v1.html(html_content, height=600, scrolling=True)
                st.download_button(
                    label="Download HTML",
                    data=open(file['path'], 'rb').read(),
                    file_name=file['name'],
                    mime='text/html'
                )
    
    # Display available download files (MD and JSON)
    if download_files:
        st.subheader("Available Downloads")
        for file in download_files:
            file_extension = file['name'].split('.')[-1]
            with open(file['path'], 'rb') as f:
                file_bytes = f.read()
            
            st.download_button(
                label=f"Download {file_extension.upper()} - {file['name']}",
                data=file_bytes,
                file_name=file['name'],
                mime=f"text/{file_extension}" if file_extension == 'md' else "application/json"
            )