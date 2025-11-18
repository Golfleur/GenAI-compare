# Two-Stage Answer Refinement Feature

## Overview

This feature allows answers to be refined by a secondary model before analysis, enabling quality improvement and comparison between initial and refined responses.

## How It Works

### 1. Configuration (UI: "Answer Refinement" Page)

Navigate to the "Answer Refinement" page in the Streamlit application to configure:

- **Enable/Disable**: Toggle the refinement feature on or off
- **Refinement Model**: Select which model should perform the refinement
- **Analysis Mode**: Choose to analyze:
  - BOTH initial and refined answers (recommended for comparison)
  - ONLY refined answers (to save on analysis costs)
- **Refinement Prompt**: Customize the prompt used for refinement

### 2. Answer Generation Process

When refinement is enabled, the workflow is:

```
Question → Initial Model → Initial Answer
                              ↓
                    Refinement Prompt with Question + Initial Answer
                              ↓
                    Refinement Model → Refined Answer
```

### 3. Storage

Depending on the "Analyze Both" setting:

**When "Analyze Both" is ENABLED:**
- Initial answer stored as: `"ModelName (initial)"`
- Refined answer stored as: `"ModelName (refined)"`
- Both include metadata about the refinement process

**When "Analyze Both" is DISABLED:**
- Only refined answer stored as: `"ModelName"`
- Initial answer preserved in metadata field

### 4. Analysis and Display

The analysis script (`app-anal.py`) automatically:
- Analyzes all stored answers
- Adds visual badges to distinguish initial vs refined
- Shows which model performed the refinement
- Allows easy comparison when both are analyzed

## Configuration File Format

The refinement configuration is stored in `./config/config.yaml`:

```yaml
selected_models:
  - model-1
  - model-2
analysis_model: analyzer-model
refinement:
  enabled: true                    # Enable/disable refinement
  model: refiner-model             # Model to use for refinement
  analyze_both: true               # Analyze both initial and refined
  prompt_template: |               # Template for refinement prompt
    Please review and refine the following answer to improve its accuracy, clarity, and completeness:
    
    Original Question: {question}
    
    Initial Answer: {initial_answer}
    
    Please provide a refined version of this answer.
```

## Example Output

### Answer File (`answers/question1.a`)

```json
{
  "gpt-4 (initial)": {
    "choices": [{
      "message": {
        "content": "This is the initial answer..."
      }
    }],
    "created": 1700000000,
    "refinement_metadata": {
      "is_initial": true,
      "has_refined_version": true,
      "refinement_model": "claude-3-opus"
    }
  },
  "gpt-4 (refined)": {
    "choices": [{
      "message": {
        "content": "This is the refined and improved answer..."
      }
    }],
    "created": 1700000001,
    "refinement_metadata": {
      "initial_answer": "This is the initial answer...",
      "refinement_model": "claude-3-opus",
      "was_refined": true,
      "is_refined_version": true
    }
  }
}
```

### Analysis Display (HTML)

Initial answers display with a **blue badge**: "Initial Answer"
Refined answers display with a **green badge**: "Refined Answer"

Additional metadata shows which model performed the refinement.

## Benefits

### 1. Quality Improvement
- Leverage powerful models to refine answers from other models
- Improve accuracy, clarity, and completeness

### 2. Comparison Capability
- See the direct impact of refinement
- Measure improvement from initial to refined
- Evaluate refinement model effectiveness

### 3. Transparency
- Initial answers preserved for audit trail
- Clear indication of which answers were refined
- Metadata tracks the refinement process

### 4. Flexibility
- Can be enabled/disabled per comparison run
- Choose to analyze both or only refined
- Customize refinement prompts
- Select any available model for refinement

## Best Practices

### 1. Refinement Model Selection
- Use a powerful model (e.g., GPT-4, Claude) for refinement
- Can be the same or different from initial models
- Consider cost vs. quality tradeoffs

### 2. When to Enable "Analyze Both"
**Enable when:**
- You want to measure refinement effectiveness
- Comparing initial vs refined performance is important
- Budget allows for additional analysis

**Disable when:**
- Only final quality matters
- Budget constraints limit analysis calls
- Initial answers not needed for your use case

### 3. Prompt Template Customization
- Include both `{question}` and `{initial_answer}` placeholders
- Provide clear instructions to the refinement model
- Consider your domain-specific requirements
- Test different prompts to optimize results

### 4. Cost Considerations
- Refinement doubles API calls for answer generation
- "Analyze Both" doubles analysis calls
- Total cost with both enabled: 4x baseline
- Consider selective use for important questions

## Troubleshooting

### Refinement Not Working
1. Check that refinement is enabled in configuration
2. Verify refinement model is selected
3. Ensure API credentials are valid
4. Check logs for error messages

### Only Refined Answers Showing
- This is expected when "Analyze Both" is disabled
- Initial answers are still in metadata
- Re-run with "Analyze Both" enabled to see both

### Missing Badges in Analysis
- Ensure you're using the updated app-anal.py
- Check that answers have refinement_metadata
- Verify HTML output is being generated correctly

## Migration Guide

### Existing Data
- Feature is backward compatible
- Existing answers without refinement work normally
- No migration needed for old data

### Enabling for Existing Projects
1. Update to latest code
2. Navigate to "Answer Refinement" page
3. Configure as desired
4. Re-run comparisons to generate refined answers
5. Old and new data will coexist

## Technical Details

### Files Modified
- `app-compare.py`: Answer generation with refinement logic
- `app-setup-questions.py`: UI configuration page
- `app-anal.py`: Enhanced display with badges
- `README.md`: Updated documentation

### Key Functions
- `load_refinement_config()`: Load refinement settings
- `refine_answer()`: Apply refinement to an answer
- `save_refinement_config()`: Save user configuration

### Metadata Structure
```python
{
  "is_initial": bool,              # True if this is initial answer
  "is_refined_version": bool,      # True if this is refined answer
  "was_refined": bool,             # True if refinement succeeded
  "refinement_attempted": bool,    # True if refinement was tried
  "refinement_model": str,         # Name of refinement model
  "has_refined_version": bool,     # True if refined version exists
  "initial_answer": str            # Original answer text (in refined version)
}
```

## Future Enhancements

Potential improvements for future versions:
- Multiple refinement stages (3-stage, 4-stage, etc.)
- Different refinement strategies per question
- A/B testing of different refinement prompts
- Automatic selection of best refinement model
- Batch refinement optimization
- Refinement quality metrics
