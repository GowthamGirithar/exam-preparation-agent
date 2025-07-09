from .embeddings import get_embedding_provider
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import  TokenTextSplitter, RecursiveCharacterTextSplitter




class ChromaRetriever:

    def __init__(self, embedding_provider: str, embedding_model: str, collection_name="default", persist_dir="./chroma_db"):
        self.embedding = get_embedding_provider(embedding_provider, embedding_model)
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.vectors_store=Chroma(persist_directory=self.persist_dir, embedding_function=self.embedding, collection_name=self.collection_name)

    def add_pdf_documents(self, fullpath: str)-> Exception:

        # Load PDF
        loader = PyPDFLoader(fullpath)
        pages = loader.load() #pages is a list of LangChain Document objects, one per page.

        # Split text into chunks
        # chunk size is tried now, later we can change depends on type of data
        # chunk overlap is To maintain context across chunks.
        # we have charcater splitter
        splitter = TokenTextSplitter(chunk_size=256, chunk_overlap=50)
        documents = splitter.split_documents(pages)

        for doc in documents:
            print(doc.page_content)
            print(doc.metadata) # metadata will be formed automatically with author, title, page and total pages , etc..,
            print(end="\n")
            print("------------------")


        # Add documents after embedding to Chroma
        try :
            self.vectors_store.add_documents(documents=documents)
            print("document is embedded and persisted into chroma db")
        except :
            print("Error in storing the document into chroma db")
            raise Exception("Error in storing the document into chroma db")
        
        

    def get_chroma_retriever(self, top_k=3) :
        return self.vectors_store.as_retriever(search_kwargs= {"k": top_k})
