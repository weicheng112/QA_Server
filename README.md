# EchoBase - Knowledge Base Q&A System

A Retrieval-Augmented Generation (RAG) system that answers questions based on a knowledge base of markdown documents. This system uses OpenAI embeddings and ChromaDB as a vector database to provide accurate, context-aware answers.

## Features

- **Document Ingestion**: Automatically processes markdown files, chunks them, and stores embeddings in ChromaDB
- **Semantic Search**: Retrieves the most relevant document chunks for any query
- **Context-Aware Answers**: Generates answers based only on the retrieved context
- **Modern React Frontend**: Interactive chat interface for easy interaction
- **FastAPI Backend**: Efficient API for querying the knowledge base

## Project Structure

```
QA_server/
│
├── docs/                       # Raw markdown documents
│   ├── policy.md               # Company policies
│   ├── labor_rules.md          # Labor rules and regulations
│   └── product_manual.md       # Product usage manuals
│
├── scripts/
│   ├── ingest.py               # Document processing and embedding pipeline
│   └── query.py                # Query and answer generation
│
├── app/
│   └── api.py                  # FastAPI backend for the chatbot
│
├── frontend/                   # React frontend for the chatbot
│   ├── public/                 # Public assets
│   │   └── index.html          # Main HTML file
│   ├── src/                    # React source code
│   │   ├── App.js              # Main React component
│   │   ├── App.css             # Component styles
│   │   ├── index.js            # React entry point
│   │   └── index.css           # Global styles
│   └── package.json            # npm configuration
│
├── chroma_store/               # Local persistent vector DB (via ChromaDB)
│
├── .env                        # Environment variables and configuration
├── requirements.txt            # Project dependencies
└── README.md                   # Project documentation
```

## Getting Started

### Prerequisites

- Python 3.8 or higher
- OpenAI API key

### Installation

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Set up your environment variables by editing the `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

### Usage

#### 1. Ingest Documents

Process your markdown documents and store them in the vector database:

```bash
python scripts/ingest.py --docs_dir ./docs --db_path ./chroma_store
```

Options:

- `--docs_dir`: Directory containing markdown files (default: `./docs`)
- `--db_path`: Directory to store ChromaDB (default: `./chroma_store`)

#### 2. Query from Command Line

Ask questions directly from the command line:

```bash
python scripts/query.py "What are the labor rules regarding overtime?" --show_context
```

Options:

- `--db_path`: ChromaDB directory (default: `./chroma_store`)
- `--model`: OpenAI model to use (default: `gpt-3.5-turbo`)
- `--top_k`: Number of context chunks to retrieve (default: `5`)
- `--show_context`: Show the context used for the answer
- `--output`: Save result to a JSON file

#### 3. Launch EchoBase Chatbot (React + FastAPI)

The EchoBase chatbot provides a chat interface for interacting with your knowledge base.

Step 1: Start the FastAPI backend:

```bash
# Navigate to your project directory
cd QA_server

# Start the FastAPI backend
python -m uvicorn app.api:app --host 0.0.0.0 --port 8000
```

Step 2: Start the React frontend:

```bash
# In a new terminal, navigate to the frontend directory
cd QA_server/frontend

# Install dependencies (first time only)
npm install

# Start the development server
npm start
```

The React app will automatically open in your browser at `http://localhost:3000`

## Customization

### Adding Documents

1. Add your markdown files to the `docs/` directory
2. Run the ingestion script to process the new documents
3. Query the updated knowledge base

### Changing Models

You can modify the embedding and completion models in the `.env` file:

- `DEFAULT_EMBEDDING_MODEL`: Model used for generating embeddings
- `DEFAULT_COMPLETION_MODEL`: Model used for generating answers

### EchoBase Chatbot Configuration

#### CORS Configuration

The FastAPI backend is configured to allow cross-origin requests from any origin. In production, you should restrict this to specific origins for security reasons. You can modify the CORS configuration in `app/api.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Restrict to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### API Endpoint

The React frontend is configured to connect to the FastAPI backend at `http://localhost:8000/api/query`. If you change the backend URL or port, you'll need to update this in `frontend/src/App.js`.

## Testing

The project includes test suites for the core functionality:

### Running Tests

```bash

# Run specific test files
python -m unittest tests/test_ingest.py

# See the chunking output
python tests/test_chunk_metadata.py
```

### Adding Tests

When extending the system with new features, add corresponding tests to ensure functionality works as expected.

## How It Works

### Document Processing Pipeline

1. **Document Processing**:
   - Markdown files are loaded and preprocessed
   - Text is split into chunks based on their header
   - Each chunk is embedded using OpenAI's embedding model
   - Embeddings and metadata are stored in ChromaDB

### Query Processing

2. **Query Processing**:
   - User query is embedded using the same embedding model
   - Vector similarity search finds the most relevant chunks
   - Retrieved chunks are formatted into a context
   - Context and query are sent to OpenAI's completion model
   - Generated answer is returned to the user

### EchoBase Chatbot Architecture

3. **FastAPI Backend**:

   - Provides a RESTful API endpoint for querying the knowledge base
   - Handles request validation and error handling
   - Processes queries using the same pipeline as the command-line tool
   - Returns structured JSON responses

4. **React Frontend**:
   - Provides a modern chat interface for user interaction
   - Sends queries to the FastAPI backend
   - Displays responses with appropriate formatting
   - Provides model selection options

## Acknowledgements

- OpenAI for providing the embedding and completion models
- ChromaDB for the vector database
- FastAPI for the backend API framework
- React for the frontend user interface
