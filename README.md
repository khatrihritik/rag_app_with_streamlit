
# RAG Application with Streamlit Interface

This application is a **Retrieval-Augmented Generation (RAG)** system that uses Qdrant as a vector database for storing and retrieving information. It provides two main components:

1. **Backend API**: Handles the indexing of documents, chatting with data, and streaming chat responses.
2. **Streamlit Frontend**: A user-friendly interface for interacting with the RAG system, uploading documents, and chatting with the assistant.

## Features

- **Document Upload**: Upload `.pdf`, `.txt`, or `.docx` files to be indexed in the Qdrant database.
- **Chat Interface**: Chat with the assistant powered by the indexed data.
- **Streaming Chat**: Chat responses are streamed in real-time, allowing you to see partial results immediately.
- **Customizable Settings**: Choose retrieval modes (dense, sparse, hybrid), set chunks per retrieval, and adjust similarity score thresholds.

## Backend Setup

Before running the Streamlit app, you need to set up the backend system.

### Setting Up Qdrant

To use Qdrant as your vector database, follow these steps:

#### Using Docker

1. Pull the Qdrant Docker image:

```bash
docker pull qdrant/qdrant
```

2. Start Qdrant with the following command:

```bash
docker run -p 6333:6333     -v $(pwd)/path/to/data:/qdrant/storage     qdrant/qdrant
```

Alternatively, you can follow the [Qdrant Installation Guide](https://qdrant.tech/documentation/guides/installation/) for other installation methods.

### Backend Configuration

Create a `.env` file with the following environment variables:

```dotenv
OPENAI_API_KEY=<your openai key>
qdrant_db_path=<path to qdrant db, e.g., http://localhost:6333/>
llm_provider=openai
model=gpt-4o-mini
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=<API key for LangSmith>
LANGSMITH_PROJECT=<name of LangSmith project>
COLLECTION_NAME=<name of the Qdrant collection>
```

### Backend Installation and Running

1. **Create a new Conda environment** (optional but recommended):

```bash
conda create --name rag-app python=3.8
conda activate rag-app
```

2. **Install dependencies**:

```bash
pip install -r requirements.txt
```

3. **Run the backend application**:

```bash
python run.py
```

---

## Streamlit Frontend Setup

The Streamlit application provides an interface for uploading documents, adjusting settings, and interacting with the RAG-powered assistant.

### Streamlit Configuration

Create a `.env` file in the Streamlit directory with the following content:

```dotenv
BACKEND_PATH=<URL of your backend API, e.g., http://localhost:5000>
```

### Streamlit Installation

1. **Create a new Conda environment**:

```bash
conda create --name rag-chatbot python=3.8
conda activate rag-chatbot
```

2. **Install the Streamlit app dependencies**:

```bash
pip install -r streamlit/requirements.txt
```

### Running the Streamlit Application

Once the environment is set up and dependencies are installed, start the Streamlit app:

```bash
streamlit run streamlit/app.py
```

This will launch the app in your web browser, where you can:

- **Upload Documents**: Upload `.pdf`, `.txt`, or `.docx` files to be indexed.
- **Interact with the Chatbot**: Enter queries and chat with the assistant.
- **Streaming Responses**: As the assistant retrieves information, you will see partial results immediately.

### Features of the Streamlit App

#### Sidebar (Document Upload + Settings)
- **File Upload**: Upload a document to index into the RAG system.
- **Username**: Enter a username to associate with the document.
- **Number of Chunks**: Adjust how many chunks should be retrieved in a single query.
- **Retrieval Mode**: Choose between `dense`, `sparse`, or `hybrid` retrieval methods.
- **Score Threshold**: Set a threshold to filter out low-relevance results.

#### Chat Interface
- **Chat History**: Displays the conversation with the assistant.
- **User Input**: Type your query to interact with the assistant.
- **Streaming Responses**: As the assistant retrieves information, you will see partial results immediately.

## Project Structure

```
.
├── app
│   ├── __init__.py
│   ├── main.py
│   ├── routes
│   │   ├── chat_routes.py
│   │   └── __init__.py
│   ├── services
│   │   ├── logger.py
│   │   └── pydantic_models.py
│   └── utils
│       ├── db_utils.py
│       ├── langchain_utils.py
│       ├── prompts.py
│       ├── qdrant_utils.py
│       └── utils.py
├── streamlit
│   ├── app.py              # Main Streamlit app file
│   ├── requirements.txt     # Python dependencies for Streamlit
├── .env                    # Environment variables for backend API
├── requirements.txt         # Backend dependencies
└── run.py                  # Backend application entry point
```

## Troubleshooting

- **API Errors**: Check the backend logs for any errors related to indexing or chat processing.
- **Document Upload Failures**: Ensure the document is in a supported format (.pdf, .txt, .docx).
- **Slow or Incomplete Responses**: Ensure the backend API is running smoothly and check for any issues with the Qdrant database.
