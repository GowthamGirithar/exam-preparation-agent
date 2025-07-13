from langsmith import Client
from config import Config

def get_langsmith_client():
    """Initialize and return LangSmith client for evaluation operations"""
    if not Config.LANGSMITH_API_KEY:
        raise ValueError("LANGSMITH_API_KEY is required for evaluation")
    
    return Client(
        api_key=Config.LANGSMITH_API_KEY,
        api_url=Config.LANGSMITH_API_URL
    )

def create_evaluation_dataset(client: Client, dataset_name: str, examples: list):
    """Create or update a dataset in LangSmith for evaluation"""
    try:
        # Try to get existing dataset
        dataset = client.read_dataset(dataset_name=dataset_name)
        print(f"Using existing dataset: {dataset_name}")
        return dataset
    except:
        # Create new dataset if it doesn't exist
        dataset = client.create_dataset(
            dataset_name=dataset_name,
            description=f"Evaluation dataset for {dataset_name}"
        )
        
        # Add examples to dataset
        # if we have format as per mentioned in create_examples function, then we can just pass examples.
        client.create_examples(
            inputs=[ex["inputs"] for ex in examples],
            outputs=[ex["outputs"] for ex in examples],
            dataset_id=dataset.id
        )
        
        print(f"Created new dataset: {dataset_name} with {len(examples)} examples")
        return dataset
