# TARANG Platform
Technology for Aquatic Regeneration, Assessment, Navigation & Geotagging

*Note: This README is a repository skeleton stub conforming to TARANG Implementation Guide v6.2. Full documentation will be expanded in Prompt I.*

---

## 1. Overview
Automated marine debris detection and management platform utilizing Side-Scan Sonar (SSS) imagery and artificial intelligence.

## 2. Architecture
Three-tier enterprise architecture:
- Frontend: React + TypeScript + Tailwind CSS (Vite)
- Gateway: Nginx reverse proxy with rate limiting and TLS termination
- Auth / Identity Service: Spring Boot + Spring Security (RS256 JWT, users, roles, organizations)
- Application & Processing Engine: FastAPI + Celery + OpenCV + PyTorch (surveys, SSS pipeline, AI inference, XAI, physics validation, geotagging, deduplication)
- Persistence: PostgreSQL 14+ / PostGIS 3.2+ and Redis

## 3. Repository Structure
- `frontend/`: Web UI components, sonar viewer, map views, dashboards, RTK Query API slices.
- `backend-auth/`: Spring Boot authentication, user management, and token service.
- `backend-app/`: FastAPI application core, Alembic migrations, SSS preprocessing pipeline, and AI inference.
- `storage/`: Structured storage root for raw, extracted, and processed sonar frames and model weights.
- `nginx/`: Nginx gateway reverse proxy and rate-limiting configuration.
- `docker/`: Dockerfiles and container definitions for each service layer.

## 4. Technology Stack
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, Redux Toolkit, RTK Query, Leaflet.
- **Backend Auth**: Java 17, Spring Boot 3, Spring Security, BCrypt, JJWT (RS256).
- **Backend App**: Python 3.11, FastAPI, SQLAlchemy 2, Alembic, Celery, Redis.
- **Computer Vision & AI**: OpenCV, NumPy, PyTorch, YOLO, U-Net/U-Net++, Grad-CAM XAI.
- **Database & GIS**: PostgreSQL 14+, PostGIS 3.2+.
- **Gateway**: Nginx.

## 5. Prerequisites
- Docker Engine 24+ & Docker Compose v2+
- Node.js 20+ & npm
- JDK 17+ & Apache Maven 3.9+
- Python 3.11+
- Git

## 6. Environment Setup
Copy the environment template and configure local variables:
```bash
cp .env.example .env
```

## 7. Database
PostgreSQL with PostGIS extension. Migrations are strictly managed via Alembic:
```bash
make migrate
```

## 8. Running the Services
Start the full stack with Docker Compose:
```bash
make build
make up
```

## 9. Authentication
Asymmetric JWT (RS256) issued exclusively by Spring Boot (`/api/auth/*`). FastAPI (`/api/v1/*`) verifies tokens using the public key ID (`kid`).

## 10. Survey Processing
Upload -> Ingestion -> Adapter -> Nadir-Zone Mask -> Slant-Range Correction -> Calibrated TVG -> Destriping -> Denoising -> Quality Assessment -> AI Detection -> Evidence Fusion -> Geotagging -> Target Association.

## 11. AI
YOLO bounding-box detector, U-Net segmentation refinement, Grad-CAM XAI, physics validation, and closed-loop retraining dataset management.

## 12. Storage
Storage root layout:
```
storage/
└── surveys/{survey_id}/
    ├── raw/
    ├── extracted/
    └── processed/{processing_job_id}/
```

## 13. API
- Auth: `/api/auth/*` (Login, Register, Refresh, Profile)
- Application: `/api/v1/*` (Surveys, Frames, Detections, Targets, Reviews, Missions, Reports)

## 14. Testing
Run multi-tier test suites:
```bash
make test
```

## 15. Security
Strict RBAC, asymmetric JWT validation, BCrypt password hashing, hashed refresh tokens, rate limiting, and audit logging.

## 16. Development Rules
- Spring Boot is the single owner of authentication and users.
- FastAPI owns surveys, pipelines, and AI inference.
- Alembic is the sole database migration tool.
- Never store raw sonar binaries in PostgreSQL.
- Zero fabricated predictions or synthetic metrics.

## 17. Deployment
Containerized deployment with multi-stage Docker builds orchestrated via Docker Compose or Kubernetes.

## 18. SIH Demo
Quick-start demonstration mode with pre-calibrated sample SSS survey data.

## 19. License / Team
TARANG Development Team. All rights reserved.
