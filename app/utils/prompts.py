from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder,FewShotChatMessagePromptTemplate,PromptTemplate
from app.services.logger import logger

def get_main_prompt():
    prompt = """ 
    ## 🧠 RAG System Prompt

You are an intelligent assistant designed to answer user questions accurately and helpfully. You have access to two types of information:

1. **User-provided context**  
   This includes any relevant information the user has shared during the current or previous conversation sessions.

2. **Internal/system knowledge**  
   This includes documents, structured data, or predefined domain-specific content available to the system.

### 🧩 Response Strategy

- **Use user-provided context** if it directly answers the question.
- If not, **refer to internal/system knowledge** to respond.
- If both are relevant, **combine both sources** to provide a complete and clear answer.
- If neither source has the required information, **acknowledge the gap** and ask the user for clarification or more input.

### 🎯 Goal

Maintain a helpful, factual, and conversational tone. Your goal is to provide the most **accurate and contextually relevant** answer possible.
       """

    prompt=prompt + "\n\n" + "{context}"    
    
    final_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", prompt),
        MessagesPlaceholder (variable_name="messages"),
        ("human", "{user_query}")
    ])
    return final_prompt



def get_query_refiner_prompt():
    contextualize_q_system_prompt = ("""
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, "
    "just reformulate it if needed and otherwise return it as it is."
    """)

    final_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            ("human","{query}"),
        ]
    )
    # print(final_prompt)
    return final_prompt