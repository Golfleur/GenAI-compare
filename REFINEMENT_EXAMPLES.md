# Two-Stage Answer Refinement - Usage Examples

## Example 1: Basic Setup

### Step 1: Enable Refinement
1. Open the application: `streamlit run app-setup-questions.py`
2. Navigate to "Answer Refinement" page
3. Check "Enable two-stage answer refinement"
4. Select refinement model (e.g., "gpt-4o")
5. Check "Analyze both initial and refined answers"
6. Click "Save Refinement Configuration"

### Step 2: Run Comparison
1. Navigate to "Perform comparison" page
2. Click "Run Compare Script"
3. Wait for completion

### Step 3: View Results
1. Navigate to "View Analysis" page
2. Open the latest analysis HTML file
3. You'll see both "(initial)" and "(refined)" versions for each model

## Example 2: Compare Refinement Effectiveness

This example shows how to measure how much refinement improves answers.

### Configuration:
- Initial models: GPT-3.5, Gemini-1.5-Flash (faster, cheaper models)
- Refinement model: GPT-4o (more powerful model)
- Analyze both: Enabled

### Workflow:
```bash
# 1. Configure refinement
# (Use UI as shown in Example 1)

# 2. Run comparison
python app-compare.py --verbose

# 3. Run analysis  
python app-anal.py --verbose

# 4. Review results
# - Check GPT-3.5 (initial) vs GPT-3.5 (refined)
# - Check Gemini-1.5-Flash (initial) vs Gemini-1.5-Flash (refined)
# - Compare improvement scores
```

### Expected Output:
- **GPT-3.5 (initial)**: Score 6/10
- **GPT-3.5 (refined)**: Score 8/10
- **Gemini-1.5-Flash (initial)**: Score 5/10  
- **Gemini-1.5-Flash (refined)**: Score 7/10

**Insight**: Refinement improved scores by 2 points on average!

## Example 3: Cost-Optimized Setup

Use refinement but minimize costs.

### Configuration:
- Enable refinement: Yes
- Refinement model: GPT-4o
- Analyze both: **No** (only refined)

### Why This Works:
- Still get refined answers for analysis
- Don't pay for analyzing initial answers
- Initial answers stored in metadata if needed later
- 50% cost savings on analysis vs. "analyze both"

### Use Case:
Good for production where you only care about final quality, not the comparison.

## Example 4: Custom Refinement Prompt

Tailor the refinement for legal domain.

### Custom Prompt Template:
```
You are a legal expert reviewing an AI-generated answer to a legal question.

Original Question: {question}

Initial Answer: {initial_answer}

Please refine this answer by:
1. Ensuring legal accuracy and citing relevant laws/precedents
2. Improving clarity and professional language
3. Adding important caveats or disclaimers
4. Structuring the answer logically

Provide the refined answer:
```

### Configuration:
1. Navigate to "Answer Refinement"
2. Paste the custom template
3. Ensure `{question}` and `{initial_answer}` are present
4. Save configuration

### Benefit:
Domain-specific refinement produces better results than generic prompts.

## Example 5: Multi-Model Testing

Test different refinement models to find the best one.

### Round 1: GPT-4 as Refiner
```yaml
refinement:
  enabled: true
  model: gpt-4o
  analyze_both: true
```
Run comparison, note scores.

### Round 2: Claude as Refiner  
```yaml
refinement:
  enabled: true
  model: claude-3-opus
  analyze_both: true
```
Run comparison, note scores.

### Round 3: Gemini as Refiner
```yaml
refinement:
  enabled: true
  model: gemini-1.5-pro
  analyze_both: true
```
Run comparison, note scores.

### Analysis:
Compare which refinement model produces the highest quality refined answers.

## Example 6: Selective Refinement

Refine only for specific question types.

### Approach 1: Manual Selection
1. Disable global refinement
2. For important questions, manually enable refinement
3. Run comparison
4. Re-disable for next run

### Approach 2: Multiple Configuration Runs
1. Create subset of critical questions in "Select Questions"
2. Enable refinement
3. Run comparison
4. Create subset of simple questions
5. Disable refinement  
6. Run comparison again

### Use Case:
Save costs by only refining answers to complex or critical questions.

## Example 7: Answer Quality Audit

Use refinement to audit answer quality.

### Scenario:
You suspect your model is giving poor answers to certain questions.

### Process:
1. Enable refinement with a very strong model (GPT-4, Claude-3-Opus)
2. Enable "analyze both"
3. Run comparison
4. Review gap between initial and refined scores

### What to Look For:
- Large gaps (3+ points) indicate initial model struggling
- Consistent patterns of improvement areas
- Questions where refinement helps most

### Action:
- Replace struggling models
- Fine-tune prompts for initial models
- Focus training on weak areas

## Example 8: A/B Testing Refinement Strategies

Test different refinement approaches.

### Strategy A: Single-Stage Refinement
```
Refinement prompt: "Improve this answer for clarity and accuracy."
```

### Strategy B: Multi-Aspect Refinement  
```
Refinement prompt: "Refine by:
1. Improving factual accuracy
2. Enhancing clarity
3. Adding relevant examples
4. Structuring logically
"
```

### Comparison:
Run both strategies on same questions, compare final scores.

## Example 9: Command-Line Workflow

Automated workflow without UI.

### Create config file:
```bash
cat > config/config.yaml << EOF
selected_models:
  - gpt-3.5-turbo
  - gemini-1.5-flash
analysis_model: gpt-4o
refinement:
  enabled: true
  model: gpt-4o
  analyze_both: true
  prompt_template: |
    Please review and refine the following answer:
    
    Question: {question}
    Initial: {initial_answer}
    
    Provide a refined version.
EOF
```

### Run comparison:
```bash
python app-compare.py --verbose > logs/compare.log 2>&1
```

### Run analysis:
```bash
python app-anal.py --verbose > logs/analysis.log 2>&1
```

### View results:
```bash
open analysis/summary_*.html
```

## Example 10: Debugging Refinement Issues

What to do when refinement isn't working as expected.

### Check 1: Verify Configuration
```bash
cat config/config.yaml | grep -A 10 refinement
```

Expected output:
```yaml
refinement:
  enabled: true
  model: gpt-4o
  analyze_both: true
  prompt_template: ...
```

### Check 2: Examine Answer File
```bash
cat answers/question1.a | python -m json.tool | grep -A 5 refinement_metadata
```

Expected output:
```json
"refinement_metadata": {
  "is_initial": true,
  "has_refined_version": true,
  "refinement_model": "gpt-4o"
}
```

### Check 3: Review Logs
```bash
python app-compare.py --verbose 2>&1 | grep -i refin
```

Look for:
- "Refinement enabled: True"
- "Applying refinement for question..."
- "Successfully refined answer..."

### Common Issues:
1. **No "(refined)" answers**: Check if refinement is enabled
2. **Error in logs**: Verify API credentials and model availability
3. **Only refined, no initial**: "Analyze both" is disabled (may be intentional)
4. **Identical initial/refined**: Refinement model may not be working properly

## Best Practices Summary

1. **Start Simple**: Enable refinement with default settings first
2. **Test Small**: Try on 1-2 questions before full run
3. **Monitor Costs**: Track API usage, especially with "analyze both"
4. **Customize Gradually**: Start with default prompt, refine based on results
5. **Compare Systematically**: Use "analyze both" to measure improvement
6. **Document Findings**: Keep notes on what works best for your domain
7. **Iterate**: Continuously improve refinement strategy based on results

## Getting Help

If you encounter issues:
1. Check `REFINEMENT_FEATURE.md` for detailed documentation
2. Review logs with `--verbose` flag
3. Verify configuration in `config/config.yaml`
4. Test with a single question first
5. Check that refinement model is accessible via API
