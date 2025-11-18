# GenAI-compare
Compare the performance of Generative AI models considering a set of pre-vetted questions and answers

run "streamlit run ./app-setup-questions.py"

allows you to:
    - manage one or more configurations of Open-Webui API key and server location (stored in the ./config/connect-owui.yaml file)
    - manage the list of questions (now possible select a subset of questions for comparison, edit questions, delete questions, add answers from external sources...)
    - select the models to be compared
    - select the model that will perform the analysis
    - **configure two-stage answer refinement** (optional feature to improve answer quality)
    - run app-compare.py to gather the answers (you can also run this from the command line)
    - run app-anal.py performs an analysis of the quality of the response from each source compared to the target data (you can also run this from the command line)
    - review the analysis in HTML and download the analysis per question in various formats

## Two-Stage Answer Refinement

The system now supports an optional two-stage answer generation process:

1. **Stage 1 (Initial Answer)**: Each selected model generates an initial answer to the question
2. **Stage 2 (Refinement)**: A refinement model reviews and improves the initial answer
3. **Analysis**: Both the initial and refined answers can be analyzed separately

### Configuration

Navigate to the "Answer Refinement" page in the application to:
- Enable/disable the refinement feature
- Select which model should perform the refinement
- Choose whether to analyze both initial and refined answers, or only the refined version
- Customize the refinement prompt template

### Benefits

- **Quality Improvement**: Allows a more powerful model to refine answers from other models
- **Comparison**: When analyzing both versions, you can see how refinement improves the answers
- **Flexibility**: Can be enabled/disabled per comparison run
- **Transparency**: Initial answers are preserved for audit purposes
