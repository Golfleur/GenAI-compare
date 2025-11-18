# GenAI-compare
Compare the performance of Generative AI models considering a set of pre-vetted questions and answers

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure your API credentials (choose one method):

### Method 1: Environment Variables (Recommended for Security)
Create a `.env` file in the project root (use `.env.example` as a template):
```bash
cp .env.example .env
```

Edit `.env` and add your credentials:
```
OPENWEBUI_API_KEY=sk-your-api-key-here
OPENWEBUI_BASE_URL=https://your-openwebui-instance.com
```

**Note:** The `.env` file is already in `.gitignore` and will not be committed to version control.

### Method 2: Configuration File
Alternatively, you can manage configurations through the Streamlit UI (stored in `./config/connect-owui.yaml`).

**Security Note:** Environment variables take precedence over configuration files. Using environment variables is more secure and follows best practices.

3. Run the application:
```bash
streamlit run ./app-setup-questions.py
```

## Features

The application allows you to:
- **Secure credential management** via environment variables or YAML configuration files
- Manage one or more configurations of Open-Webui API key and server location
- Manage the list of questions (select subsets for comparison, edit, delete, add answers from external sources)
- Select the models to be compared
- Select the model that will perform the analysis
- Run `app-compare.py` to gather the answers (CLI or UI)
- Run `app-anal.py` to perform quality analysis of responses compared to target data (CLI or UI)
- Review the analysis in HTML and download results in various formats

## Command Line Usage

You can also run the comparison and analysis scripts directly:

```bash
# Run comparison (uses environment variables if set, otherwise falls back to config file)
python app-compare.py --verbose

# Run analysis
python app-anal.py --verbose
```

## Security Best Practices

- Always use environment variables for sensitive credentials in production
- Never commit `.env` files or API keys to version control
- The `.env.example` file is provided as a template - copy it to `.env` and fill in your values
- Keep your API keys secure and rotate them regularly

