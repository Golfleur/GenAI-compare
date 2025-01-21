# GenAI-compare
Compare the performance of Generative AI models considering a set of pre-vetted questions

- Insert your Open-Webui API key in the ./config/connect-oweui.yaml file
- run app-config.py first to select the models to be compared
- run app-setup-questions.py to manage the list of questions (now possible select a subset of questions for comparison)
- app-compare.py will gather the answers
- run app-select-comparator.py to select the model that will perform the analysis
- app-anal.py will perform actual analysis - to be impproved
