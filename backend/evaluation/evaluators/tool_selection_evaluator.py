import re
from typing import Dict, Any
from langsmith.evaluation import run_evaluator

@run_evaluator
def tool_selection_evaluator(run, example) -> Dict[str, Any]:
    """
    Evaluates whether the agent selected the correct tool for the given question.
    
    Args:
        run: The agent's execution run containing intermediate steps
        example: The test example with expected tool selection
    
    Returns:
        Dict containing score and reasoning
    """
    try:
        # Get expected tool from example
        expected_tool = example.outputs.get("expected_tool")
        if not expected_tool:
            return {
                "key": "tool_selection_accuracy",
                "score": 0,
                "reason": "No expected tool specified in example"
            }
        
        # Extract tools used from intermediate steps
        tools_used = []
        if hasattr(run, 'outputs') and run.outputs:
            # Check if intermediate_steps exists in outputs
            intermediate_steps = run.outputs.get('intermediate_steps', [])
            
            for step in intermediate_steps:
                if isinstance(step, tuple) and len(step) >= 2:
                    action = step[0]
                    if hasattr(action, 'tool'):
                        tools_used.append(action.tool)
                    elif hasattr(action, 'log'):
                        # Extract tool name from log using regex
                        tool_match = re.search(r'Action:\s*(\w+)', action.log)
                        if tool_match:
                            tools_used.append(tool_match.group(1))
        
        # Check if expected tool was used
        tool_used_correctly = expected_tool in tools_used
        
        # Calculate score
        score = 1.0 if tool_used_correctly else 0.0
        
        # Provide reasoning
        if tool_used_correctly:
            reason = f"Correctly used {expected_tool} tool"
        else:
            reason = f"Expected {expected_tool}, but used {tools_used if tools_used else 'no tools detected'}"
        
        return {
            "key": "tool_selection_accuracy",
            "score": score,
            "reason": reason
        }
        
    except Exception as e:
        return {
            "key": "tool_selection_accuracy",
            "score": 0,
            "reason": f"Error evaluating tool selection: {str(e)}"
        }
