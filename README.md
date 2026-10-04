# NexPath (CareerMind AI) - Production AI Career Operating System

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

NexPath is fully configured for 1-click deployment on [Render](https://render.com).

### Option 1: Deploy with Render Blueprint (`render.yaml`)
1. Push this repository to GitHub: `https://github.com/Tishal68/careermind-ai.git`
2. Go to [Render Dashboard](https://dashboard.render.com/) $\rightarrow$ Click **New +** $\rightarrow$ Select **Blueprint**.
3. Connect your GitHub repository `Tishal68/careermind-ai`.
4. Render will automatically detect `render.yaml` and configure:
   - **`nexpath-backend`**: FastAPI Web Service (`uvicorn app.main:app --host 0.0.0.0 --port $PORT`)
   - **`nexpath-frontend`**: Next.js Web Service (`npm run build` & `npm start`)
5. Add your `GEMINI_API_KEY` under Environment Variables in the backend service.
6. Click **Apply**. Render will deploy both services automatically!

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
