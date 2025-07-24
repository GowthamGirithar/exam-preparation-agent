from llm.llm_factory import get_llm
from langchain.prompts import PromptTemplate
from classifiers.topic_classifier import TopicClassifier
from classifiers.topic_classifier import Topic
from retrievers.vector_store_factory import get_vector_store
from langchain.schema.runnable import RunnableMap
from config import Config




class LawExamAgent:
    '''
    LawExamAgent does the following things.
    
    Classify the question to decide whether to use RAG or pass to LLM without context.

    And call the LLM again with the vector db results to get the answer.
    
    '''
    def __init__(self, llm_provider: str, llm_model: str, llm_host: str):
        # get the specific llm by providing provider , model name and host
        self.llm = get_llm(llm_provider, llm_model, llm_host)

        # assign the classifier
        self.classifier = TopicClassifier(self.llm)

        # vector store for each topic - vector store has collection for each topic
        self.vector_stores = {
            Topic.MICROSERVICE: get_vector_store(provider_name=Config.VECTOR_STORE_PROVIDER,
                                                 embedding_provider=Config.EMBEDDING_PROVIDER,
                                                 embedding_model=Config.DEFAULT_EMBEDDING_MODEL,
                                                 collection_name=Config.MICROSERVICE_COLLECTION),
        }

        # prompt template for each topic
        self.topic_prompts = {
            Topic.MICROSERVICE: PromptTemplate.from_template(
                '''
                You will act as an architect of software engineering and with the context provided answer the question in a 
                 simplest way with an example.

                    context is  {context}

                    and the question is {question}

                '''

            ),

            Topic.LAW: PromptTemplate.from_template(

                '''
                You will act as a legal practisioner and coach to help learn for the CLAT exam for the youngters.

                Your questions and answers should focus on exam and also answer should with simple sentences with details captured in easiest way

                And the question is {question}

                Provide a clear, exam-focused answer with:
                     1. Direct answer to the question
                     2. Relevant legal provisions or concepts
                     3. Examples if applicable
                     4. Exam tips

                Answer:

                '''
            )

        }


    def answer_questions(self, question: str) -> str:

        # classify using the llm
        topic = self.classifier.llm_based_classify(question)

        if topic == Topic.MICROSERVICE:

            # retrive the data from vector db and send it to the prompt and then to llm 
            # Chain using Runnable (RunnableMap + pipe)
            
            retrieval_chain = (
                RunnableMap({
                "context": lambda x: self.vector_stores[Topic.MICROSERVICE].get_chroma_retriever().invoke(x["question"]),
                "question": lambda x: x["question"]
            })
                | self.topic_prompts[Topic.MICROSERVICE]
                | self.llm
            )
            question = {"question": question}
            # using stream to not wait for entire result to be returned
            response = retrieval_chain.stream(question)
            return response

        if topic == Topic.LAW:
            prompt = self.topic_prompts[Topic.LAW]
            chain = prompt | self.llm # runnable -anything takes input and gives output ; promt takes input and format to give it to LLM
            return chain.invoke({"question": question}) #chain invoke will return the final result and so we have to wait
