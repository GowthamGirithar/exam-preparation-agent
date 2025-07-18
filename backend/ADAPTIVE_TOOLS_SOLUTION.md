# Adaptive Tools Solution

## Problem Solved
Fixed the LangChain + Ollama tool input parsing issue where entire JSON objects like `{"query": "current issue in Indian law"}` were being passed as the first parameter instead of being parsed properly.

## Solution Overview
Implemented a **simple, clean solution** with environment-controlled schema validation that supports both OpenAI and Ollama models seamlessly.

## Key Components

### 1. Simple Helper Function
```python
def parse_tool_input(raw_input: Any, tool_name: str = "") -> Dict[str, Any]:
    """Simple helper to parse tool input for Ollama models."""
    if not Config.TOOL_SCHEMA_VALIDATION:
        # Ollama mode: parse JSON manually
        if isinstance(raw_input, str) and raw_input.strip().startswith('{'):
            try:
                parsed = json.loads(raw_input.strip())
                return parsed
            except json.JSONDecodeError:
                return {"query": raw_input}
        return {"query": str(raw_input)}
    else:
        # OpenAI mode: input already properly parsed
        return raw_input if isinstance(raw_input, dict) else {"query": str(raw_input)}
```

### 2. Clean Tool Implementation Pattern
```python
@tool("search_web", description="Search the web for current information")
def search_web(query_or_json: str) -> str:
    """Search the web for current information."""
    
    # Parse input based on mode
    if Config.TOOL_SCHEMA_VALIDATION:
        # OpenAI mode: parameter is correctly parsed
        query = query_or_json
    else:
        # Ollama mode: parse JSON manually
        params = parse_tool_input(query_or_json, "search_web")
        query = params.get("query", str(query_or_json))
    
    # Tool implementation...
```

### 3. Environment Configuration
```bash
# For Ollama (default)
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1
TOOL_SCHEMA_VALIDATION=false  # Automatically set by agent factory

# For OpenAI
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
LLM_PROVIDER_API_KEY=sk-your-api-key-here
TOOL_SCHEMA_VALIDATION=true   # Automatically set by agent factory
```

### 4. Universal API Key Support
- Single `LLM_PROVIDER_API_KEY` environment variable for any provider
- Supports OpenAI, Anthropic, and future providers
- Maintains backward compatibility with existing `OPENAI_API_KEY`

### 5. Automatic Mode Detection
The agent factory automatically sets the correct mode:
```python
def get_agent():
    if Config.LLM_PROVIDER == "openai":
        os.environ["TOOL_SCHEMA_VALIDATION"] = "true"
    else:
        os.environ["TOOL_SCHEMA_VALIDATION"] = "false"
    # ... rest of agent creation
```

## Benefits

✅ **Simple & Clean**: Easy to understand and maintain
✅ **Backward Compatible**: Existing Ollama setup works without changes  
✅ **OpenAI Ready**: Seamless integration with proper schema validation
✅ **Universal API Key**: Single configuration for any LLM provider
✅ **Automatic**: No manual configuration needed
✅ **Robust**: Handles malformed JSON and edge cases
✅ **Well Tested**: Comprehensive test coverage

## Usage Examples

### Current Ollama Setup (No Changes Needed)
```python
from agents.agent_factory import get_agent

agent = get_agent()  # Automatically uses Ollama mode
response = agent.answer_questions("What is contract law?", "user_1", "session_1")
```

### OpenAI Integration
```bash
# Set environment variables
export LLM_PROVIDER=openai
export LLM_MODEL=gpt-4
export LLM_PROVIDER_API_KEY=sk-your-openai-api-key-here
```

```python
from agents.agent_factory import get_agent

agent = get_agent()  # Automatically uses OpenAI mode with schema validation
response = agent.answer_questions("What is contract law?", "user_1", "session_1")
```

## Files Modified

1. **`config.py`** - Added `TOOL_SCHEMA_VALIDATION` and `LLM_PROVIDER_API_KEY`
2. **`llm/llm_factory.py`** - Updated to use universal API key
3. **`tools/tools_registry.py`** - Simplified with clean if/else logic in each tool
4. **`agents/agent_factory.py`** - Added automatic mode detection
5. **`.env.example`** - Updated with new configuration options

## Test Results
```
✅ JSON parsing works correctly
✅ Tool creation successful in both modes
✅ Configuration properly loaded
✅ Universal API key system working
✅ Automatic mode detection functioning
```

The solution resolves the original LangChain + Ollama tool input issue while providing a robust foundation for multi-provider LLM support.
