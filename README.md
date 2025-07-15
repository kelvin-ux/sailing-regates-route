# ⛵ Sailing Route Optimizer

An intelligent sailing route planning system optimized for competitive sailors and recreational boaters. Calculates optimal routes considering weather conditions, marine obstacles, and vessel characteristics.

## 🌟 Features

- **🧭 Smart Route Planning** - Advanced pathfinding algorithms with real-time weather data
- **🌊 Live Weather Data** - Integration with OpenWeatherMap API
- **⚓ Obstacle Management** - Database of marine obstacles and restricted areas
- **🚤 Vessel Profiles** - Customizable polar characteristics configuration
- **📊 Performance Analytics** - Detailed route statistics and estimated times
- **🗺️ Interactive Interface** - Web map with route visualization and weather data
- **📱 Responsive Design** - Compatible with mobile devices and tablets

## 🏗️ Architecture

### Backend (FastAPI + Python)
- **REST API** with automatic documentation (OpenAPI/Swagger)
- **PostgreSQL database** with PostGIS extension for geospatial data
- **Redis cache** for performance optimization
- **Routing algorithms** based on A* and Dijkstra
- **Weather integration** with multiple data sources

### Frontend (React + TypeScript)
- **Modern interface** built with React 18 and TypeScript
- **Interactive maps** using Leaflet
- **UI components** with Chakra UI
- **State management** with React Query
- **Responsive design** with CSS Grid and Flexbox

### Infrastructure
- **Complete containerization** with Docker and Docker Compose
- **PostgreSQL 15 database** with PostGIS for geospatial data
- **Redis cache** for sessions and temporary data
- **Nginx** as reverse proxy and static file server

## 🚀 Installation and Setup

### Prerequisites

- **Docker Desktop** (Mac/Windows) or **Docker Engine** (Linux)
- **Docker Compose** v2.0+
- **Git**
- At least **4GB RAM** available
- **5GB** free disk space

### Quick Installation

1. **Configure environment variables:**
```bash
cat > .env << 'EOF'
OPENWEATHER_API_KEY=your_api_key_here
DEBUG=True
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=sailing_routes
EOF
```

1. **Start services step by step:**
```bash
# Database
docker-compose up -d db
sleep 30

# Cache
docker-compose up -d redis

# Backend API
docker-compose up -d backend
sleep 60

# Frontend
docker-compose up -d frontend
```

2. **Verify installation:**
```bash
curl http://localhost:8000/health
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENWEATHER_API_KEY` | OpenWeatherMap API key | `demo_key` |
| `DATABASE_URL` | PostgreSQL connection URL | Auto-generated |
| `REDIS_URL` | Redis connection URL | `redis://redis:6379` |
| `DEBUG` | Debug mode | `True` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `localhost:3000` |

### OpenWeatherMap API Key

1. Sign up at [OpenWeatherMap](https://openweathermap.org/api)
2. Get your free API key
3. Add it to the `.env` file:
```bash
OPENWEATHER_API_KEY=your_real_api_key_here
```

## 🖥️ Usage

### Application Access

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:3000 | Main interface |
| **API Backend** | http://localhost:8000 | REST API |
| **API Documentation** | http://localhost:8000/docs | Swagger UI |
| **Health Check** | http://localhost:8000/health | System status |

### Main Features

#### 1. Calculate Optimal Route
```bash
# Example with curl
curl -X POST "http://localhost:8000/api/v1/routes/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "start": {"lat": 54.52, "lon": 18.55},
    "end": {"lat": 54.48, "lon": 18.65},
    "grid_resolution_nm": 0.5,
    "use_weather_routing": true
  }'
```

#### 2. Export Route to GPX
```bash
curl "http://localhost:8000/api/v1/routes/{route_id}/gpx" \
  -o optimized_route.gpx
```

#### 3. Query Weather Data
```bash
curl "http://localhost:8000/api/v1/weather?north=54.8&south=54.3&east=19.0&west=18.3"
```

## 🛠️ Development

### Project Structure

```
sailing-regates-route/
├── docker-compose.yml          # Services configuration
├── .env                        # Environment variables
├── route-planning/
│   ├── app/                    # FastAPI Backend
│   │   ├── app/
│   │   │   ├── api/           # API endpoints
│   │   │   ├── core/          # Business logic
│   │   │   ├── db/            # Models and CRUD
│   │   │   ├── schemas/       # Pydantic schemas
│   │   │   └── services/      # Application services
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── frontend/              # React Frontend
│       ├── src/
│       │   ├── components/    # React components
│       │   ├── hooks/         # Custom hooks
│       │   ├── services/      # API clients
│       │   └── types/         # TypeScript types
│       ├── package.json
│       └── Dockerfile
├── nginx/                     # Proxy configuration
├── db/                        # DB initialization scripts
└── static/                    # Static files
```

### Development Commands

```bash
# View logs in real-time
docker-compose logs -f

# Restart specific service
docker-compose restart backend

# Access backend shell
docker-compose exec backend bash

# Run tests (when implemented)
docker-compose exec backend pytest

# Rebuild with changes
docker-compose up --build -d
```

### Debugging

```bash
# Verify network connections
./diagnose.sh

# View specific service logs
docker-compose logs backend | tail -50

# Check database status
docker-compose exec db pg_isready -U postgres

# Manual connection test
docker-compose exec backend python3 -c "
import asyncpg, asyncio
async def test():
    conn = await asyncpg.connect('postgresql://postgres:password@db:5432/sailing_routes')
    print('Connection successful')
    await conn.close()
asyncio.run(test())
"
```

## 🐳 Docker

### Useful Commands

```bash
# Stop everything
docker-compose down

# Complete restart (deletes data)
docker-compose down -v
docker-compose up -d

# View resource usage
docker stats

# Clean Docker system
docker system prune -f
```

### Common Troubleshooting

#### Error: "Connection refused"
```bash
# Verify database is ready
docker-compose exec db pg_isready -U postgres

# Restart services in order
docker-compose down
docker-compose up -d db redis
sleep 30
docker-compose up -d backend frontend
```

#### Error: Platform mismatch (Mac M1/M2)
```yaml
# Add to docker-compose.yml
services:
  backend:
    platform: linux/amd64
```

#### Error: Port already in use
```bash
# Find process using the port
lsof -i :8000
sudo kill -9 <PID>
```

## 📊 API Endpoints

### Main Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/routes/calculate` | Calculate optimal route |
| `GET` | `/api/v1/routes` | List routes |
| `GET` | `/api/v1/routes/{id}` | Get specific route |
| `DELETE` | `/api/v1/routes/{id}` | Delete route |
| `GET` | `/api/v1/routes/{id}/gpx` | Export to GPX |

### Auxiliary Data

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/weather` | Weather data |
| `GET` | `/api/v1/obstacles` | Marine obstacles |
| `GET` | `/api/v1/boat-profiles` | Vessel profiles |
| `GET` | `/api/v1/statistics` | System statistics |

## 🧪 Testing

```bash
# Unit tests (backend)
docker-compose exec backend pytest

# Integration tests
docker-compose exec backend pytest tests/integration/

# API tests with curl
curl -X POST http://localhost:8000/api/v1/routes/calculate \
  -H "Content-Type: application/json" \
  -d @test_data/sample_route.json
```

## 🚀 Deployment

### Production

1. **Configure production environment variables:**
```bash
cat > .env.production << 'EOF'
DEBUG=False
OPENWEATHER_API_KEY=your_real_api_key
SECRET_KEY=very_secure_secret_key
POSTGRES_PASSWORD=secure_password
ALLOWED_ORIGINS=https://your-domain.com
EOF
```

2. **Deploy with Docker:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Security Considerations

- ✅ Change all default passwords
- ✅ Configure HTTPS with SSL certificates
- ✅ Configure firewall to limit port access
- ✅ Enable authentication if needed
- ✅ Regularly update Docker images

## 🤝 Contributing

1. **Fork the project**
2. **Create a feature branch** (`git checkout -b feature/new-feature`)
3. **Commit changes** (`git commit -am 'Add new feature'`)
4. **Push to branch** (`git push origin feature/new-feature`)
5. **Create a Pull Request**

### Code Standards

- **Backend**: Follow PEP 8 for Python
- **Frontend**: Use ESLint and Prettier
- **Commits**: Conventional Commits format
- **Testing**: Minimum 80% coverage

## 📄 License

This project is licensed under the MIT License. See `LICENSE` for more details.

## 🆘 Support

### Additional Documentation
- [API Documentation](http://localhost:8000/docs) (when app is running)
- [OpenWeatherMap API](https://openweathermap.org/api)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://reactjs.org/docs/)

### Report Issues
- Use [GitHub Issues](https://github.com/your-username/sailing-regates-route/issues)
- Include relevant logs and reproduction steps
- Specify operating system and Docker version


---

## 🎯 Roadmap

### Version 2.0
- [ ] User authentication and authorization
- [ ] Mobile device API
- [ ] Integration with more weather sources
- [ ] Machine learning for route prediction
- [ ] Multi-fleet support

### Version 1.1
- [ ] Export to KML and JSON formats
- [ ] Real-time notifications
- [ ] Performance optimization
- [ ] Complete automated tests
- [ ] Enhanced API documentation

---

**Happy sailing! ⛵**
