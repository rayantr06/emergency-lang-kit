# 🚀 ELK Deployment Guide

This guide details how to deploy the **Emergency Lang Kit (ELK)** platform using Docker.

## Prerequisites
- Docker & Docker Compose installed.
- (Optional) Gemini API Key for LLM features.

## Quick Start (Production Mode)

1.  **Set Environment Variables**
    Create a `.env` file in the root directory:
    ```bash
    GEMINI_API_KEY=your_api_key_here
    ```

2.  **Launch the Stack**
    ```bash
    docker-compose up --build -d
    ```

3.  **Access Services**
    - **API Documentation (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
    - **Annotation Dashboard:** [http://localhost:8501](http://localhost:8501)

## Architecture
The platform runs as a microservice ecosystem:
- **`elk-api`**: FastAPI backend handling ASR and LLM inference.
- **`elk-ui`**: Streamlit frontend for human-in-the-loop annotation.

## Development
To run tests locally:
```bash
pip install -r requirements.txt
pytest tests/
```
