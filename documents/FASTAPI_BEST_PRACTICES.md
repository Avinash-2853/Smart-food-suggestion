# FastAPI Best Practices - Implementation Guide

This document outlines FastAPI best practices implemented in the NextGen Catering Platform.

## ✅ Implemented Best Practices

### 1. Project Structure

**✅ Proper Layered Architecture:**
```
app/
├── api/              # API layer (routers, endpoints)
│   └── v1/          # API versioning
│       ├── endpoints/
│       └── router.py
├── core/             # Core components (dependencies, config)
├── schemas/          # Pydantic models (request/response)
├── services/         # Business logic layer
├── repositories/     # Data access layer
├── models/           # SQLAlchemy models
└── main.py           # Application entry point
```

**Benefits:**
- Clear separation of concerns
- Easy to test each layer independently
- Scalable and maintainable

### 2. Dependency Injection

**✅ FastAPI Dependencies:**
```python
# app/core/dependencies.py
async def get_database() -> AsyncSession:
    """Dependency for database session."""
    async for session in get_db():
        yield session

DatabaseDep = Annotated[AsyncSession, Depends(get_database)]

async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> dict:
    """Dependency for authenticated user."""
    # JWT validation logic
    return payload
```

**Usage:**
```python
@app.get("/users/me")
async def get_current_user_profile(
    user: CurrentUser,
    db: DatabaseDep,
):
    """Get current user profile."""
    # user and db are injected automatically
    pass
```

**Benefits:**
- Testable (can mock dependencies)
- Reusable across endpoints
- Type-safe

### 3. API Versioning

**✅ URL-based Versioning:**
```python
# app/api/v1/router.py
api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# app/main.py
app.include_router(api_router, prefix="/api/v1")
```

**Benefits:**
- Clear API versioning
- Backward compatibility
- Easy to add v2 later

### 4. Request/Response Validation

**✅ Pydantic Schemas:**
```python
# app/schemas/user.py
class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=1, max_length=100)

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    name: str
    created_at: datetime
```

**Usage:**
```python
@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: CreateUserRequest,
    db: DatabaseDep,
):
    """Create new user."""
    # user_data is automatically validated
    pass
```

**Benefits:**
- Automatic validation
- Type safety
- OpenAPI documentation

### 5. Error Handling

**✅ Custom Exception Handlers:**
```python
# app/main.py
@app.exception_handler(NextGenCaterException)
async def nextgencater_exception_handler(request, exc):
    """Handle custom exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.message},
    )
```

**Benefits:**
- Consistent error responses
- Proper HTTP status codes
- Detailed error logging

### 6. Structured Logging

**✅ JSON Logging:**
```python
from shared.common.logger import get_logger

logger = get_logger(__name__)

logger.info(
    "user_created",
    user_id=user.id,
    email=user.email,
    request_id=request.state.request_id,
)
```

**Benefits:**
- Machine-readable logs
- Easy to query and analyze
- Correlation IDs for tracing

### 7. Health Checks

**✅ Health and Readiness Endpoints:**
```python
@router.get("/health")
async def health_check():
    """Basic health check."""
    return {"status": "healthy"}

@router.get("/ready")
async def readiness_check():
    """Readiness check - verifies dependencies."""
    # Check database, Redis, etc.
    return {"status": "ready", "checks": {...}}
```

**Benefits:**
- Kubernetes/Docker health checks
- Load balancer health checks
- Dependency verification

### 8. Async/Await

**✅ Async I/O:**
```python
@router.get("/users/{user_id}")
async def get_user(user_id: UUID, db: DatabaseDep):
    """Get user by ID."""
    # Async database query
    user = await db.get(User, user_id)
    return user
```

**Benefits:**
- High concurrency
- Non-blocking I/O
- Better performance

### 9. OpenAPI Documentation

**✅ Automatic Documentation:**
- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

**Enhancements:**
```python
app = FastAPI(
    title="Identity Service",
    description="User identity and authentication service",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)
```

### 10. Middleware

**✅ Request ID and Logging:**
```python
app.add_middleware(RequestIDMiddleware)  # Add request ID
app.add_middleware(LoggingMiddleware)    # Log requests
app.add_middleware(CORSMiddleware)       # CORS
```

**Benefits:**
- Request tracing
- Automatic logging
- CORS handling

## 📋 Checklist for New Services

When creating a new service, ensure:

- [ ] Proper project structure (api/, core/, schemas/, services/, repositories/)
- [ ] Dependency injection for database, auth, etc.
- [ ] API versioning (/api/v1/)
- [ ] Pydantic schemas for all requests/responses
- [ ] Custom exception handlers
- [ ] Structured logging
- [ ] Health and readiness checks
- [ ] Async/await for I/O operations
- [ ] OpenAPI documentation
- [ ] Middleware configured
- [ ] Type hints throughout
- [ ] Error handling
- [ ] Unit tests
- [ ] Integration tests

## 🔗 References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)
- [TECH_GUIDELINES.md](../../TECH_GUIDELINES.md)
- [Developer Guidelines](../developer-guidelines.md)
- [System Design Guidelines](system-design-guidelines.md)

