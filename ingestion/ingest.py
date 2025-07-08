from retrievers.vector_store_factory import get_vector_store
import os


class DataIngestor:
    
    def __init__(self, directory_path: str, vector_store: str, embedding_provider: str, embedding_model: str):
        self.directory_path = directory_path
        self.chroma_retriever = get_vector_store(vector_store, embedding_provider, embedding_model)


    def ingest_data(self):
        for filename in os.listdir(self.directory):
            file_path = os.path.join(self.directory_path, filename)
            if os.path.isfile(file_path):
                 try : 
                    self.chroma_retriever.add_pdf_documents(file_path)
                 except Exception as e:
                    print(f"Error in data ingestion of filename {{filename}} and error is {{e}}")
                 
                

    
    