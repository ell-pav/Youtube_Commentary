# YouTube AI Comment Generator

An AI-powered application that analyzes YouTube videos, summarizes transcripts, retrieves contextual memory using RAG, and generates validated YouTube comments with sentiment control.

---

# Features

* YouTube transcript extraction
* Transcript summarization with Phi-3
* RAG pipeline with LlamaIndex + FAISS
* Semantic memory retrieval from real YouTube comments dataset
* AI-generated YouTube comments
* Sentiment validation with DistilBERT
* ReAct-style retry loop
* FastAPI backend
* Streamlit frontend
* JWT authentication
* CI/CD with GitHub Actions

---

# Tech Stack

## Backend

* FastAPI
* Ollama
* Phi-3
* DistilBERT
* LlamaIndex
* FAISS
* SentenceTransformers

## Frontend

* Streamlit

## AI / NLP

* Retrieval-Augmented Generation (RAG)
* Embeddings
* Vector Search
* Sentiment Analysis
* Agentic Retry Loop

---

# Architecture

```text
YouTube Video
↓
Transcript Extraction
↓
Cleaning
↓
Chunking
↓
Embeddings
↓
FAISS Vector Store
↓
LlamaIndex Retrieval
↓
Relevant Context Retrieval
↓
Phi3 Summarization
↓
Phi3 Comment Generation
↓
DistilBERT Sentiment Validation
↓
Agent ReAct Loop
↓
Validated YouTube Comment
```

---

# Project Structure

```text
YoutubeComment/
│
├── backend/
│   ├── services/
│   ├── main.py
│
├── frontend/
│   ├── views/
│   ├── app.py
│   ├── auth.py
│
├── data/
│   └── YoutubeCommentsDataSet.csv
│
├── tests/
│
├── .github/
│   └── workflows/
│
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

# Installation

## 1. Clone Repository

```bash
git clone https://github.com/ell-pav/Youtube_Commentary.git

cd Youtube_Commentary
```

---

## 2. Create Virtual Environment

```bash
python -m venv .venv
```

### Windows

```bash
.venv\Scripts\activate
```

### Linux / Mac

```bash
source .venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Ollama Setup

Install Ollama:

[https://ollama.com](https://ollama.com)

Pull Phi-3 model:

```bash
ollama pull phi3
```

Start Ollama:

```bash
ollama serve
```

---

# Environment Variables

Create a `.env` file:

```env
SECRET_KEY=your_secret_key
ALGORITHM=HS256

ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

---

# Run Backend

```bash
uvicorn backend.main:app --reload
```

Backend URL:

```text
http://localhost:8000
```

Swagger Docs:

```text
http://localhost:8000/docs
```

---

# Run Frontend

```bash
streamlit run frontend/app.py
```

Frontend URL:

```text
http://localhost:8501
```

---

# Docker Setup

## Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## docker-compose.yml

```yaml
version: '3.9'

services:

  backend:
    build: .
    container_name: youtube-backend
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - .:/app

  frontend:
    build: .
    container_name: youtube-frontend
    command: streamlit run frontend/app.py --server.address=0.0.0.0
    ports:
      - "8501:8501"
    env_file:
      - .env
    depends_on:
      - backend
```

---

# Run Docker

```bash
docker compose up --build
```

---

# API Endpoints

## Login

```http
POST /login
```

Returns JWT access token.

---

## Analyze Video

```http
POST /analyze
```

Request:

```json
{
  "url": "https://youtube.com/watch?v=...",
  "sentiment": "positive"
}
```

Response:

```json
{
  "summary": "...",
  "generated_comment": "...",
  "validated": true,
  "attempts": 2
}
```

---

# Testing

Run tests:

```bash
pytest
```

---

# CI/CD

GitHub Actions automatically:

* installs dependencies
* runs pytest
* validates backend

Workflow location:

```text
.github/workflows/tests.yml
```

---

# RAG Pipeline

The system uses:

* FAISS vector database
* SentenceTransformer embeddings
* LlamaIndex retrieval
* YouTube comments dataset memory

The retrieved comments help guide realistic comment generation.

---

# Security

* JWT authentication
* Environment variables with `.env`
* GitHub Secrets for CI/CD
* OAuth2 password flow

---

# Future Improvements

* Multi-user authentication
* Persistent vector database
* Dockerized Ollama service
* Toxicity filtering
* Better memory ranking
* Kubernetes deployment
* Async inference

---

# Author

Elliot Pavone

---

# License

MIT License
