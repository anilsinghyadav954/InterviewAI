# InterviewAI

InterviewAI is an intelligent, full-stack AI-powered interview preparation and career readiness platform. It empowers candidates to practice realistic technical and behavioral interviews, optimize resumes against ATS filters, transcribe spoken answers via browser-native Speech-to-Text, receive multi-dimensional AI scoring, and track performance growth with interactive analytics and PDF reports.

---

## Features

- **Authentication & Password Recovery**: Secure candidate registration, login, bcrypt password hashing, signed JWT session management with auto-refresh protection, plus cryptographically secure Forgot Password / Reset Password with anti-account-enumeration protection, single-use SHA-256 hashed tokens, and SMTP email dispatch.
- **Resume Analyzer**: PDF/text upload, text extraction with magic header validation, ATS compatibility scoring, detected & missing skill taxonomies, and personalized role benchmark recommendations.
- **AI Question Generation**: Dynamic role-based question bank generator (Technical, HR, Mixed across 8 industry roles and 3 difficulty tiers) with resume skill awareness.
- **Mock Interview**: Timed interview practice session, question progression, bookmarking, and instant answer evaluations.
- **AI Answer Evaluation**: Multi-dimensional evaluation engine scoring technical accuracy, relevance, completeness, clarity, and communication with strengths, weak points, and model answer outlines.
- **Performance Analytics**: Longitudinal progress tracking, chronological score trend charts, skill competency distributions, category & role breakdowns, and actionable recommendations.
- **Interview Reports**: Comprehensive evaluation scorecards, question-by-question review with transcripts and scores, and one-click PDF export.
- **Voice Interview**: Browser-native microphone recording with real-time audio visualizer frequency meter and elapsed timer.
- **Speech-to-Text**: Continuous live transcription via Web Speech API (`SpeechRecognition` / `webkitSpeechRecognition`), interim subtitles, live editable transcript, word & character counters, and text-to-speech question audio.
- **Interview History**: Searchable and filterable history for text question banks, voice interview sessions, and past evaluation scorecards.
- **Dashboard**: Central candidate command center aggregating metrics, recent activities, interview readiness, and quick action launchpads.

---

## Technology Stack

### Frontend
- **React**: Modern component-based user interface architecture
- **Vite**: Ultra-fast build tool and dev server
- **Tailwind CSS**: Modern utility-first design system
- **React Router**: Client-side protected and public routing
- **Axios**: HTTP client with Bearer token authentication and 401 response interceptors
- **Recharts**: Interactive responsive data visualization charts
- **Lucide React**: Clean, accessible iconography

### Backend
- **Python**: Robust backend runtime
- **FastAPI**: Modern, high-performance async REST API framework
- **MongoDB**: Document database with compound indexes for candidate sessions
- **JWT**: Stateless token authentication with expiration enforcement
- **bcrypt**: 12-round salted cryptographic password hashing
- **Pydantic**: Strict data contract validation on request and response schemas

### AI
- **Google Gemini API**: Generative AI models (`gemini-1.5-flash`) with dynamic heuristic NLP fallback engines

### Voice & Audio
- **Browser MediaRecorder**: Native microphone audio capture (`getUserMedia`)
- **Browser Speech Recognition API**: Web Speech API (`SpeechRecognition` / `webkitSpeechRecognition`) for real-time speech-to-text
- **Browser SpeechSynthesis**: Native text-to-speech audio reader for interview questions

---

## Project Structure

```text
AI_Resume_Analyzer/
├── backend/
│   ├── app/
│   │   ├── models/            # Domain models and constants
│   │   ├── routes/            # FastAPI API routers (auth, resume, interview, performance, voice)
│   │   ├── schemas/           # Pydantic schemas and strict request/response validators
│   │   ├── services/          # Business logic (AI engine, resume NLP, auth, voice, performance)
│   │   ├── utils/             # Security (bcrypt, JWT) and in-memory rate limiting
│   │   ├── config.py          # Centralized environment configuration
│   │   ├── database.py        # MongoDB connection management & compound index creation
│   │   └── main.py            # FastAPI entry point, CORS middleware & global error handling
│   ├── .env.example           # Backend environment variable template
│   ├── requirements.txt       # Python dependencies
│   ├── test_phase4_interview.py      # Phase 4 question generator tests
│   ├── test_phase5_evaluation.py     # Phase 5 answer evaluation tests
│   ├── test_phase6_performance.py    # Phase 6 analytics and report tests
│   ├── test_phase7_voice.py          # Phase 7 voice & STT tests
│   ├── test_phase8_comprehensive.py  # Phase 8 production readiness & security audit suite
│   └── test_resume_pipeline.py       # Resume parsing & ATS test suite
│
├── frontend/
│   ├── public/                # Static assets and icons
│   ├── src/
│   │   ├── components/        # Reusable UI components (Navbar, Sidebar, Card, Button, Modal, etc.)
│   │   ├── context/           # React context providers (AuthContext)
│   │   ├── layouts/           # PublicLayout and DashboardLayout wrappers
│   │   ├── pages/             # Route pages (Landing, Login, Dashboard, Resume, Mock, Voice, Performance, History, Profile, Settings, 404)
│   │   ├── services/          # Centralized Axios API service layer (api.js)
│   │   ├── utils/             # PDF export helpers and mock data
│   │   ├── App.jsx            # Main route configuration
│   │   └── main.jsx           # React DOM root mounting
│   ├── .env.example           # Frontend environment variable template
│   ├── package.json           # Dependencies and build scripts
│   └── vite.config.js         # Vite configuration
│
├── .env.example               # Unified project environment template
├── .gitignore                 # Production-grade git ignore rules
└── README.md                  # Project documentation
```

---

## Environment Setup

### 1. Backend Environment (`backend/.env`)

Copy `backend/.env.example` to `backend/.env` and configure:

```env
# Database Configuration
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=interview_ai

# Security & Authentication
JWT_SECRET_KEY=replace_with_a_secure_random_secret_minimum_32_characters
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
FRONTEND_URL=http://localhost:5173

# Email / SMTP Configuration (Gmail or standard SMTP)
# For Gmail: Use smtp.gmail.com, port 587, and a 16-character App Password (https://myaccount.google.com/apppasswords)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_16_character_app_password
SMTP_FROM_EMAIL=your_email@gmail.com
SMTP_FROM_NAME=InterviewAI
SMTP_USE_TLS=true

# Google Gemini AI API Configuration (Optional: uses built-in NLP heuristics if empty)
GEMINI_API_KEY=
GEMINI_MODEL=gemini-1.5-flash

# CORS Allowed Origins (Comma-separated origins for production)
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Application Environment
ENVIRONMENT=production
```

### 2. Frontend Environment (`frontend/.env`)

Copy `frontend/.env.example` to `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

---

## Local Development

### Starting the Backend

1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```
2. Activate your virtual environment and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
   API interactive documentation will be available at: `http://127.0.0.1:8000/docs`

### Starting the Frontend

1. Navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```
2. Install node dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```
   The application will be accessible at: `http://localhost:5173`

---

## Testing

All backend test suites run against the in-process FastAPI application and MongoDB:

```bash
cd backend

# Run Forgot Password & Reset Password suite:
python test_forgot_password.py

# Run comprehensive Phase 8 production readiness & security suite:
python test_phase8_comprehensive.py

# Run Phase 7 Voice Interview suite:
python test_phase7_voice.py

# Run Phase 6 Performance Analytics suite:
python test_phase6_performance.py

# Run Phase 5 Answer Evaluation suite:
python test_phase5_evaluation.py

# Run Phase 4 Question Generator suite:
python test_phase4_interview.py

# Run Resume Pipeline suite:
python test_resume_pipeline.py
```

---

## Build

To compile and optimize the frontend for production deployment:

```bash
cd frontend
npm run build
```

This outputs production-optimized, minified chunks into the `frontend/dist/` directory ready for deployment on static hosts (Vercel, Netlify, Cloudflare Pages, Nginx, or AWS S3/CloudFront).

---

## Browser Compatibility

- **Voice Recording (`MediaRecorder`)**: Supported across all modern Chromium browsers (Chrome, Edge, Brave), Firefox, and Safari 14.1+.
- **Speech-to-Text (`SpeechRecognition`)**: Powered by `window.SpeechRecognition` with automatic fallback to `window.webkitSpeechRecognition`. Supported in Google Chrome, Microsoft Edge, and Chromium-based browsers. If opened on unsupported browsers, a non-intrusive fallback notification is displayed, allowing candidates to type their response directly without interruption.
- **Microphone Permissions**: The browser will request microphone permission on initial recording start. If permission is denied or blocked, the UI gracefully informs the user with instructions to enable microphone access in browser settings.

---

## Security

- **Strict User Isolation**: All database queries are explicitly scoped to the authenticated user ID (`user_id`). Users cannot access, modify, or view other candidates' resumes, question sets, evaluations, reports, or voice sessions.
- **Password Security & Complexity**: Passwords are never stored in plaintext and must adhere to strong security rules (minimum 8 characters, at least 1 uppercase letter, 1 lowercase letter, and 1 number). Passwords are cryptographically salted and hashed using `bcrypt` (12 rounds) before database persistence.
- **Password Reset Cryptography & Anti-Enumeration**:
  - The Forgot Password endpoint (`POST /api/auth/forgot-password`) strictly returns a generic 200 response (`"If an account exists for this email, a password reset link has been sent."`) regardless of whether the email is registered, completely preventing email enumeration attacks.
  - Reset tokens are generated using `secrets.token_urlsafe(32)`. Raw reset tokens are **never** persisted in the database; only a SHA-256 cryptographic hash (`hashlib.sha256`) is stored with a 20-minute expiration window.
  - Reset tokens are strictly single-use; any previous pending tokens for a user are automatically revoked whenever a new reset is requested.
  - Dedicated rate-limiting on password reset requests blocks brute-force abuse (HTTP 429).
- **Stateless JWT Tokens**: Tokens are cryptographically signed with HMAC-SHA256 (`HS256`) and expire automatically after 60 minutes.
- **File Upload Safeguards**: Resume uploads are strictly capped at 5MB, limited to `.pdf` and `.txt`, validated against binary signatures (`%PDF-` header check), and sanitized against path traversal vulnerabilities. Password-protected and encrypted PDFs are safely rejected.
- **Rate Limiting & Abuse Prevention**: AI-intensive endpoints (resume parsing, question generation, answer evaluation, voice evaluation, and forgot password) are protected by a sliding window in-memory rate limiter that returns `HTTP 429 Too Many Requests` if abused.
- **Production CORS**: Configured to restrict origins to verified domains, avoiding wildcard (`*`) origins when handling authenticated credentials.
- **Secrets Isolation**: Secrets (JWT keys, database credentials, AI keys, SMTP credentials) are loaded strictly through environment variables and are never committed to version control.

