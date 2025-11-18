# GenAI-compare
Compare the performance of Generative AI models considering a set of pre-vetted questions and answers

## Getting Started

run "streamlit run ./app-setup-questions.py"

## Features

allows you to:
    - manage one or more configurations of Open-Webui API key and server location (stored in the ./config/connect-owui.yaml file)
    - manage the list of questions (now possible select a subset of questions for comparison, edit questions, delete questions, add answers from external sources...)
    - select the models to be compared
    - select the model that will perform the analysis
    - run app-compare.py to gather the answers (you can also run this from the command line)
    - run app-anal.py performs an analysis of the quality of the response from each source compared to the target data  (you can also run this from the command line)
    - review the analysis in HTML and download the analysis per question in various formats

## Forking or Mirroring This Repository

Want to create your own copy of this repository or fork it to another GitHub account? See the [FORKING_GUIDE.md](FORKING_GUIDE.md) for detailed instructions on how to:
- Fork this repository to another GitHub account
- Mirror the repository for complete independence
- Keep your fork synchronized with the original repository

