# GenAI-compare
Compare the performance of Generative AI models considering a set of pre-vetted questions and answers

- Insert your Open-Webui API key and server location in the ./config/connect-oweui.yaml file
- run app-setup-questions.py; allows you to:
    - manage the list of questions (now possible select a subset of questions for comparison, edit questions, delete questions, add answers from external sources...)
    - select the models to be compared
    - select the model that will perform the analysis
    - run app-compare.py to gather the answers (you can also run this from the command line)
    - run app-anal.py performs an analysis of the quality of the resposne from each source compared to teh target data  (you can also run this from the command line)
