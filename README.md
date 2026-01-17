# Science Digest - Scientific News Aggregator

A full-stack application that aggregates scientific papers from multiple databases, uses AI to generate digestible summaries with credibility analysis, creates accompanying images, and outputs formatted newsletters.

## Features

- **Multi-Source Aggregation**: Collect papers from PubMed, arXiv, bioRxiv, medRxiv, Semantic Scholar, and journal RSS feeds
- **AI-Powered Summarization**: Generate concise, accessible summaries using OpenAI, Anthropic Claude, or local Ollama models
- **Credibility Analysis**: Multi-factor scoring system evaluating journal impact, author h-index, methodology, and more
- **Image Generation**: Create visual abstracts using Google Gemini Imagen or DALL-E 3
- **Multiple Export Formats**: HTML email, PDF, and Markdown output
- **Web Dashboard**: React-based interface for configuration, preview, and management
- **Email Integration**: Send newsletters via SendGrid or SMTP

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Data Sources                            │
│  PubMed │ arXiv │ bioRxiv │ Semantic Scholar │ RSS Feeds   │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  Python Backend (FastAPI)                   │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐  │
│  │Fetchers │→│ Parser   │→│Credibility│→│ AI Summarizer │  │
│  └─────────┘ └──────────┘ └──────────┘ └────────────────┘  │
│                                              │              │
│                                    ┌─────────▼─────────┐   │
│                                    │ Image Generator   │   │
│                                    └─────────┬─────────┘   │
│                                              │              │
│  ┌──────────────────────────────────────────▼───────────┐  │
│  │             Newsletter Composers                      │  │
│  │         HTML │ PDF │ Markdown │ Email                │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              React Frontend Dashboard                       │
│    Papers │ Digests │ Fetch │ Settings │ Preview           │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+

### Using Docker Compose (Recommended)

1. Clone the repository and set up environment:

```bash
cd "PPT NEWS FEED"

# Copy and configure environment variables
cp backend/env.example backend/.env
# Edit backend/.env with your API keys
```

2. Start all services:

```bash
docker-compose up -d
```

3. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Manual Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp env.example .env
# Edit .env with your API keys

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Configuration

### Required API Keys

| Provider | Key | Required For |
|----------|-----|-------------|
| OpenAI | `OPENAI_API_KEY` | GPT summarization, DALL-E images |
| Google | `GOOGLE_API_KEY` | Gemini Imagen image generation |
| Anthropic | `ANTHROPIC_API_KEY` | Claude summarization (optional) |
| Semantic Scholar | `SEMANTIC_SCHOLAR_API_KEY` | Enhanced citation data (optional) |
| SendGrid | `SENDGRID_API_KEY` | Email delivery (optional) |

### Credibility Scoring Weights

Default weights (adjustable in Settings):

| Factor | Weight | Description |
|--------|--------|-------------|
| Journal Impact Factor | 25% | Based on journal ranking |
| Author H-Index | 15% | Publication history of authors |
| Sample Size | 20% | Study participant count |
| Methodology Quality | 20% | Study design (RCT, meta-analysis, etc.) |
| Peer Review Status | 10% | Published vs. preprint |
| Citation Velocity | 10% | Citations per month |

## Usage

### 1. Fetch Papers

Navigate to "Fetch Papers" to collect recent research from selected sources:

- Select data sources (PubMed, arXiv, etc.)
- Optionally add search keywords
- Set time range and max results
- Click "Start Fetch"

### 2. Browse & Select Papers

In "Papers", browse fetched papers with filtering options:

- Filter by source, credibility score, date
- Search by title/abstract
- Select papers for digest creation

### 3. Create Digest

Select papers and click "Create Digest":

- Name your digest
- AI generates summaries, credibility analysis, and images
- Processing happens in background

### 4. Export Newsletter

Open a completed digest to:

- Preview the formatted newsletter
- Export as HTML, PDF, or Markdown
- Send directly via email

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/papers/` | GET | List papers with filters |
| `/api/v1/fetch/` | POST | Start paper fetch operation |
| `/api/v1/digests/` | GET, POST | List/create digests |
| `/api/v1/digests/{id}` | GET | Get digest with papers |
| `/api/v1/newsletters/{id}/export` | POST | Export as HTML/PDF/Markdown |
| `/api/v1/newsletters/{id}/send` | POST | Send via email |
| `/api/v1/settings/` | GET, PUT | Application settings |

## Project Structure

```
ppt-news-feed/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routes
│   │   ├── fetchers/         # Source-specific fetchers
│   │   ├── analysis/         # Credibility scoring
│   │   ├── ai/               # LLM & image generation
│   │   │   └── providers/    # OpenAI, Claude, Ollama
│   │   ├── composers/        # Newsletter formatters
│   │   ├── models/           # SQLAlchemy models
│   │   ├── services/         # Business logic
│   │   └── core/             # Config, database
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   └── api/              # API client
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Tech Stack

**Backend:**
- Python 3.11+
- FastAPI
- SQLAlchemy + PostgreSQL
- Celery + Redis
- OpenAI, Anthropic, Ollama SDKs

**Frontend:**
- React 18 + TypeScript
- Vite
- TanStack Query
- Tailwind CSS

## License

MIT
