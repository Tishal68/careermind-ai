# CareerMind AI — Resume match and Ollama career coach

The main workspace now focuses on choosing a job role, matching a resume against
its core skills, identifying learning steps, and chatting with a local Ollama coach.
See **[RUN_LOCAL.md](RUN_LOCAL.md)** for local setup and **[RENDER_SETUP.md](RENDER_SETUP.md)** for Render with Ollama Cloud.
The older platform features described below remain in the repository.

## Original platform documentation

NexPath is a production-grade, AI-powered Career Operating System built with **Next.js 14+**, **FastAPI**, **SQLAlchemy**, and **Google Gemini AI**. Designed as a high-performance SaaS platform, it empowers users to parse resumes, audit ATS readability, compute skill gaps against specialized tech roles, track weekly learning roadmaps, interact with an AI career coach, and practice real-time mock interviews.

---

## 🚀 Key Features

1. **JWT Authentication & Security**: Secure registration, login, token refresh, and user profile management using bcrypt password hashing.
2. **Multi-Format Resume Parser**: PDF and DOCX parser extracting technical skills, soft skills, tools, education, work experience, and contact data.
3. **Gemini Skill Gap Analysis**: Detailed scoring across ATS Compatibility, Resume Quality, and Career Readiness against 8 fields and 9 tech roles.
4. **Personalized Learning Roadmaps**: 4-8 week structured milestone timelines with task checkboxes, hour estimates, and curated learning resources.
5. **Project Recommendation Engine**: Targeted portfolio project cards matched to missing candidate skills.
6. **AI Career Assistant (RAG Chatbot)**: Notion/ChatGPT-style glassmorphic streaming interface backed by TF-IDF / FAISS vector retrieval and full resume context awareness.
7. **AI Mock Interview Arena**: Interactive simulator supporting Technical, HR, Behavioral, and Mixed interviews with instant Gemini scoring and model answer feedback.
8. **Unified Dashboard & Analytics**: Executive command center consolidating metrics, skill progress gauges, and recent evaluation reports.

---

## 📁 Directory Structure

```
careermind-ai/
├── frontend/                     # Next.js 14+ App Router Frontend
│   ├── src/
│   │   ├── app/                 # Pages (Workspace, Coach, Reports, Settings)
│   │   ├── components/          # UI, Workspace, Coach, Reports components
│   │   ├── context/             # Auth, Session, Career, Workspace contexts
│   │   ├── hooks/               # Domain hooks (useWorkspace, useCoach, etc.)
│   │   ├── services/            # API client services
│   ├── package.json
│   └── tailwind.config.js
├── backend/                      # FastAPI Python Backend
│   ├── app/
│   │   ├── api/v1/              # Domain REST API Endpoints
│   │   ├── core/                # Database engine, JWT security, Config
│   │   ├── intelligence/        # 15 Product Intelligence Engines & AI Command Center
│   │   ├── kernel/              # Career OS Kernel Source of Truth
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── repositories/        # Repository Layer
│   │   ├── services/            # Domain Services
│   │   └── main.py              # FastAPI app entry point
│   ├── requirements.txt
│   └── Dockerfile
├── render.yaml                  # Render Blueprint deployment configuration
├── docker-compose.yml           # Docker container setup
└── README.md
```

---

## 🌐 Deploying on Render

Use the root Dockerfile and the updated Docker Blueprint. Add your Ollama Cloud key and model settings as described in **[RENDER_SETUP.md](RENDER_SETUP.md)**, then redeploy. The Docker service starts both Next.js and FastAPI.

---

## ⚡ How to Run Locally

### 1. Start FastAPI Backend
```bash
cd backend
py -m pip install -r requirements.txt
py -m uvicorn app.main:app --reload --port 8000
```
Backend API interactive docs: `http://localhost:8000/docs`

### 2. Start Next.js Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend web application: `http://localhost:3000`

---

## 🧪 Testing

Run the automated system diagnostic test suite:
```bash
py test_e2e.py
```
