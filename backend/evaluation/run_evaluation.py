import json
import asyncio
from typing import Dict, List, Any
from langsmith import Client
from langsmith.evaluation import evaluate
from config import Config
from evaluation.langsmith_setup import get_langsmith_client, create_evaluation_dataset
from evaluation.evaluators.correctness_evaluator import correctness_evaluator, llm_based_correctness_evaluator
from evaluation.evaluators.tool_selection_evaluator import tool_selection_evaluator
from evaluation.evaluators.relevance_evaluator import relevance_evaluator, llm_based_relevance_evaluator
from evaluation.evaluators.memory_evaluator import memory_retention_evaluator, conversation_context_evaluator
from agents.modern_dynamic_law_agent_session_memory import ModernDynamicLawAgentWithSessionMemory


class LawAgentEvaluator:
    """
    Main evaluation class for the ModernDynamicLawAgentWithSessionMemory
    """
    
    def __init__(self):
        # langsmith client 
        self.client = get_langsmith_client()

        # agent which we need to evaluate 
        self.agent = ModernDynamicLawAgentWithSessionMemory(
            llm_provider=Config.LLM_PROVIDER,
            llm_model=Config.LLM_MODEL,
            llm_host=Config.LLM_HOST,
            tools=["english_search_document", "search_web"]
        )
        
        # Define evaluators for different test types
        self.basic_evaluators = [
            correctness_evaluator,
            tool_selection_evaluator,
            relevance_evaluator,
            llm_based_correctness_evaluator,
            llm_based_relevance_evaluator
        ]
        
        self.memory_evaluators = [
            memory_retention_evaluator,
            conversation_context_evaluator
        ]
    
    # dataset for evaluaton
    def load_dataset(self, dataset_path: str) -> Dict[str, Any]:
        """Load evaluation dataset from JSON file"""
        with open(dataset_path, 'r') as f:
            return json.load(f)
    
    def create_agent_wrapper(self):
        """Create a wrapper function for the agent that matches LangSmith's expected interface"""
        # we need this to have signature for experiment 
        #  The target system or experiment(s) to evaluate. Can be a function that takes a dict and returns a dict
        def agent_wrapper(input: Dict[str, Any]) -> Dict[str, Any]:
            question = input.get("question", "")
            user_id = input.get("user_id", "eval_user")
            session_id = input.get("session_id", "eval_session")
            
            try:
                response = self.agent.answer_questions(question, user_id, session_id)
                return response
            except Exception as e:
                return {
                    "output": f"Error: {str(e)}",
                    "error": True
                }
        
        return agent_wrapper
    
    def run_basic_evaluation_using_langsmith(self, dataset_name: str = "basic_qa_evaluation") -> Dict[str, Any]:
        """
        Run basic Q&A evaluation on the agent
        
        Args:
            dataset_name: Name for the evaluation dataset in LangSmith
            
        Returns:
            Evaluation results
        """
        print(f"Starting basic evaluation: {dataset_name}")
        
        # Load dataset
        dataset_data = self.load_dataset("evaluation/datasets/basic_qa_dataset.json")
        
        # Create dataset in LangSmith
        dataset = create_evaluation_dataset(
            self.client, 
            dataset_name, 
            dataset_data["examples"]
        )
        
        # Create agent wrapper
        agent_wrapper = self.create_agent_wrapper()
        
        # Run evaluation using langsmith
        results = evaluate(
            agent_wrapper,
            data=dataset_name,
            evaluators=self.basic_evaluators, # A list of evaluators to run on each example
            experiment_prefix="basic_qa",
            client=self.client
        )
        
        return self.process_results(results, "basic_evaluation")
    
    def run_memory_evaluation_using_langsmith(self, dataset_name: str = "memory_test_evaluation") -> Dict[str, Any]:
        """
        Run memory-specific evaluation on the agent with proper conversation sequence handling
        
        Args:
            dataset_name: Name for the evaluation dataset in LangSmith
            
        Returns:
            Evaluation results
        """
        print(f"Starting memory evaluation: {dataset_name}")
        
        # Load dataset
        dataset_data = self.load_dataset("evaluation/datasets/memory_test_dataset.json")
        
        # Process memory test examples with full conversation context
        processed_examples = []
        conversation_contexts = {}  # Store conversation history for each example
        
        for idx, example in enumerate(dataset_data["examples"]):
            conversation = example["inputs"]["conversation"]
            
            # Store the full conversation for this example
            example_id = f"memory_example_{idx}"
            conversation_contexts[example_id] = conversation
            
            # Create evaluation example with the final question and full context
            final_turn = conversation[-1]
            processed_examples.append({
                "inputs": {
                    **final_turn,
                    "example_id": example_id,  # Reference to full conversation
                    "conversation_length": len(conversation)
                },
                "outputs": example["outputs"]
            })
        
        # Create dataset in LangSmith
        dataset = create_evaluation_dataset(
            self.client, 
            dataset_name, 
            processed_examples
        )
        
        # Create memory agent wrapper that handles full conversation sequences
        def memory_agent_wrapper(inputs: Dict[str, Any]) -> Dict[str, Any]:
            question = inputs.get("question", "")
            user_id = inputs.get("user_id", "memory_eval_user")
            session_id = inputs.get("session_id", "memory_eval_session")
            example_id = inputs.get("example_id", "")
            
            try:
                # Get the full conversation for this example
                if example_id in conversation_contexts:
                    conversation = conversation_contexts[example_id]
                    
                    # Execute the full conversation sequence to build memory
                    for i, turn in enumerate(conversation):
                        turn_question = turn["question"]
                        turn_user_id = turn.get("user_id", user_id)
                        turn_session_id = turn.get("session_id", session_id)
                        
                        # Run each turn to build conversation history
                        response = self.agent.answer_questions(turn_question, turn_user_id, turn_session_id)
                        
                        # Return the final response for evaluation
                        if i == len(conversation) - 1:
                            return response
                    
                    # Fallback if no conversation found
                    return {
                        "output": "Error: No conversation turns found",
                        "error": True
                    }
                else:
                    # Fallback to single question if no conversation context
                    response = self.agent.answer_questions(question, user_id, session_id)
                    return response
                    
            except Exception as e:
                return {
                    "output": f"Error: {str(e)}",
                    "error": True
                }
        
        # Run evaluation with LangSmith evaluators
        results = evaluate(
            memory_agent_wrapper,
            data=dataset_name,
            evaluators=self.memory_evaluators,
            experiment_prefix="memory_test",
            client=self.client
        )
        
        # internal method to process the result as same as custom result
        return self.process_results(results, "memory_evaluation")
    
    def run_full_conversation_memory_local_evaluation_test(self) -> Dict[str, Any]:
        """
        Run a comprehensive memory test with full conversation sequences
        """
        print("Starting full conversation memory test")
        
        # Load memory test dataset
        dataset_data = self.load_dataset("evaluation/datasets/memory_test_dataset.json")
        
        results = []
        
        for example in dataset_data["examples"]:
            conversation = example["inputs"]["conversation"]
            expected_recall = example["outputs"]["expected_memory_recall"]
            
            # Run the full conversation
            session_id = f"memory_test_{len(results)}"
            user_id = "memory_test_user"
            
            conversation_history = []
            
            try:
                # Execute each turn in the conversation
                for i, turn in enumerate(conversation):
                    question = turn["question"]
                    response = self.agent.answer_questions(question, user_id, session_id)
                    
                    conversation_history.append({
                        "question": question,
                        "response": response.get("output", ""),
                        "turn": i + 1
                    })
                
                # Evaluate the final response (memory question)
                final_response = conversation_history[-1]["response"]
                memory_score = self.evaluate_memory_recall(final_response, expected_recall)
                
                results.append({
                    "session_id": session_id,
                    "conversation": conversation_history,
                    "expected_recall": expected_recall,
                    "memory_score": memory_score,
                    "passed": memory_score >= Config.EVALUATION_THRESHOLDS["memory_retention"]
                })
                
            except Exception as e:
                results.append({
                    "session_id": session_id,
                    "error": str(e),
                    "memory_score": 0.0,
                    "passed": False
                })
        
        # Calculate overall statistics
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.get("passed", False))
        average_score = sum(r.get("memory_score", 0) for r in results) / total_tests if total_tests > 0 else 0
        
        return {
            "test_type": "full_conversation_memory",
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "pass_rate": passed_tests / total_tests if total_tests > 0 else 0,
            "average_score": average_score,
            "threshold": Config.EVALUATION_THRESHOLDS["memory_retention"],
            "detailed_results": results
        }
    
    def evaluate_memory_recall(self, agent_output: str, expected_recall: str) -> float:
        """Simple memory recall evaluation"""
        from evaluation.evaluators.memory_evaluator import calculate_memory_recall_score
        return calculate_memory_recall_score(agent_output, expected_recall)
    
    def process_results(self, results: Any, test_type: str) -> Dict[str, Any]:
        """
        Process and summarize evaluation results
        
        Args:
            results: Raw evaluation results from LangSmith
            test_type: Type of evaluation performed
            
        Returns:
            Processed results summary
        """
        # This is a simplified version - actual implementation would depend on LangSmith's result format
        summary = {
            "test_type": test_type,
            "timestamp": str(results),  # Placeholder
            "thresholds": Config.EVALUATION_THRESHOLDS,
            "results_summary": "Evaluation completed - check LangSmith dashboard for detailed results"
        }
        
        return summary
    
    def run_all_evaluations(self) -> Dict[str, Any]:
        """
        Run all evaluation types
        
        Returns:
            Combined results from all evaluations
        """
        print("Starting comprehensive evaluation of ModernDynamicLawAgentWithSessionMemory")
        
        all_results = {}
        
        try:

            if Config.EVALUATION_LOCAL: 
                    # Run memory evaluation locally
                    print("\n=== Running Full Conversation Memory Test ===")
                    all_results["full_conversation_memory"] = self.run_full_conversation_memory_local_evaluation_test()

            else:
                # Run memory evaluation using LangSmith
                print("\n=== Running Memory Evaluation using LangSmith ===")
                all_results["memory_evaluation"] = self.run_memory_evaluation_using_langsmith()

                # Run basic Q&A evaluation
                print("\n=== Running Basic Q&A Evaluation ===")
                all_results["basic_qa"] = self.run_basic_evaluation_using_langsmith()
            
            # Calculate overall summary
            all_results["overall_summary"] = self.calculate_overall_summary(all_results)
            
        except Exception as e:
            all_results["error"] = f"Evaluation failed: {str(e)}"
        
        return all_results
    
    def calculate_overall_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall evaluation summary"""
        summary = {
            "total_evaluations": len([k for k in results.keys() if k != "overall_summary"]),
            "evaluations_completed": [],
            "overall_status": "completed"
        }
        
        for eval_type, result in results.items():
            if eval_type != "overall_summary":
                summary["evaluations_completed"].append({
                    "type": eval_type,
                    "status": "completed" if "error" not in result else "failed"
                })
        
        return summary

def main():
    """Main function to run evaluations"""
    evaluator = LawAgentEvaluator()
    
    # Run all evaluations
    results = evaluator.run_all_evaluations()
    
    # Print summary
    print("\n" + "="*50)
    print("EVALUATION SUMMARY")
    print("="*50)
    
    for eval_type, result in results.items():
        print(f"\n{eval_type.upper()}:")
        if isinstance(result, dict):
            for key, value in result.items():
                if key != "detailed_results":  # Skip detailed results in summary as it is in evaluation_results.json
                    print(f"  {key}: {value}")
        else:
            print(f"  {result}")
    
    # Save results to file
    with open("evaluation_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nDetailed results saved to: evaluation_results.json")
    print("Check LangSmith dashboard for interactive results and traces")

if __name__ == "__main__":
    main()
