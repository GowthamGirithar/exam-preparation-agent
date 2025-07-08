from enum import Enum
from llm.llm_factory import get_llm
from langchain.prompts import PromptTemplate
from langchain_core.language_models.llms import BaseLLM





class Topic(Enum):
    MICROSERVICE = "microservice"
    LAW = "law"


class TopicClassifier:
    def __init__(self, llm: BaseLLM):
        self.llm = llm
        self.classification_prompt_template = PromptTemplate.from_template(
            '''
            You are a classification expert. And Classify the following question into the categories listed below:

            1. microservice = Any question related to microservices in software engineering
            2. law = Any questions about the current affaire, legal proceedings, legal questions, citations.

            Question: "{question}"
            
            Respond with ONLY the category name (e.g., "microservice", "law").

            '''
        )

    def llm_based_classify(self, question: str) -> Topic:
         """Advanced classification using LLM."""
         try:
             chain = self.classification_prompt_template | self.llm #we do not need to format prompt
             response = chain.invoke({"question": question})
             # Parse LLM response
             result_text = response.strip().lower()
             for topic in Topic:
                    if topic.value in result_text:
                        return topic


             return Topic.LAW

         except Exception as e:
             print("LLM classification failed")
             raise e