# InsightFlow — Enterprise Operations Analytics & AI Automation Platform

A full-stack enterprise analytics platform for managing sales, customers, products, inventory, payments, and business reports with an AI-powered business analyst assistant.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, TailwindCSS, shadcn/ui, ECharts, Zustand |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic, Pandas |
| Database | PostgreSQL 16 |
| AI | OpenAI API (GPT-4o-mini) |
| DevOps | Docker, Docker Compose |

## Features

- **Authentication**: JWT-based login with role-based access control (admin, manager, staff)
- **Dashboard**: KPI cards, revenue trends, product performance, regional analysis, alerts
- **Orders**: Full CRUD with search, filtering, sorting, and pagination
- **Customers**: Customer management with order history tracking
- **Products**: Product catalog with inventory monitoring and low-stock alerts
- **CSV Import**: Bulk data upload for orders, customers, products, and inventory
- **Analytics**: Revenue growth, customer repeat rate, payment delay analysis, sales targets
- **AI Assistant**: Natural language business Q&A, automated report generation, trend explanation
- **Export**: CSV export for sales/customers/inventory, PDF business report
- **Audit Logs**: Complete action tracking for compliance

## Project Structure

```
insightflow/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entry
│   │   ├── config.py            # Pydantic settings (.env)
│   │   ├── database.py          # SQLAlchemy engine + session
│   │   ├── dependencies.py      # Auth + DB dependencies
│   │   ├── models/              # SQLAlchemy ORM models (14 tables)
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── routers/             # API route handlers (11 routers)
│   │   ├── services/            # Business logic layer
│   │   └── utils/               # CSV parser, seed data, audit logging
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/                 # Axios client + API functions
│   │   ├── components/ui/       # shadcn/ui components
│   │   ├── layouts/             # Dashboard layout with sidebar
│   │   ├── pages/               # All page components
│   │   ├── stores/              # Zustand state management
│   │   └── types/               # TypeScript interfaces
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Or: Python 3.12+, Node.js 20+, PostgreSQL 16

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone <repo-url>
cd insightflow

# Copy environment files
cp .env.example .env
cp backend/.env.example backend/.env

# Start all services
docker compose up --build

# Seed the database (in another terminal)
docker compose exec backend python -m app.utils.seed_data
```

The app will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Local Development

**Backend:**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up PostgreSQL, then:
cp .env.example .env
# Edit .env with your database credentials and OpenAI API key

# Create tables and seed data
python -m app.utils.seed_data

# Start the server
uvicorn app.main:app --reload --port 8000
```

Run the backend test suite with the development dependencies:

```bash
cd backend
pip install -r requirements-dev.txt
pytest -q
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

## Default Accounts

After running the seed script, these accounts are available:

| Email | Password | Role |
|-------|----------|------|
| admin@insightflow.com | password123 | Admin |
| manager@insightflow.com | password123 | Manager |
| staff1@insightflow.com | password123 | Staff |
| staff2@insightflow.com | password123 | Staff |
| analyst@insightflow.com | password123 | Manager |

## API Endpoints

### Authentication
- `POST /api/auth/login` — Login with email/password
- `POST /api/auth/register` — Register new user
- `GET /api/auth/me` — Current user profile

### Dashboard
- `GET /api/dashboard/summary` — KPI summary
- `GET /api/dashboard/sales-trend` — Monthly revenue trend
- `GET /api/dashboard/top-products` — Top products by revenue
- `GET /api/dashboard/top-customers` — Top customers by spending
- `GET /api/dashboard/region-performance` — Regional analysis
- `GET /api/dashboard/recent-orders` — Latest orders
- `GET /api/dashboard/alerts` — Active alerts

### Orders / Customers / Products
- Full CRUD with search, filtering, and pagination
- `GET/POST /api/orders`, `GET/PUT/DELETE /api/orders/{id}`
- `GET/POST /api/customers`, `GET/PUT/DELETE /api/customers/{id}`
- `GET/POST /api/products`, `GET/PUT/DELETE /api/products/{id}`

### Analytics
- `GET /api/analytics/revenue` — Revenue analytics
- `GET /api/analytics/growth` — Growth rate analysis
- `GET /api/analytics/customer-repeat-rate` — Customer retention
- `GET /api/analytics/product-performance` — Product metrics
- `GET /api/analytics/region-performance` — Regional metrics
- `GET /api/analytics/payment-delay` — Overdue payments
- `GET /api/analytics/sales-targets` — Target completion

### AI Assistant
- `POST /api/ai/ask` — Ask a business question
- `POST /api/ai/generate-report` — Generate AI report
- `POST /api/ai/explain-trend` — Explain a trend
- `POST /api/ai/inventory-suggestion` — Inventory recommendations

### Export
- `GET /api/export/sales.csv` — Sales data CSV
- `GET /api/export/customers.csv` — Customer data CSV
- `GET /api/export/inventory.csv` — Inventory data CSV
- `GET /api/export/business-report.pdf` — Business report PDF

### Upload
- `POST /api/upload/orders` — Import orders CSV
- `POST /api/upload/customers` — Import customers CSV
- `POST /api/upload/products` — Import products CSV
- `POST /api/upload/inventory` — Import inventory CSV

## Database Schema

14 tables with proper foreign keys and indexes:
`users`, `roles`, `customers`, `products`, `suppliers`, `orders`, `order_items`, `inventory`, `payments`, `shipments`, `sales_targets`, `upload_history`, `audit_logs`, `ai_reports`

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection string | postgresql://insightflow:insightflow@localhost:5432/insightflow |
| SECRET_KEY | JWT signing secret | dev-secret-key-change-me |
| OPENAI_API_KEY | OpenAI API key | (required for AI features) |
| OPENAI_MODEL | OpenAI model name | gpt-4o-mini |
| CORS_ORIGINS | Allowed frontend origins | http://localhost:5173 |

## License

MIT
