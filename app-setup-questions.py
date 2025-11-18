import streamlit as st
import json
import os
import yaml
import requests
import subprocess
from datetime import datetime
from pathlib import Path
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(
    page_title="GenAI Performance Comparator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

CONFIG_PATH = './config/config.yaml'
config_file = './config/connect-owui.yaml'

os.makedirs('./questions', exist_ok=True)
os.makedirs('./targets', exist_ok=True)
os.makedirs('./answers', exist_ok=True)
os.makedirs('./config', exist_ok=True)
if not os.path.exists(config_file):
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump({'configs': []}, f)

if 'show_new_config_form' not in st.session_state:
    st.session_state.show_new_config_form = False

def load_all_configs(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            config_data = yaml.safe_load(file)
            if isinstance(config_data, dict) and 'configs' in config_data:
                configs = config_data.get('configs', [])
                return [c for c in configs if isinstance(c, dict)]
            else:
                print(f"Config data doesn't have expected structure: {config_data}")
                return []
    except (FileNotFoundError, yaml.YAMLError) as e:
        print(f"Error loading configs: {e}")
        return []

all_configs = load_all_configs(config_file)
config_names = []
if all_configs:
    for c in all_configs:
        if isinstance(c, dict):
            config_names.append(c.get('name', 'Unnamed Config'))
        else:
            config_names.append(f"Invalid config: {str(c)[:20]}")
current_config_index = 0
config = all_configs[current_config_index] if all_configs else {}

API_KEY = config.get('open_webui', {}).get('api_key', '')
BASE_URL = config.get('open_webui', {}).get('location', '')
API_URL = f"{BASE_URL}/api/models" if BASE_URL else ""

def save_all_configs(configs, file_path):
    """Save configurations preserving active flags"""
    with open(file_path, 'w', encoding='utf-8') as file:
        yaml.dump({'configs': configs}, file)

def initialize_session_state():
    """Initialize session state variables if they don't exist"""
    if 'selected_config_name' not in st.session_state:
        all_configs = load_all_configs(config_file)
        config_names = [c.get('name', f'Unnamed Config {i}') for i, c in enumerate(all_configs)] if all_configs else []
        st.session_state.selected_config_name = config_names[0] if config_names else None
        
initialize_session_state()

def get_current_config():
    """Get the currently selected configuration"""
    all_configs = load_all_configs(config_file)
    if not all_configs:
        return {}
    selected_name = st.session_state.selected_config_name
    for config in all_configs:
        if config.get('name') == selected_name:
            return config
    return all_configs[0] if all_configs else {}
    
def get_api_credentials():
    config = get_current_config()
    api_key = config.get('open_webui', {}).get('api_key', '')
    base_url = config.get('open_webui', {}).get('location', '')
    return api_key, base_url

# --- Question Management Functions ---
def save_question(nom_question, question_content):
    question_path = f'./questions/{nom_question}.q'
    with open(question_path, 'w', encoding="utf-8") as file:
        file.write(question_content)

def load_question(nom_question):
    question_path = f'./questions/{nom_question}.q'
    if os.path.exists(question_path):
        with open(question_path, 'r', encoding="utf-8") as file:
            return file.read()
    return None

def save_target(nom_question, target_data):
    target_path = f'./targets/{nom_question}.t'
    with open(target_path, 'w', encoding="utf-8") as file:
        json.dump(target_data, file, indent=4)

def load_target(nom_question):
    target_path = f'./targets/{nom_question}.t'
    if os.path.exists(target_path):
        with open(target_path, 'r', encoding="utf-8") as file:
            return json.load(file)
    return None

def save_question_metadata(nom_question, metadata):
    """Save metadata for a question in a separate file"""
    metadata_dir = './questions_metadata'
    os.makedirs(metadata_dir, exist_ok=True)
    metadata_path = f'{metadata_dir}/{nom_question}.meta'
    with open(metadata_path, 'w', encoding="utf-8") as file:
        json.dump(metadata, file, indent=4)

def load_question_metadata(nom_question):
    """Load metadata for a question"""
    metadata_dir = './questions_metadata'
    os.makedirs(metadata_dir, exist_ok=True) 
    metadata_path = f'{metadata_dir}/{nom_question}.meta'
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r', encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError: # Return default if file is corrupted
            return {"category": "Uncategorized"}
    return {"category": "Uncategorized"} 

def get_all_categories():
    metadata_dir = './questions_metadata'
    os.makedirs(metadata_dir, exist_ok=True)
    categories = set(["Uncategorized"])  # Default 
    if os.path.exists(metadata_dir):
        for filename in os.listdir(metadata_dir):
            if filename.endswith('.meta'):
                filepath = os.path.join(metadata_dir, filename)
                try:
                    with open(filepath, 'r', encoding="utf-8") as file:
                        metadata = json.load(file)
                        if metadata and isinstance(metadata, dict) and 'category' in metadata and metadata['category']:
                            categories.add(metadata['category'])
                except (json.JSONDecodeError, FileNotFoundError):
                    pass
    return sorted(list(categories))

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
    try:
        API_KEY, BASE_URL = get_api_credentials()
        if not API_KEY or not BASE_URL:
            if not local:
                return {'status': 'error', 'message': 'API key and location are required.'}
            return False
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
    API_KEY, BASE_URL = get_api_credentials()
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
    current_config = {}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r', encoding="utf-8") as file:
            try:
                current_config = yaml.safe_load(file) or {}
            except yaml.YAMLError:
                print("Error reading YAML configuration")
    current_config['selected_models'] = selected_models
    with open(CONFIG_PATH, 'w', encoding="utf-8") as file:
        yaml.dump(current_config, file)

# Sidebar navigation
st.sidebar.title("Navigation")
if st.session_state.selected_config_name:
    st.sidebar.info(f"Active Config: {st.session_state.selected_config_name}")
else:
    st.sidebar.warning("No configuration selected")

page = st.sidebar.radio(
    "Choose a page",
    ["Perform comparison", "Add Question", "View Questions", "Edit Questions", "Delete Questions",
     "Select Questions", "Manage Question Categories", "Manual Entry", "Models", "Select Comparator", "Configuration", "View Analysis","Manage Analysis Files"]
)
# --- HOME PAGE ---
if page == "Perform comparison":
    st.title("Performance Analyser for Generative AI models ")
    st.write("Use the sidebar to navigate.\n\nFirst, make sure to enter your Configuration\n\nYou must also setup at least one question\n\nThen, select which Models are to be compared and select a Comparator model that will perform the analysis of the answers")
    current_config = st.session_state.selected_config_name
    st.info(f"Using configuration: {current_config}" if current_config else "No configuration selected")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Run Comparison")
        if st.button("Run Compare Script", key="run_compare"):
            st.info("Running comparison script...")
            output_placeholder = st.empty()

            command = ["python", "-u", "app-compare.py", "--verbose"]
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            output_text = ""
            while True:
                output_line = process.stdout.readline()
                if output_line == '' and process.poll() is not None:
                    break
                if output_line:
                    output_text += output_line
                    output_placeholder.text_area("Output:", output_text, height=800, key=f"output_{hash(output_text)}")           
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

            command = ["python", "-u", "app-anal.py", "--verbose"]
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            output_text = ""
            while True:
                output_line = process.stdout.readline()
                if output_line == '' and process.poll() is not None:
                    break
                if output_line:
                    output_text += output_line
                    output_placeholder.text_area("Output:", output_text, height=800, key=f"output_{hash(output_text)}")           
            return_code = process.poll()
            if return_code == 0:
                st.success("Script executed successfully!")
            else:
                st.error(f"Script execution failed with return code {return_code}")

# --- ADD QUESTION PAGE ---
elif page == "Add Question":
    st.title("Add New Question")

    nom_question = st.text_input("Question Name (no spaces)")
    existing_categories = get_all_categories()

    col1, col2 = st.columns([3, 1])
    with col1:
        category_type = st.radio("Category Selection", ["Choose Existing", "Add New"], horizontal=True)
        if category_type == "Choose Existing":
            category = st.selectbox("Select Category", existing_categories)
        else:
            category = st.text_input("New Category Name")

    with col2:
        st.write("Existing Categories:")
        for cat in existing_categories:
            st.write(f"- {cat}")

    question_content = st.text_area("Question Content", height=200)
    reponse_cible = st.text_area("Target Answer", height=150)
    infos_cruciales = st.text_area("Crucial Information", height=100)
    infos_a_eviter = st.text_area("Information to Avoid", height=100)

    if st.button("Save Question"):
        if not nom_question:
            st.error("Question name is required")
        elif ' ' in nom_question:
            st.error("Question name must not contain spaces")
        elif category_type == "Add New" and not category:
            st.error("New category name is required")
        else:
            save_question(nom_question, question_content)
            target_data = {
                "reponse_cible": reponse_cible,
                "infos_cruciales": infos_cruciales,
                "infos_a_eviter": infos_a_eviter
            }
            save_target(nom_question,  target_data)
            save_question_metadata(nom_question, {"category": category})
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
            metadata = load_question_metadata(nom_question)
            first_paragraph = question_content.split('\n')[0] if question_content else ''

            questions.append({
                'nom_question': nom_question,
                'question_content': question_content,
                'target_data': target_data,
                'first_paragraph': first_paragraph,
                'category': metadata.get("category", "Uncategorized")
            })

    questions.sort(key=lambda x: x['nom_question'].lower())

    if not questions:
        st.info("No questions found. Add some questions first.")
    else:
        all_categories = sorted(list(set([q['category'] for q in questions])))
        selected_category = st.selectbox("Filter by category", ["All"] + all_categories)

        filtered_questions = questions
        if selected_category != "All":
            filtered_questions = [q for q in questions if q['category'] == selected_category]

        for q in filtered_questions:
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
    question_files.sort(key=str.lower)
    if not question_files:
        st.info("No questions found. Add some questions first.")
    else:
        selected_question = st.selectbox("Select a question to edit", question_files)
        if selected_question:
            question_content = load_question(selected_question)
            target_data = load_target(selected_question) or {}
            metadata = load_question_metadata(selected_question)
            current_category = metadata.get('category', 'Uncategorized')
            existing_categories = get_all_categories()

            if current_category not in existing_categories:
                existing_categories.append(current_category)
                existing_categories.sort()

            col1, col2 = st.columns([3, 1])
            with col1:
                category_type = st.radio("Category Selection", ["Choose Existing", "Add New"], horizontal=True)
                if category_type == "Choose Existing":
                    new_category = st.selectbox("Select Category", existing_categories, 
                                              index=existing_categories.index(current_category))
                else:
                    new_category = st.text_input("New Category Name")
            with col2:
                st.write("Existing Categories:")
                for cat in existing_categories:
                    st.write(f"- {cat}")

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
                save_question_metadata(selected_question, {"category": new_category})   
                st.success(f"Question '{selected_question}' updated successfully!")

# --- DELETE QUESTIONS PAGE ---
elif page == "Delete Questions":
    st.title("Delete Questions")

    question_files = [f[:-2] for f in os.listdir('./questions') if f.endswith('.q')]
    question_files.sort(key=str.lower)
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
                st.rerun()

# --- SELECT QUESTIONS PAGE ---
elif page == "Select Questions":
    st.title("Select Questions for Analysis")
    all_categories = get_all_categories()

    question_files = [f[:-2] for f in os.listdir('./questions') if f.endswith('.q')]
    question_files.sort(key=str.lower)
    question_categories = {}
    for qname in question_files:
        metadata = load_question_metadata(qname)
        question_categories[qname] = metadata.get("category", "Uncategorized")

    if not question_files:
        st.info("No questions found. Add some questions first.")
    else:
        selected_category = st.selectbox("Filter by category", ["All"] + all_categories)
        filtered_questions = question_files
        if selected_category != "All":
            filtered_questions = [q for q in question_files if question_categories.get(q) == selected_category]
        selected_questions = load_selected_questions()
        valid_selected_questions = [q for q in selected_questions if q in question_files]
        new_selected_questions = st.multiselect(
            "Select questions for analysis",
            filtered_questions,
            default=valid_selected_questions,
            format_func=lambda q: f"{q} [{question_categories.get(q)}]"
        )
        if st.button("Save Selection"):
            save_selected_questions(new_selected_questions)
            st.success(f"Selected {len(new_selected_questions)} question(s) for analysis!")

# --- MANAGE QUESTION CATEGORIES PAGE
elif page == "Manage Question Categories":
    st.title("Manage Question Categories")
    all_categories = get_all_categories()
    st.subheader("Current Categories")
    for cat in all_categories:
        st.write(f"- {cat}")
    st.divider()
    st.subheader("Add New Category")
    new_category = st.text_input("New category name")
    if st.button("Add Category"):
        if not new_category:
            st.error("Category name is required")
        elif new_category in all_categories:
            st.error(f"Category '{new_category}' already exists")
        else:
            metadata_dir = './questions_metadata'
            os.makedirs(metadata_dir, exist_ok=True)
            placeholder_id = f"category_placeholder_{new_category.lower().replace(' ', '_')}"
            placeholder_path = os.path.join(metadata_dir, f"{placeholder_id}.meta")
            placeholder_metadata = {
                "id": placeholder_id,
                "category": new_category,
                "difficulty": "medium",
                "created": datetime.now().isoformat(),
                "is_placeholder": True  # Flag to identify this as a category placeholder
            }
            with open(placeholder_path, 'w', encoding="utf-8") as file:
                json.dump(placeholder_metadata, file, indent=4)
            st.success(f"Added new category: '{new_category}'")
            st.rerun()  # Refresh to show updated categories
    st.divider()

    st.subheader("Rename Category")
    old_category = st.selectbox("Select category to rename", all_categories)
    new_category_name = st.text_input("New category name", key="rename_category")
    if st.button("Rename Category"):
        if not new_category_name:
            st.error("New category name is required")
        elif new_category_name in all_categories:
            st.error(f"Category '{new_category_name}' already exists")
        else:
            metadata_dir = './questions_metadata'
            renamed_count = 0
            for filename in os.listdir(metadata_dir):
                if filename.endswith('.meta'):
                    filepath = os.path.join(metadata_dir, filename)
                    try:
                        with open(filepath, 'r', encoding="utf-8") as file:
                            metadata = json.load(file)
                        if metadata.get("category") == old_category:
                            metadata["category"] = new_category_name
                            with open(filepath, 'w', encoding="utf-8") as file:
                                json.dump(metadata, file, indent=4)
                            renamed_count += 1
                    except (json.JSONDecodeError, FileNotFoundError):
                        pass
            st.success(f"Renamed category '{old_category}' to '{new_category_name}' for {renamed_count} questions")
            st.rerun()  # Refresh to show updated categories
    st.divider()
    st.subheader("Merge Categories")
    categories_to_merge = st.multiselect("Select categories to merge", all_categories)
    target_category = st.selectbox("Target category (all selected will be merged into this)",
                                  all_categories if all_categories else [""],
                                  disabled=not categories_to_merge)
    if st.button("Merge Categories"):
        if not categories_to_merge:
            st.error("Please select at least one category to merge")
        elif target_category not in categories_to_merge:
            st.error("Target category must be one of the selected categories")
        else:
            metadata_dir = './questions_metadata'
            merged_count = 0
            for filename in os.listdir(metadata_dir):
                if filename.endswith('.meta'):
                    filepath = os.path.join(metadata_dir, filename)
                    try:
                        with open(filepath, 'r', encoding="utf-8") as file:
                            metadata = json.load(file)
                        if metadata.get("category") in categories_to_merge and metadata.get("category") != target_category:
                            metadata["category"] = target_category
                            with open(filepath, 'w', encoding="utf-8") as file:
                                json.dump(metadata, file, indent=4)
                            merged_count += 1
                    except (json.JSONDecodeError, FileNotFoundError):
                        pass
            st.success(f"Merged {len(categories_to_merge)-1} categories into '{target_category}', affecting {merged_count} questions")
            st.rerun()
    st.divider()
    st.subheader("Delete Category")
    category_to_delete = st.selectbox("Select category to delete", all_categories)
    replacement_category = st.selectbox("Move questions to category",
                                       [c for c in all_categories if c != category_to_delete],
                                       disabled=len(all_categories) <= 1)
    if st.button("Delete Category"):
        if len(all_categories) <= 1:
            st.error("Cannot delete the only category")
        else:
            metadata_dir = './questions_metadata'
            moved_count = 0
            for filename in os.listdir(metadata_dir):
                if filename.endswith('.meta'):
                    filepath = os.path.join(metadata_dir, filename)
                    try:
                        with open(filepath, 'r', encoding="utf-8") as file:
                            metadata = json.load(file)
                        if metadata.get("category") == category_to_delete:
                            metadata["category"] = replacement_category
                            with open(filepath, 'w', encoding="utf-8") as file:
                                json.dump(metadata, file, indent=4)
                            moved_count += 1
                    except (json.JSONDecodeError, FileNotFoundError):
                        pass
            st.success(f"Deleted category '{category_to_delete}' and moved {moved_count} questions to '{replacement_category}'")
            st.rerun()

# --- MANUAL ENTRY PAGE ---
elif page == "Manual Entry":
    st.title("Manual Answer Entry")
    questions = [f[:-2] for f in os.listdir('./questions') if f.endswith('.q')]
    questions.sort(key=str.lower)

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
            selected_models = load_selected_models()
            all_model_ids = [model['id'] for model in models]
            provider_tabs = st.tabs(list(providers.keys()))
            tab_selections = {}
            model_id_to_name = {model['id']: model['name'] for model in models}
            for i, (provider, provider_models) in enumerate(providers.items()):
                with provider_tabs[i]:
                    if not provider_models:
                        st.info(f"No {provider} models available.")
                    else:
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
                        tab_selections[provider] = [
                            row['ID'] for _, row in edited_df.iterrows() if row['Selected']
                        ]
            st.divider()
            st.subheader("Currently Selected Models")
            current_selections = []
            for selections in tab_selections.values():
                current_selections.extend(selections)
            if current_selections:
                selected_data = []
                for model_id in current_selections:
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
                selected_data.sort(key=lambda x: (x["Provider"], x["Model Name"]))
                st.dataframe(
                    pd.DataFrame(selected_data),
                    use_container_width=True,
                    hide_index=True
                )
                st.info(f"Total selected models: {len(current_selections)}")
            else:
                st.info("No models currently selected.")
            if st.button("Save Selected Models"):
                save_to_yaml(current_selections)
                st.success(f"Selected {len(current_selections)} model(s) successfully!")
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
    all_configs = load_all_configs(config_file)
    config_names = [c['name'] for c in all_configs] if all_configs else []
    if st.button("➕ Add New Configuration"):
        st.session_state.show_new_config_form = True
    if st.session_state.get('show_new_config_form', False):
        st.subheader("Add New Configuration")
        with st.form("new_config_form"):
            new_config_name = st.text_input("Configuration Name")
            new_api_key = st.text_input("API Key", type="password")
            new_location = st.text_input("API Location")
            submit_button = st.form_submit_button("Save New Configuration")
            if submit_button:
                if not new_config_name:
                    st.error("Configuration name is required")
                elif new_config_name in config_names:
                    st.error(f"A configuration named '{new_config_name}' already exists")
                else:
                    new_config = {
                        'name': new_config_name,
                        'active': True,  # Mark as active
                        'open_webui': {
                            'api_key': new_api_key,
                            'location': new_location
                        }
                    }
                    for config in all_configs:
                        config['active'] = False
                    all_configs.append(new_config)
                    save_all_configs(all_configs, config_file)
                    st.session_state.selected_config_name = new_config_name
                    st.session_state.show_new_config_form = False
                    st.success("Configuration added successfully!")
                    st.rerun()
    if config_names:
        st.subheader("Existing Configurations")
        selected_config_name = st.selectbox(
            "Choose Configuration", 
            config_names, 
            index=config_names.index(st.session_state.selected_config_name) if st.session_state.selected_config_name in config_names else 0
        )
        if selected_config_name != st.session_state.selected_config_name:
            st.session_state.selected_config_name = selected_config_name
            for config in all_configs:
                config['active'] = (config.get('name') == selected_config_name)
            save_all_configs(all_configs, config_file)
            st.rerun()
        config = next((c for c in all_configs if c['name'] == selected_config_name), None)
        if config is None:
            st.error("Selected configuration not found.")
        else:
            if 'open_webui' not in config:
                config['open_webui'] = {'api_key': '', 'location': ''}
            api_key = config.get('open_webui', {}).get('api_key', '')
            location = config.get('open_webui', {}).get('location', '')
            with st.form("edit_config_form"):
                st.subheader(f"Edit Configuration: {selected_config_name}")
                new_api_key = st.text_input("API Key", value=api_key, type="password")
                new_location = st.text_input("API Location", value=location)
                col1, col2, col3 = st.columns(3)
                with col1:
                    submit_button = st.form_submit_button("Save Changes")
                with col2:
                    test_button = st.form_submit_button("Test Connection")
                with col3:
                    delete_button = st.form_submit_button("Delete Configuration", type="secondary")
                if test_button:
                    test_result = test_connection()
                    if test_result.get('status') == 'success':
                        st.success(test_result.get('message'))
                    else:
                        st.error(test_result.get('message'))

                if submit_button:
                    if 'open_webui' not in config:
                        config['open_webui'] = {}
                    config['open_webui']['api_key'] = new_api_key
                    config['open_webui']['location'] = new_location
                    for i, cfg in enumerate(all_configs):
                        if cfg.get('name') == selected_config_name:
                            all_configs[i] = config
                            all_configs[i]['active'] = True
                        else:
                            all_configs[i]['active'] = False
                    save_all_configs(all_configs, config_file)
                    st.success("Configuration saved successfully!")
                    test_result = test_connection()
                    if test_result.get('status') == 'success':
                        st.success(test_result.get('message'))
                    else:
                        st.error(test_result.get('message'))
                if delete_button:
                    if len(all_configs) <= 1:
                        st.error("Cannot delete the only configuration. Please add another configuration first.")
                    else:
                        all_configs = [cfg for cfg in all_configs if cfg.get('name') != selected_config_name]
                        if all_configs:
                            all_configs[0]['active'] = True
                            st.session_state.selected_config_name = all_configs[0].get('name')
                        else:
                            st.session_state.selected_config_name = None
                        save_all_configs(all_configs, config_file)
                        st.success(f"Configuration '{selected_config_name}' deleted successfully!")
                        st.rerun()
    else:
        st.info("No configurations available. Please add one.")
        with st.form("initial_config_form"):
            new_config_name = st.text_input("New Configuration Name")
            new_api_key = st.text_input("API Key", type="password")
            new_location = st.text_input("API Location")
            submit_button = st.form_submit_button("Add Configuration")
            if submit_button:
                if not new_config_name:
                    st.error("Configuration name is required")
                else:
                    new_config = {
                        'name': new_config_name,
                        'active': True,  # Mark as active
                        'open_webui': {
                            'api_key': new_api_key,
                            'location': new_location
                        }
                    }
                    all_configs.append(new_config)
                    save_all_configs(all_configs, config_file)
                    st.session_state.selected_config_name = new_config_name
                    st.success("Configuration added successfully!")
                    st.rerun()

# ANALYSIS
elif page == "View Analysis":
    st.title("View Analysis Results")
    analysis_dir = './analysis'
    os.makedirs(analysis_dir, exist_ok=True)
    html_files = []
    download_files = []
    all_analysis_files = []

    for file in os.listdir(analysis_dir):
        file_path = os.path.join(analysis_dir, file)
        if file.endswith('.html'):
            html_files.append({
                'name': file,
                'path': file_path,
                'modified': os.path.getmtime(file_path),
            })
            all_analysis_files.append(file_path)
        elif file.endswith(('.md', '.json')):
            download_files.append({
                'name': file,
                'path': file_path,
                'modified': os.path.getmtime(file_path),
            })
            all_analysis_files.append(file_path)
    html_files.sort(key=lambda x: x['name'], reverse=True)
    download_files.sort(key=lambda x: x['name'], reverse=True)
    all_analysis_files.sort(key=str.lower)

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

elif page == "Manage Analysis Files":
    st.title("Analysis Files Management")
    analysis_dir = './analysis'
    os.makedirs(analysis_dir, exist_ok=True)
    download_files = []
    all_analysis_files = []
    for file in os.listdir(analysis_dir):
        file_path = os.path.join(analysis_dir, file)
        download_files.append({
            'name': file,
            'path': file_path,
            'modified': os.path.getmtime(file_path),
        })
        all_analysis_files.append(file_path)
    download_files.sort(key=lambda x: x['name'], reverse=True)
    all_analysis_files.sort(key=str.lower)
    st.subheader("Delete files")
    all_file_names = [os.path.basename(path) for path in all_analysis_files]
    if all_file_names:
        files_to_delete = st.multiselect("Select files to delete", all_file_names)
        if files_to_delete and st.button("Delete Selected Files", type="primary"):
            deleted_count = 0
            for file_name in files_to_delete:
                file_path = os.path.join(analysis_dir, file_name)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    deleted_count += 1
            st.success(f"Successfully deleted {deleted_count} file(s). Refresh the page to see changes.")
    st.divider()
    st.subheader("Download files")
    num_columns = 4
    columns = st.columns(num_columns)
    for idx, file in enumerate(download_files):
        file_extension = file['name'].split('.')[-1]
        with open(file['path'], 'rb') as f:
            file_bytes = f.read()
        col = columns[idx % num_columns]  # Rotate through columns based on index
        with col:
            st.download_button(
                label=f"{file_extension.upper()} - {file['name']}",
                data=file_bytes,
                file_name=file['name'],
                mime=f"text/{file_extension}" if file_extension == 'md' else "application/json"
            )
