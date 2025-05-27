# AI Shopping Assistant

**An chatbot for shopping assistant accepting text message and image upload.**

**Try it out: [Link](https://main.d38zzsxdrba2b0.amplifyapp.com)**

### Preface:
It’s been a very educational journey for me.
1. I was shocked by how good Cursor has become. “Vibing engineer” is real!
2. I started to understand some of the challenges in ML engineering — especially the gap LLMs face due to the lack of private data and realtime data. More fundementally, I feel the existing data management solutions aren't working for LLM (Vector Database doesn't seem to be a right solution) It’s a fascinating problem.
3. when the program became non-deterministic, how to verify its behavior or goodness?


### CUJs 
- **Text Chat**: Ask about any product and get personalized recommendations
- **Image Upload**: Upload a product image to start a coverasation
- **New Chat**: Create a new conversation

## System Architecture

```
                              ┌──────────┐
                              │   User   │
                              └────┬─────┘
                                   │
                                   │ HTTPS
                                   │
                              ┌────┴─────┐
                              │   AWS    │
                              │ Amplify  │
                              └────┬─────┘
                                   │
                                   │ HTTPS
                                   │
                              ┌────┴─────┐
                              │   AWS    │
                              │CloudFront│
                              └────┬─────┘
                                   │
                                   │ HTTP
                                   │
                         ┌─────────┴──────────┐
                         │  Elastic Beanstalk │
                         │  (FastAPI Backend) │
                         └─────────┬──────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
             ┌──────────┐                   ┌──────────┐
             │  OpenAI  │                   │  Serper  │
             │  GPT-4   │                   │  Search  │
             └──────────┘                   └──────────┘
                 Chat                          Product
              Responses                        Search
```

## Backend Request Flow

```
┌──────────┐                ┌───────────────┐
│ Frontend │                │FastAPI Backend│
└────┬─────┘                └───────┬───────┘
     │                              │
     │ User Input                   │
     │ ───────────────────────────> │ 
     │                              │   Analyze input and detect 3 major scenario: 
     |                              |   A. search ready 
     |                              |   B. More info needed to be collected
     |                              |   C. restart coveration as user shows dissatification or topic switch.
     │                              │  ┌────────────┐
     │         Response(B/C)        │  │   OpenAI   │
     │ <─────────────────────────── │  │   GPT-4    │
     │                              │  └─────┬──────┘
     │                              │        │
     │                              │    1. generate Search Query (A)
     │                              │        │
     │                              │        ▼
     │                              │  ┌────────────┐
     │                              │  │   Serper   │
     │                              │  │   Search   │
     │                              │  └─────┬──────┘
     │                              │        │
     │                              │    2. Get Product
     │                              │    Search Results
     │                              │        │
     │                              │        ▼
     │                              │  ┌────────────┐
     │                              │  │   OpenAI   │
     │                              │  │   GPT-4    │
     │                              │  └─────┬──────┘
     │                              │        │
     │                              │    3. Generate
     │                              │    Final Response
     │                              │        │
     │         Response             │        │
     │ ◄──────────────────────────────────────
     │                              │
```


## Architecture

### Backend (FastAPI + Python)
- Built with FastAPI and Python 3.11
  - **Why:** FastAPI is lightweight which is more proper for quick hack comparing to django or Flask 
- Deployed on AWS Elastic Beanstalk
- Dependencies:
  - OpenAI GPT integration for natural language understanding and image analysis
    - **Why:** Most popular one. I should have tried other LLMs if I got more time.
  - Google Search API integration for product search
    - **Why:** Providing large dataset and rich search filtering. 
  - Langchain for history management
    - **Why:** Seems to be suitable for LLM application building comparing to MCP in this project. The memory abstraction is great. I should have used prompt and LLM abstractions as well. 

### Frontend (React + TypeScript)
- Built with React and TypeScript using Vite
- Deployed on AWS Amplify


------------------------------------------
## Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- AWS CLI
- EB CLI

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

Set up environment variables in `.env`:
```
OPENAI_API_KEY=your_openai_key
SERPER_API_KEY=your_serper_key
ALLOWED_ORIGIN=your_frontend_domain
```

Run development server:
```bash
uvicorn main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
```

Set up environment variables in `.env`:
```
VITE_API_URL=your_backend_url
```

Run development server:
```bash
npm run dev
```
