from retrievers.chroma_retrievers import ChromaRetriever


def test_chroma_add_and_query():
    print(" Starting test")
    chroma_vector_instance =ChromaRetriever(embedding_provider="sentence_transformers", embedding_model="all-MiniLM-L6-v2")
    print(" add to doc")
    chroma_vector_instance.add_pdf_documents("/Users/g.srirangasamy/Downloads/Monolith-to-Microservices.pdf")
    print("read from pdf")
    out= chroma_vector_instance.get_chroma_retriever().invoke("ownership in microservices")
    print("hello here is the output",out)



