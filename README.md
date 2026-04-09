# SmartSpend

SmartSpend is a production-oriented personal finance platform built with:

- `Next.js 16` frontend
- `FastAPI` backend
- real-time dashboard updates via WebSockets
- AI/ML-driven analytics, forecasting, anomaly detection, and financial guidance

## Stack detection

- Frontend: Next.js App Router, TypeScript, Tailwind CSS, Recharts
- Backend: FastAPI, Python 3.12
- Persistence: JSON-backed file storage under [`backend/data`](/D:/newwork/finset/backend/data)
- Deployment-ready targets:
  - local Docker Compose
  - Vercel + Render
  - AWS EC2 with Terraform

## Local development

Frontend:

```bash
npm install
npm run dev -- --hostname 127.0.0.1 --port 3001
```

Backend:

```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8001
```

Health checks:

- frontend: `GET /api/health`
- backend: `GET /health`

## Docker

Production-style local stack:

```bash
docker compose build
docker compose up -d
```

Services:

- frontend: [http://127.0.0.1:3001](http://127.0.0.1:3001)
- backend: [http://127.0.0.1:8001/health](http://127.0.0.1:8001/health)

Files:

- [Dockerfile.frontend](/D:/newwork/finset/Dockerfile.frontend)
- [backend/Dockerfile](/D:/newwork/finset/backend/Dockerfile)
- [docker-compose.yml](/D:/newwork/finset/docker-compose.yml)
- [.env.docker.example](/D:/newwork/finset/.env.docker.example)

## One-command deployment

Run:

```bash
./deploy.sh
```

What it does:

1. lints frontend
2. builds frontend
3. validates backend import
4. builds Docker images
5. starts Docker Compose
6. waits for health checks with retries

## CI/CD

GitHub Actions workflow:

- [ci-cd.yml](/D:/newwork/finset/.github/workflows/ci-cd.yml)

Pipeline behavior:

1. install frontend dependencies
2. run `npm run lint`
3. run `npm run build`
4. install backend dev dependencies
5. run backend smoke tests
6. build and push Docker images to `ghcr.io`
7. optionally deploy to EC2 over SSH if secrets are configured

Recommended GitHub secrets for auto-deploy:

- `EC2_HOST`
- `EC2_USER`
- `EC2_SSH_KEY`
- `APP_URL`
- `FRONTEND_ORIGINS`

## AWS infrastructure

Terraform files:

- [infra/aws/versions.tf](/D:/newwork/finset/infra/aws/versions.tf)
- [infra/aws/variables.tf](/D:/newwork/finset/infra/aws/variables.tf)
- [infra/aws/main.tf](/D:/newwork/finset/infra/aws/main.tf)
- [infra/aws/outputs.tf](/D:/newwork/finset/infra/aws/outputs.tf)
- [infra/aws/user_data.sh.tpl](/D:/newwork/finset/infra/aws/user_data.sh.tpl)

This provisions:

- VPC
- public subnet
- internet gateway
- route table
- security group
- EC2 instance
- Docker-ready host bootstrap

Apply example:

```bash
cd infra/aws
terraform init
terraform apply -var="key_name=YOUR_KEYPAIR"
```

## Vercel + Render deployment

Frontend on Vercel:

- [vercel.json](/D:/newwork/finset/vercel.json)

Backend on Render:

- [render.yaml](/D:/newwork/finset/render.yaml)

Required Vercel env vars:

- `BACKEND_API_BASE=https://your-backend.onrender.com`
- `NEXT_PUBLIC_BACKEND_API_BASE=https://your-backend.onrender.com`
- `NEXT_PUBLIC_BACKEND_WS_BASE=wss://your-backend.onrender.com`
- `APP_URL=https://your-frontend.vercel.app`
- `NEXT_PUBLIC_APP_URL=https://your-frontend.vercel.app`

Required Render env vars:

- `FRONTEND_ORIGINS=https://your-frontend.vercel.app`
- `FRONTEND_ORIGIN_REGEX=https://.*\\.vercel\\.app`

## Logging and monitoring

- backend logs go to stdout and [`backend/logs/smartspend.log`](/D:/newwork/finset/backend/logs/smartspend.log)
- backend request timing is logged through middleware
- Docker health checks are configured for frontend and backend

## Testing

Backend smoke tests:

- [backend/tests/test_health.py](/D:/newwork/finset/backend/tests/test_health.py)

Run manually:

```bash
pytest backend/tests -q
```
