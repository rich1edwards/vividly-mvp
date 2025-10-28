MVP - Product Requirements Document
Version: 1.0
Date: October 27, 2025
Status: Draft
1. Introduction & Overview
Vividly is a web-based educational application designed to make learning High School STEM subjects more engaging and effective. It leverages AI to generate personalized micro-lessons (initially audio+script, then full video) that explain academic topics using analogies and themes based on a student's individual interests.
Problem: Traditional textbook content can be dry, one-size-fits-all, and fail to connect with students' passions, leading to disengagement.
MVP Goal: To validate the core technical pipeline (AI-driven NLU, personalized content generation, caching) and test the viability of a B2B pilot model within a single school district (Metro Nashville Public Schools - MNPS). The MVP will focus on delivering the core student experience and essential administrative/teacher views for pilot management and evaluation.
Vision: To transform K-12 STEM education by providing hyper-personalized, engaging, and effective learning content accessible to every student.
2. Goals for MVP
Validate Core Technology: Prove the feasibility of the end-to-end generation pipeline: Free-text NLU $\rightarrow$ Topic Standardization $\rightarrow$ Cache Check $\rightarrow$ Personalized Script/Audio ("Vivid Now") $\rightarrow$ Asynchronous Video ("Vivid Learning").
Test B2B Pilot Viability: Assess the adoption and engagement within a controlled pilot in MNPS high schools.
Achieve Target KPIs: Meet or exceed the defined success metrics for teacher/student adoption, student engagement, and cache hit rate during the pilot phase.
Gather User Feedback: Collect qualitative feedback from students, teachers, and administrators to inform future development priorities.
Establish Foundational Compliance: Implement necessary measures to ensure compliance with FERPA and COPPA within the school context.
3. Users & Roles (MVP Scope)
A. School & District Roles (B2B Customers - MNPS Pilot):
District Administrator: Manages pilot setup, bulk student onboarding, approves student account requests, manages School Admin/Teacher accounts, views district-level KPIs.
School Administrator (Principal): Manages Teacher accounts for their school, approves student account requests from their teachers, views school-level KPIs.
Teacher / Educator: Manages class groups, views engagement/progress for their students, requests new student accounts (routed for approval).
Student: Primary end-user. Inputs learning requests, views generated content, provides feedback, manages interests.
B. Internal Roles (Vividly Staff):
Vividly Admin (Technical): Super-user access for system management, user administration, and infrastructure oversight.
Vividly Curriculum Manager (Content): Manages OER ingestion, builds/maintains the topic hierarchy, curates the canonical interest list.
Vividly Ops / Support (Read-Only): Troubleshoots issues, monitors system health, provides customer support.
4. MVP Features (Scope)
Core Student Experience:
FEAT-001: User Authentication: Secure login for all defined roles. (Student login managed initially via roster upload).
FEAT-002: Student Profile & Interest Management: Students can view/rank predefined canonical interests.
FEAT-003: Conversational Topic Request (NLU): Input field for students to type free-text requests.
FEAT-004: Topic Standardization & Clarification: LLM backend process to map free-text input to canonical topic_id, including basic clarification dialogue if needed.
FEAT-005: Cache Check: System checks for existing (topic_id, interest, style) video before initiating generation.
FEAT-006: "Vivid Now" Display: Immediate display of generated script + embedded audio player upon cache miss.
FEAT-007: "Vivid Learning" Display: Asynchronous loading and display of the fully rendered video (replacing Vivid Now) upon completion. Basic video player controls.
FEAT-008: Post-Lesson Feedback: Buttons ("Mark as Complete," "Make it Simpler," "Try Different Interest") triggering corresponding backend actions (progress update, re-generation request).
FEAT-009: Basic Progress Tracking: Visual indication on a student view (simple list or adapted tree for now) showing completed topics.
Teacher & Admin Experience:
FEAT-010: Teacher Dashboard: View list of assigned students, basic engagement metrics (e.g., last login, videos viewed) per student.
FEAT-011: Class Management (Teacher): Ability to create simple class groups and view students within them.
FEAT-012: Student Account Request (Teacher): Form to request a new student account, triggering approval workflow.
FEAT-013: School Admin Dashboard: View aggregated engagement metrics for their school, manage Teacher accounts, approve student requests.
FEAT-014: District Admin Dashboard: View aggregated engagement metrics for the district, manage School Admin/Teacher accounts, approve student requests.
FEAT-015: Bulk Student Upload (District Admin): Basic CSV upload functionality for initial student rostering.
Backend & System:
FEAT-016: OER Ingestion (MVP): Initial ingestion pipeline using OpenStax .docx files for core Physics/Math content.
FEAT-017: Topic Hierarchy: Backend definition of the course structure (Topic Tree/List).
FEAT-018: Canonical Interest List: Backend storage and management of the predefined interests.
FEAT-019: AI Generation Pipeline: Workers for NLU, Script Generation (LearnLM via RAG), TTS, and Video Rendering (Nano Banana). Includes fallback logic for interests.
FEAT-020: Job Queue System: Using Cloud Pub/Sub + Cloud Tasks.
FEAT-021: Caching Mechanism: Storing/retrieving generated assets in GCS keyed by (topic_id, interest, style).
FEAT-022: Role-Based Access Control (RBAC): Backend logic enforcing permissions for each defined user role.
FEAT-023: Basic AI Safety Guardrails: Input sanitization, Canonical Interest list, prompt-level safety instructions, basic output filtering (keyword-based initially).
Out of Scope for MVP: Parent accounts, SSO, SIS integration, advanced reporting/analytics, human-in-the-loop review interface, complex accessibility features (beyond basics), payment processing, OpenStax web scraping, LibreTexts API integration.
5. User Flows
Student Content Request: Student logs in $\rightarrow$ Enters free-text query $\rightarrow$ (Optional Clarification) $\rightarrow$ Confirms Topic $\rightarrow$ System checks cache $\rightarrow$ Displays "Full Experience" (hit) OR Displays "Fast Path" then notifies when "Full Experience" ready (miss) $\rightarrow$ Student views content $\rightarrow$ Student provides feedback.
Teacher Checks Progress: Teacher logs in $\rightarrow$ Selects a class $\rightarrow$ Views dashboard showing student list and basic engagement metrics.
Teacher Requests Student Account: Teacher logs in $\rightarrow$ Navigates to student management $\rightarrow$ Fills out request form $\rightarrow$ Submits $\rightarrow$ Request routed to School/District Admin.
Admin Approves Request: Admin logs in $\rightarrow$ Views pending requests $\rightarrow$ Reviews request $\rightarrow$ Approves/Denies $\rightarrow$ (If Approved) Student account created/invited.
6. Non-Functional Requirements
Performance: "Fast Path" (script + audio) should load within 5-10 seconds on cache miss. Cache hits should load video < 2 seconds. NLU/Clarification step should respond < 5 seconds.
Scalability: MVP infrastructure should handle load for the pilot (~3,000 active students, moderate usage). Focus on serverless components (Cloud Run, Cloud Functions, Pub/Sub, Tasks).
Security: Implement standard web security practices (HTTPS, secure authentication, input validation, dependency scanning). Protect API keys and credentials. Ensure GCS bucket permissions are correctly configured.
Compliance: Adhere strictly to the drafted Data Privacy Policy. Ensure all data handling meets FERPA requirements for acting as a "School Official" and COPPA requirements for school-based consent. Implement data minimization.
Accessibility: MVP web interface should adhere to basic WCAG 2.1 Level AA guidelines (e.g., sufficient color contrast, keyboard navigation basics, semantic HTML). Generated scripts provide inherent transcript capability.
7. Success Metrics (KPIs) - Pilot Phase Targets
Teacher Adoption Rate: 50%
Student Activation Rate (in Active Classes): 30%
Student Engagement: Average 3 videos generated per active student (over pilot duration).
Cache Hit Rate: 15% (Initial target, aim to increase rapidly via usage and potential pre-warming).
8. Future Considerations (Post-MVP)
Single Sign-On (SSO) Integration (Google, Clever, ClassLink).
Automated Rostering / SIS Integration (OneRoster).
Parent Portal / Linked Accounts.
Advanced Teacher/Admin Reporting and Analytics.
Expansion of OER Content Sources (LibreTexts API).
Human-in-the-Loop (HITL) content review system.
Enhanced AI Safety Features (Sophisticated classifiers, bias detection).
Full WCAG 2.1 AA Compliance including video player accessibility.
Subscription Management and Payment Integration.

