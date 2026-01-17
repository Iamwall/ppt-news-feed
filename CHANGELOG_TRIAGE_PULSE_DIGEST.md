# Changelog: Triage Agent, Daily Digest & Live Pulse Features

## Summary

Three major features have been implemented to transform PPT NEWS FEED into a professional news platform:

1. **Triage Agent** - AI-powered pre-filter using cheap/fast models
2. **Daily Digest Mode** - Automated scheduled digest generation with topic clustering
3. **Live Pulse Mode** - Real-time feed with breaking news detection

All features maintain **full backward compatibility** with existing functionality.

---

## Files Changed

### Backend - Models

| File | Status | Description |
|------|--------|-------------|
| `backend/app/models/paper.py` | Modified | Added triage fields (triage_status, triage_score, triage_reason, triage_model, triaged_at) and breaking news fields (is_breaking, breaking_score, breaking_keywords, published_at, freshness_score) |
| `backend/app/models/digest_schedule.py` | **NEW** | DigestSchedule model for cron-based automated digest generation, ScheduledDigest for history tracking |
| `backend/app/models/topic_cluster.py` | **NEW** | TopicCluster model for grouping papers by topic, cluster_papers association table |
| `backend/app/models/__init__.py` | Modified | Added exports for new models |

### Backend - Services

| File | Status | Description |
|------|--------|-------------|
| `backend/app/services/triage_service.py` | **NEW** | TriageService for AI-powered content filtering with fast/cheap models |
| `backend/app/services/scheduler_service.py` | **NEW** | DigestScheduler with APScheduler for cron-based digest generation |
| `backend/app/services/breaking_detector.py` | **NEW** | BreakingNewsDetector for detecting urgent/breaking news based on keywords and recency |
| `backend/app/services/live_pulse_service.py` | **NEW** | LivePulseService for real-time feed management with freshness scoring |
| `backend/app/services/fetch_service.py` | Modified | Integrated optional triage step during fetch (disabled by default) |

### Backend - AI

| File | Status | Description |
|------|--------|-------------|
| `backend/app/ai/topic_clusterer.py` | **NEW** | TopicClusterer for AI-powered topic grouping and "Top N" story selection |

### Backend - API

| File | Status | Description |
|------|--------|-------------|
| `backend/app/api/schedules.py` | **NEW** | CRUD endpoints for digest schedules, run-now trigger, history |
| `backend/app/api/pulse.py` | **NEW** | Live feed endpoints (feed, breaking, stats, refresh, new items) |
| `backend/app/api/websocket.py` | **NEW** | WebSocket endpoints for real-time updates |
| `backend/app/api/fetch.py` | Modified | Added optional triage parameters (enable_triage, triage_provider, triage_model) |
| `backend/app/api/__init__.py` | Modified | Registered new routers (schedules, pulse, websocket) |

### Backend - Schemas

| File | Status | Description |
|------|--------|-------------|
| `backend/app/models/schemas.py` | Modified | Added triage options to FetchRequest (enable_triage, triage_provider, triage_model) |

### Frontend - Pages

| File | Status | Description |
|------|--------|-------------|
| `frontend/src/pages/Schedules.tsx` | **NEW** | Schedule management UI with create, edit, toggle, run-now, history |
| `frontend/src/pages/LivePulse.tsx` | **NEW** | Real-time feed UI with breaking news banner, stats, auto-refresh |

### Frontend - Routing & Navigation

| File | Status | Description |
|------|--------|-------------|
| `frontend/src/App.tsx` | Modified | Added routes for /schedules and /pulse |
| `frontend/src/components/Layout.tsx` | Modified | Added navigation links for Live Pulse and Schedules |

---

## Database Changes

### Papers Table - New Columns

```sql
-- Triage fields
published_at DATETIME
triage_status VARCHAR(20) DEFAULT 'pending'  -- pending/passed/rejected
triage_score FLOAT                           -- 0.0-1.0 confidence
triage_reason TEXT                           -- Why passed/rejected
triage_model VARCHAR(50)                     -- Model used
triaged_at DATETIME

-- Breaking news fields
is_breaking BOOLEAN DEFAULT 0
breaking_score FLOAT                         -- 0.0-1.0 urgency
breaking_keywords JSON                       -- Detected trigger words
freshness_score FLOAT                        -- Time-decay score
```

### New Tables

```sql
-- Scheduled digest configuration
CREATE TABLE digest_schedules (
    id INTEGER PRIMARY KEY,
    domain_id VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    cron_expression VARCHAR(100) NOT NULL,
    timezone VARCHAR(50) DEFAULT 'UTC',
    is_active BOOLEAN DEFAULT 1,
    lookback_hours INTEGER DEFAULT 24,
    max_items INTEGER DEFAULT 10,
    top_picks_count INTEGER DEFAULT 3,
    cluster_topics BOOLEAN DEFAULT 1,
    min_triage_score FLOAT DEFAULT 0.3,
    only_passed_triage BOOLEAN DEFAULT 1,
    ai_provider VARCHAR(50) DEFAULT 'gemini',
    ai_model VARCHAR(100),
    last_run_at DATETIME,
    next_run_at DATETIME,
    run_count INTEGER DEFAULT 0,
    last_error TEXT,
    created_at DATETIME,
    updated_at DATETIME
);

-- History of scheduled digests
CREATE TABLE scheduled_digests (
    id INTEGER PRIMARY KEY,
    schedule_id INTEGER REFERENCES digest_schedules(id),
    digest_id INTEGER REFERENCES digests(id),
    papers_considered INTEGER DEFAULT 0,
    papers_included INTEGER DEFAULT 0,
    topics_clustered INTEGER DEFAULT 0,
    triggered_at DATETIME,
    completed_at DATETIME,
    generation_time_seconds FLOAT
);

-- Topic clusters for grouping papers
CREATE TABLE topic_clusters (
    id INTEGER PRIMARY KEY,
    digest_id INTEGER REFERENCES digests(id),
    domain_id VARCHAR(50),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    keywords TEXT,
    display_order INTEGER DEFAULT 0,
    is_top_pick BOOLEAN DEFAULT 0,
    paper_count INTEGER DEFAULT 0,
    importance_score FLOAT,
    created_at DATETIME
);

-- Many-to-many: clusters to papers
CREATE TABLE cluster_papers (
    cluster_id INTEGER REFERENCES topic_clusters(id),
    paper_id INTEGER REFERENCES papers(id),
    relevance_score FLOAT DEFAULT 1.0,
    display_order INTEGER DEFAULT 0,
    PRIMARY KEY (cluster_id, paper_id)
);
```

---

## API Endpoints

### Schedules API (`/api/schedules/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/schedules/` | List all schedules (filter by domain_id, active_only) |
| GET | `/schedules/{id}` | Get specific schedule |
| POST | `/schedules/` | Create new schedule |
| PUT | `/schedules/{id}` | Update schedule |
| DELETE | `/schedules/{id}` | Delete schedule |
| POST | `/schedules/{id}/run-now` | Manually trigger schedule |
| POST | `/schedules/{id}/toggle` | Toggle active status |
| GET | `/schedules/{id}/history` | Get generation history |
| GET | `/schedules/status/scheduler` | Get scheduler status |

### Pulse API (`/api/pulse/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/pulse/feed` | Get live feed (sorted by breaking + freshness) |
| GET | `/pulse/breaking` | Get breaking news only |
| GET | `/pulse/stats` | Get feed statistics |
| POST | `/pulse/refresh` | Refresh breaking/freshness scores |
| GET | `/pulse/new` | Get items since timestamp (for polling) |
| POST | `/pulse/analyze/{paper_id}` | Analyze specific paper |

### WebSocket Endpoints

| Endpoint | Description |
|----------|-------------|
| `/ws/pulse` | Global live updates |
| `/ws/pulse/{domain_id}` | Domain-specific updates |
| GET `/ws/status` | Connection status |

### Fetch API (Modified)

New optional parameters in `POST /api/fetch/`:

```json
{
  "sources": ["pubmed", "arxiv"],
  "keywords": ["AI", "machine learning"],
  "max_results": 50,
  "days_back": 7,
  "enable_triage": false,          // NEW: Enable AI triage (default: false)
  "triage_provider": "openai",     // NEW: AI provider for triage
  "triage_model": "gpt-4o-mini"    // NEW: Specific model (optional)
}
```

---

## Backward Compatibility

All new features are **opt-in** and disabled by default:

1. **Triage** - Only runs if `enable_triage: true` in fetch request
2. **Scheduled Digests** - Separate from manual digest creation
3. **Live Pulse** - New page, doesn't affect existing digest workflow
4. **Breaking Detection** - Papers still work without breaking analysis

Existing functionality remains unchanged:
- Manual digest creation
- Newsletter preview/export
- Paper fetching (without triage)
- Domain switching
- All existing API endpoints

---

## Dependencies

### Backend (requirements.txt)

```
apscheduler>=3.10.0  # For scheduled digest generation (optional)
```

### Frontend (package.json)

No new dependencies required. Uses existing:
- react-query for data fetching
- lucide-react for icons
- tailwindcss for styling

---

## Feature Details

### 1. Triage Agent

**Purpose**: Filter noise before expensive AI processing.

**How it works**:
1. Fast model (GPT-4o-mini, Claude Haiku) evaluates each paper
2. Asks: Is this actual news? Is it relevant? What's the quality?
3. Marks papers as `passed` or `rejected`
4. Rejected papers are still saved but filtered from digests

**Cost**: ~$2.74/year for 100 articles/day

### 2. Daily Digest Mode

**Purpose**: Automated morning briefings.

**How it works**:
1. Create schedule with cron expression (e.g., "0 6 * * *" for 6 AM)
2. Scheduler triggers at specified times
3. Fetches papers from lookback period
4. AI clusters papers into topics
5. Picks "Top N" stories
6. Creates digest automatically

**Features**:
- Cron-based scheduling
- Topic clustering with AI
- Top picks selection
- History tracking
- Manual "Run Now" trigger

### 3. Live Pulse Mode

**Purpose**: Real-time feed like Twitter but high signal-to-noise.

**How it works**:
1. Papers are analyzed for breaking news keywords
2. Freshness score decays over time (24-hour half-life)
3. Feed sorted by: breaking status > breaking score > freshness
4. WebSocket for real-time updates
5. Breaking news banner for urgent items

**Breaking Keywords by Domain**:
- News: "breaking", "just in", "urgent", "developing"
- Business: "crash", "surge", "bankruptcy", "fed"
- Tech: "leak", "breach", "hack", "outage"
- Health: "outbreak", "pandemic", "emergency"
- Science: "discovery", "breakthrough", "retraction"

---

## Usage Examples

### Enable Triage During Fetch

```bash
curl -X POST http://localhost:8000/api/fetch/ \
  -H "Content-Type: application/json" \
  -d '{
    "sources": ["arxiv", "pubmed"],
    "max_results": 50,
    "enable_triage": true,
    "triage_provider": "openai"
  }'
```

### Create a Schedule

```bash
curl -X POST http://localhost:8000/api/schedules/ \
  -H "Content-Type: application/json" \
  -d '{
    "domain_id": "tech",
    "name": "Morning Tech Briefing",
    "cron_expression": "0 6 * * *",
    "lookback_hours": 24,
    "max_items": 10,
    "top_picks_count": 3
  }'
```

### Get Live Feed

```bash
curl "http://localhost:8000/api/pulse/feed?limit=50&breaking_only=false"
```

### Connect to WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/pulse/tech');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'breaking') {
    alert(`BREAKING: ${data.data.title}`);
  }
};
```

---

## Testing Checklist

### Triage Agent
- [ ] Fetch with triage enabled filters ~30-60% as noise
- [ ] triage_status correctly set on all papers
- [ ] Rejected papers don't appear in digests by default

### Daily Digest
- [ ] Create schedule with cron expression
- [ ] Manual "Run Now" creates digest
- [ ] Topic clustering groups related articles
- [ ] "Top 3" selection highlights important stories
- [ ] History shows past runs

### Live Pulse
- [ ] Feed shows papers sorted by breaking + freshness
- [ ] Breaking news banner appears for urgent items
- [ ] Auto-refresh updates feed every 30 seconds
- [ ] Freshness scores decay over time
- [ ] Keywords detected correctly per domain
