# Law Exam Agent Evaluation System

This directory contains the evaluation framework for the ModernDynamicLawAgentWithSessionMemory using LangSmith.

## Overview

The evaluation system provides comprehensive testing of:
- **Correctness**: How accurate are the agent's answers?
- **Tool Selection**: Does the agent choose the right tool for each question type?
- **Relevance**: Are responses relevant to the questions asked?
- **Memory Retention**: Can the agent remember previous conversation context?
- **Conversation Context**: Does the agent maintain proper conversation flow?

## Directory Structure

```
evaluation/
├── datasets/
│   ├── basic_qa_dataset.json          # Basic Q&A test cases
│   └── memory_test_dataset.json       # Memory functionality tests
├── evaluators/
│   ├── correctness_evaluator.py       # Answer correctness evaluation
│   ├── tool_selection_evaluator.py    # Tool selection accuracy
│   ├── relevance_evaluator.py         # Response relevance scoring
│   └── memory_evaluator.py            # Memory retention testing
├── utils/
│   └── results_analyzer.py            # LangSmith results analysis
├── langsmith_setup.py                 # LangSmith client configuration
├── run_evaluation.py                  # Main evaluation runner
└── README.md                          # This file
```

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# LangSmith Configuration
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=law-exam-agent-evaluation
LANGSMITH_API_URL=https://api.smith.langchain.com

# Evaluation Thresholds (optional - defaults provided)
CORRECTNESS_THRESHOLD=0.75
TOOL_SELECTION_THRESHOLD=0.90
RELEVANCE_THRESHOLD=0.80
COMPLETENESS_THRESHOLD=0.70
MEMORY_RETENTION_THRESHOLD=0.85
```

### Agent Configuration

Ensure your agent is configured in `config.py`:

```bash
AGENT_NAME=ModernDynamicLawAgentWithSessionMemory
```

## Running Evaluations

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Full Evaluation Suite

```bash
cd backend
python -m evaluation.run_evaluation
```

### 3. Run Specific Evaluations

```python
from evaluation.run_evaluation import LawAgentEvaluator

evaluator = LawAgentEvaluator()

# Run only basic Q&A evaluation
basic_results = evaluator.run_basic_evaluation()

# Run only memory evaluation
memory_results = evaluator.run_full_conversation_memory_test()
```

### 4. Analyze Results

```bash
# View results summary from LangSmith
python -m evaluation.utils.results_analyzer
```

## Test Datasets

### Basic Q&A Dataset

Contains 13 test cases covering:
- **English Grammar** (5 questions): Past tense, sentence structure, vocabulary
- **Current Affairs** (8 questions): Presidents, capitals, recent events

Expected tool usage:
- English questions → `english_search_document`
- Current affairs → `search_web`

### Memory Test Dataset

Contains 5 conversation sequences testing:
- Single question recall
- Multi-turn conversation memory
- Context-specific memory queries

## Evaluators

### 1. Correctness Evaluator
- **String-based**: Keyword matching and similarity scoring
- **LLM-based**: Uses LLM to evaluate semantic correctness

### 2. Tool Selection Evaluator
- Checks if the agent used the expected tool
- Extracts tool usage from intermediate steps
- Scores: 1.0 (correct) or 0.0 (incorrect)

### 3. Relevance Evaluator
- **Rule-based**: Keyword overlap and question type matching
- **LLM-based**: Uses LLM to judge relevance

### 4. Memory Evaluator
- **Memory Retention**: Can the agent recall previous questions?
- **Conversation Context**: Does it maintain conversation awareness?

## Evaluation Thresholds

Default performance thresholds:

| Metric | Threshold | Description |
|--------|-----------|-------------|
| Correctness | 75% | Realistic for complex CLAT questions |
| Tool Selection | 90% | Should be high (rule-based logic) |
| Relevance | 80% | Responses should be on-topic |
| Completeness | 70% | CLAT answers can be concise |
| Memory Retention | 85% | Session memory should work reliably |

## LangSmith Integration

### Automatic Tracing
- All agent interactions are automatically traced
- View detailed execution steps in LangSmith dashboard

### Datasets
- Test datasets are automatically uploaded to LangSmith
- Reusable across multiple evaluation runs

### Experiments
- Each evaluation run creates a new experiment
- Compare performance across different runs
- Track improvements over time

### Dashboard Access
Visit your LangSmith project dashboard:
```
https://smith.langchain.com/projects/law-exam-agent-evaluation
```

## Interpreting Results

### Memory Test Results
```json
{
  "test_type": "full_conversation_memory",
  "total_tests": 5,
  "passed_tests": 4,
  "pass_rate": 0.8,
  "average_score": 0.82,
  "threshold": 0.85
}
```

- **Pass Rate**: Percentage of tests that met the threshold
- **Average Score**: Mean score across all tests
- **Threshold**: Minimum score required to pass

### LangSmith Metrics
- **Correctness**: View in LangSmith experiments tab
- **Tool Selection**: Check evaluation feedback in runs
- **Relevance**: LLM-based scoring in evaluation results
- **Latency**: Response time metrics in traces

## Troubleshooting

### Common Issues

1. **LangSmith API Key Error**
   ```
   ValueError: LANGSMITH_API_KEY is required for evaluation
   ```
   Solution: Add your LangSmith API key to `.env`

2. **Agent Import Error**
   ```
   ModuleNotFoundError: No module named 'agents'
   ```
   Solution: Run from `backend/` directory

3. **Memory Test Failures**
   - Check session memory configuration
   - Verify `get_session_history` function
   - Ensure proper user_id/session_id handling

4. **Tool Selection Failures**
   - Review agent prompt template
   - Check tool descriptions and selection logic
   - Verify intermediate steps are captured

### Debug Mode

Enable verbose logging:
```bash
export VERBOSE_MODE=true
python -m evaluation.run_evaluation
```

## Extending the Evaluation System

### Adding New Test Cases

1. **Basic Q&A**: Add to `datasets/basic_qa_dataset.json`
2. **Memory Tests**: Add to `datasets/memory_test_dataset.json`

### Creating Custom Evaluators

```python
from langsmith.evaluation import evaluator

@evaluator
def custom_evaluator(run, example):
    # Your evaluation logic here
    return {
        "key": "custom_metric",
        "score": 0.85,
        "reason": "Evaluation explanation"
    }
```

### Adding New Metrics

1. Create evaluator in `evaluators/`
2. Add to evaluator lists in `run_evaluation.py`
3. Update thresholds in `config.py`

## Best Practices

1. **Regular Evaluation**: Run weekly/monthly to track performance
2. **Baseline Establishment**: Record initial performance metrics
3. **Incremental Testing**: Add new test cases based on real user interactions
4. **Performance Monitoring**: Track response times and error rates
5. **Threshold Tuning**: Adjust thresholds based on production requirements

## Support

For issues or questions:
1. Check LangSmith documentation: https://docs.smith.langchain.com/
2. Review agent implementation in `agents/modern_dynamic_law_agent_session_memory.py`
3. Examine evaluation traces in LangSmith dashboard
