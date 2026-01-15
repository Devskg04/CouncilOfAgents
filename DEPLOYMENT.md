# AETHER Free Local Multi-Agent Deployment

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- No other dependencies needed!

### Start All Services
```bash
# Build and start all agent services
docker-compose -f docker-compose.agents.yml up --build

# Run in background
docker-compose -f docker-compose.agents.yml up -d

# View logs
docker-compose -f docker-compose.agents.yml logs -f

# View specific agent logs
docker-compose -f docker-compose.agents.yml logs -f factor-agent
```

### Scale Agents
```bash
# Scale factor agent to 3 instances
docker-compose -f docker-compose.agents.yml up --scale factor-agent=3

# Scale critic agent to 2 instances
docker-compose -f docker-compose.agents.yml up --scale critic-agent=2
```

### Stop Services
```bash
# Stop all services
docker-compose -f docker-compose.agents.yml down

# Stop and remove volumes
docker-compose -f docker-compose.agents.yml down -v
```

### Health Checks
```bash
# Check orchestrator health
curl http://localhost:8000/health

# Check factor agent health
curl http://localhost:8001/health

# Check metrics
curl http://localhost:8000/metrics
```

## Architecture

### Services
- **Orchestrator** (port 8000) - Coordinates agent workflow
- **Factor Agent** (port 8001) - Extracts factors
- **Supporting Agent** (port 8002) - Generates supporting arguments
- **Critic Agent** (port 8003) - Provides counter-arguments
- **Synthesizer Agent** (port 8004) - Synthesizes debate results
- **Final Decision Agent** (port 8005) - Generates final report

### Shared Resources
- **SQLite Databases** - Stored in `./data` directory
  - `message_bus.db` - Message history
  - `state.db` - Agent state and outputs
- **Logs** - Stored in `./logs` directory (JSON format)

### Communication
- **In-memory message bus** - Async pub/sub within containers
- **SQLite persistence** - Shared via Docker volumes
- **Zero external dependencies** - Everything runs locally

## Development

### Run Single Agent
```bash
# Run factor agent only
docker-compose -f docker-compose.agents.yml up factor-agent

# Restart single agent
docker-compose -f docker-compose.agents.yml restart critic-agent
```

### View Database
```bash
# Access SQLite database
sqlite3 ./data/message_bus.db

# Query messages
SELECT * FROM messages ORDER BY created_at DESC LIMIT 10;

# Query state
sqlite3 ./data/state.db
SELECT * FROM factors;
```

### Debug
```bash
# Exec into container
docker exec -it aether-orchestrator /bin/bash

# View logs in real-time
docker-compose -f docker-compose.agents.yml logs -f --tail=100
```

## Cost Analysis

| Component | Traditional | Free Architecture |
|-----------|------------|-------------------|
| Message Broker | RabbitMQ ($$$) | In-memory + SQLite ($0) |
| State Store | Redis ($$$) | SQLite ($0) |
| Orchestration | Kubernetes ($$$) | Docker Compose ($0) |
| Monitoring | Prometheus/Grafana ($) | JSON logs + /metrics ($0) |
| **Total** | **$$$** | **$0** |

## Production Deployment

### Self-Hosted Server
```bash
# Same commands work on any server with Docker
# No cloud provider needed
# No managed services required
```

### Resource Limits
Add to docker-compose.agents.yml:
```yaml
services:
  factor-agent:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
```

### Persistent Volumes
Data persists in `./data` directory
Backup with:
```bash
tar -czf aether-backup.tar.gz ./data
```

## Troubleshooting

### Agent Not Starting
```bash
# Check logs
docker-compose -f docker-compose.agents.yml logs agent-name

# Check health
curl http://localhost:PORT/health
```

### Database Locked
```bash
# Stop all services
docker-compose -f docker-compose.agents.yml down

# Remove lock files
rm ./data/*.db-shm ./data/*.db-wal

# Restart
docker-compose -f docker-compose.agents.yml up
```

### Performance Issues
```bash
# Scale agents
docker-compose -f docker-compose.agents.yml up --scale factor-agent=2

# Check metrics
curl http://localhost:8001/metrics
```
