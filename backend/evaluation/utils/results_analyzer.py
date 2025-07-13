import json
from typing import Dict, List, Any
from datetime import datetime
from langsmith import Client
from config import Config

class LangSmithResultsAnalyzer:
    """
    Utility class to fetch and analyze results from LangSmith API
    """
    
    def __init__(self):
        self.client = Client(
            api_key=Config.LANGSMITH_API_KEY,
            api_url=Config.LANGSMITH_API_URL
        )
    
    def get_experiment_results(self, experiment_name: str) -> Dict[str, Any]:
        """
        Fetch experiment results from LangSmith
        
        Args:
            experiment_name: Name of the experiment to fetch
            
        Returns:
            Experiment results from LangSmith
        """
        try:
            # Get experiment by name
            experiments = list(self.client.list_experiments(
                experiment_name_contains=experiment_name
            ))
            
            if not experiments:
                return {"error": f"No experiment found with name containing '{experiment_name}'"}
            
            # Get the most recent experiment
            latest_experiment = experiments[0]
            
            # Get runs for this experiment
            runs = list(self.client.list_runs(
                experiment_id=latest_experiment.id
            ))
            
            return {
                "experiment_id": str(latest_experiment.id),
                "experiment_name": latest_experiment.name,
                "created_at": latest_experiment.created_at.isoformat() if latest_experiment.created_at else None,
                "total_runs": len(runs),
                "runs": [self._format_run(run) for run in runs[:10]]  # Limit to first 10 for summary
            }
            
        except Exception as e:
            return {"error": f"Failed to fetch experiment results: {str(e)}"}
    
    def _format_run(self, run) -> Dict[str, Any]:
        """Format a single run for display"""
        return {
            "run_id": str(run.id),
            "status": run.status,
            "start_time": run.start_time.isoformat() if run.start_time else None,
            "end_time": run.end_time.isoformat() if run.end_time else None,
            "inputs": run.inputs,
            "outputs": run.outputs,
            "error": run.error
        }
    
    def get_evaluation_summary(self, project_name: str = None) -> Dict[str, Any]:
        """
        Get evaluation summary from LangSmith project
        
        Args:
            project_name: Name of the project (defaults to config value)
            
        Returns:
            Summary of evaluations
        """
        if not project_name:
            project_name = Config.LANGSMITH_PROJECT
        
        try:
            # Get recent experiments for the project
            experiments = list(self.client.list_experiments(
                limit=10
            ))
            
            summary = {
                "project_name": project_name,
                "total_experiments": len(experiments),
                "recent_experiments": []
            }
            
            for exp in experiments:
                exp_summary = {
                    "name": exp.name,
                    "id": str(exp.id),
                    "created_at": exp.created_at.isoformat() if exp.created_at else None,
                    "description": exp.description
                }
                summary["recent_experiments"].append(exp_summary)
            
            return summary
            
        except Exception as e:
            return {"error": f"Failed to get evaluation summary: {str(e)}"}
    
    def get_dataset_info(self, dataset_name: str) -> Dict[str, Any]:
        """
        Get information about a dataset from LangSmith
        
        Args:
            dataset_name: Name of the dataset
            
        Returns:
            Dataset information
        """
        try:
            dataset = self.client.read_dataset(dataset_name=dataset_name)
            
            # Get examples count
            examples = list(self.client.list_examples(dataset_id=dataset.id, limit=1))
            
            return {
                "dataset_id": str(dataset.id),
                "name": dataset.name,
                "description": dataset.description,
                "created_at": dataset.created_at.isoformat() if dataset.created_at else None,
                "example_count": len(examples)
            }
            
        except Exception as e:
            return {"error": f"Failed to get dataset info: {str(e)}"}
    
    def print_evaluation_summary(self) -> None:
        """Print a formatted evaluation summary"""
        print("="*60)
        print("LANGSMITH EVALUATION SUMMARY")
        print("="*60)
        
        # Get project summary
        summary = self.get_evaluation_summary()
        
        if "error" in summary:
            print(f"Error: {summary['error']}")
            return
        
        print(f"Project: {summary['project_name']}")
        print(f"Total Experiments: {summary['total_experiments']}")
        print()
        
        print("Recent Experiments:")
        for exp in summary["recent_experiments"][:5]:
            print(f"  - {exp['name']} (ID: {exp['id'][:8]}...)")
            print(f"    Created: {exp['created_at']}")
            if exp['description']:
                print(f"    Description: {exp['description']}")
            print()
        
        print("="*60)
        print("To view detailed results, visit:")
        print(f"https://smith.langchain.com/projects/{summary['project_name']}")
        print("="*60)

def main():
    """Main function to display LangSmith results"""
    analyzer = LangSmithResultsAnalyzer()
    
    # Print evaluation summary
    analyzer.print_evaluation_summary()
    
    # Get specific experiment results if available
    print("\nFetching recent experiment results...")
    
    # Try to get basic_qa experiment results
    basic_qa_results = analyzer.get_experiment_results("basic_qa")
    if "error" not in basic_qa_results:
        print(f"\nBasic Q&A Experiment:")
        print(f"  Total Runs: {basic_qa_results['total_runs']}")
        print(f"  Experiment ID: {basic_qa_results['experiment_id']}")
    
    # Try to get memory test experiment results
    memory_results = analyzer.get_experiment_results("memory_test")
    if "error" not in memory_results:
        print(f"\nMemory Test Experiment:")
        print(f"  Total Runs: {memory_results['total_runs']}")
        print(f"  Experiment ID: {memory_results['experiment_id']}")

if __name__ == "__main__":
    main()
