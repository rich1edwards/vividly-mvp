Vividly
Vividly is a web and  phone based educational application using AI to generate personalized micro-lessons (audio, script, video) for High School STEM subjects, tailored to student interests.
This README provides an overview for the Minimum Viable Product (MVP) aimed at a pilot program with Metro Nashville Public Schools (MNPS).
MVP Goals
Validate the core AI personalization and content generation pipeline.
Test B2B pilot viability within MNPS.
Achieve defined pilot KPIs for adoption, engagement, and cache performance.
Ensure foundational compliance with FERPA & COPPA.
Technology Stack (Planned)
Cloud Provider: Google Cloud Platform (GCP)
Frontend: TBD (e.g., React, Vue, Angular)
Backend: Python (e.g., Flask/Django/FastAPI) hosted on Cloud Run or GKE
AI - Script Gen: Google LearnLM (or similar) via Vertex AI, using RAG
AI - Video Gen: Nano Banana API (External)
AI - NLU: Google LLM via Vertex AI
AI - TTS: Google Cloud Text-to-Speech API
Vector Database: Vertex AI Vector Search
Job Queue: Cloud Pub/Sub + Cloud Tasks
Databases:
User/Metadata: Cloud SQL for PostgreSQL
Cache/Asset Storage: Google Cloud Storage (GCS)
Monitoring: Google Cloud Monitoring, Logging, Error Reporting (or Datadog/Sentry)
CI/CD: GitHub Actions, Google Cloud Build
Architecture Overview (MVP)
Student Request: Student interacts via Web App (React/Vue/Angular), inputs free-text query.
NLU & Topic Standardize: Web App backend sends query to NLU Service (Cloud Run/Function w/ Vertex AI LLM). Optional clarification loop. Confirmed topic_id returned.
Cache Check: Backend checks GCS or DB index for existing video (topic_id, interest, style).
Cache Hit: Return GCS URL for video $\rightarrow$ Web App displays "Full Experience". DONE.
Cache Miss:
Publish "Generate Script" job to Pub/Sub.
Cloud Task triggers Script Worker (Cloud Run/Function).
Script Generation: Worker queries Vertex AI Vector Search (RAG w/ OER data), calls LearnLM (Vertex AI) with topic, interest, RAG context $\rightarrow$ Generates JSON storyboard.
Fast Path Generation: Script Worker publishes "Generate Audio" job. Audio Worker (Cloud Run/Function) calls TTS API $\rightarrow$ Saves audio to GCS. Script + Audio URL sent back to Web App.
Fast Path Display: Web App shows script and audio player.
Full Experience Generation (Async): Script Worker also publishes "Generate Video" job. Video Worker (Cloud Run/Function) calls Nano Banana API with script + audio URL $\rightarrow$ Receives final video $\rightarrow$ Saves video to GCS.
Notification & Update: Video Worker (or separate mechanism) notifies Web App. Web App updates view to show "Full Experience" video player.
Setup Instructions (Placeholder)
Clone the repository:
git clone [repository-url]
cd vividly


Set up GCP Project:
Ensure you have a GCP project with billing enabled.
Enable necessary APIs (Vertex AI, Cloud Storage, Pub/Sub, Cloud Tasks, Cloud Run, Cloud SQL, etc.).
Configure authentication (e.g., gcloud auth application-default login).
Configure Environment Variables:
Create a .env file based on .env.example.
Fill in GCP project ID, database credentials, API keys (Nano Banana, etc.), GCS bucket names, Pub/Sub topics.
Install Dependencies:
Backend: pip install -r requirements.txt (or use Poetry/Pipenv)
Frontend: cd frontend && npm install (or yarn)
Database Setup:
Set up Cloud SQL for PostgreSQL instance.
Run database migrations (details TBD).
OER Ingestion:
Run the initial OER ingestion script (details TBD) to populate the Vector DB (scripts/ingest_oer.py).
Key Components (Example Structure)
/vividly
|-- webapp/           # Frontend code (React/Vue/Angular)
|-- backend/          # Backend API service (Flask/Django/FastAPI)
|   |-- api/          # API endpoint definitions
|   |-- core/         # Core business logic, DB models
|   |-- services/     # External service integrations (GCP, Nano Banana)
|-- workers/          # Background worker services (Cloud Run/Functions)
|   |-- nlu_service/
|   |-- script_generator/
|   |-- tts_generator/
|   |-- video_generator/
|-- scripts/          # Utility and operational scripts
|   |-- ingest_oer.py
|   |-- prewarm_cache.py
|-- .env.example      # Environment variable template
|-- requirements.txt  # Python dependencies
|-- Dockerfile        # Docker config for services
|-- README.md         # This file


Running the Application (Placeholder)
Start Backend API:
# (Activate virtual env if needed)
python backend/main.py # Or use gunicorn/uvicorn


Start Frontend Dev Server:
cd webapp
npm run dev # Or yarn dev


Deploy/Run Workers: (Details TBD - likely deployed to Cloud Run/Functions and triggered by Cloud Tasks/Pub/Sub).
Contributing
(Placeholder - Outline basic process if applicable, e.g., fork, branch, PR).
License
(Placeholder - e.g., Proprietary or MIT License).

