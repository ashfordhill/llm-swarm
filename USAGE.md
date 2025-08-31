# Usage Guide

This guide shows you how to use the LLM Swarm system to generate complete software projects.

## Basic Usage

### 1. Command Line Interface

The main interface is through the `main.py` script:

```bash
python main.py generate --spec "Your project description" --output ./my-project
```

### 2. Project Specifications

You can provide project specifications in two ways:

#### Inline Specification
```bash
python main.py generate \
  --spec "Create a REST API for a todo app with user authentication" \
  --output ./todo-api
```

#### Specification File
Create a text file with your project requirements:

```bash
# project-spec.txt
Create a web application with the following features:
- User registration and authentication
- Todo list management (CRUD operations)
- RESTful API with JSON responses
- SQLite database for data storage
- React frontend with modern UI
- Unit tests for all components
- Docker deployment configuration
- Comprehensive documentation

Technology preferences:
- Backend: Python with Flask or FastAPI
- Frontend: React with TypeScript
- Database: SQLite with SQLAlchemy ORM
- Testing: pytest for backend, Jest for frontend
```

Then run:
```bash
python main.py generate --spec project-spec.txt --output ./todo-app
```

### 3. Dry Run Mode

Before generating actual code, you can see the execution plan:

```bash
python main.py generate --spec project-spec.txt --output ./test --dry-run
```

This shows you:
- What tasks will be created
- Which agents will handle each task
- Task dependencies and execution order
- Estimated complexity

## Advanced Usage

### 1. Custom Configuration

Use a custom configuration file:

```bash
python main.py generate \
  --spec project-spec.txt \
  --output ./project \
  --config custom-config.yaml
```

### 2. Force Overwrite

Overwrite existing output directory:

```bash
python main.py generate \
  --spec project-spec.txt \
  --output ./existing-project \
  --force
```

### 3. Verbose Logging

Enable debug logging to see detailed execution:

```bash
python main.py generate \
  --spec project-spec.txt \
  --output ./project \
  --log-level DEBUG \
  --log-file generation.log
```

## Writing Effective Project Specifications

### 1. Be Specific

❌ **Bad**: "Create a web app"

✅ **Good**: "Create a task management web application with user authentication, CRUD operations for tasks, and a React frontend"

### 2. Include Technology Preferences

```
Technology Stack:
- Backend: Python with FastAPI
- Frontend: React with TypeScript
- Database: PostgreSQL
- Authentication: JWT tokens
- Deployment: Docker containers
```

### 3. Specify Features Clearly

```
Core Features:
1. User Management
   - User registration with email verification
   - Login/logout with JWT authentication
   - Password reset functionality

2. Task Management
   - Create, read, update, delete tasks
   - Task categories and tags
   - Due dates and priorities
   - Task sharing between users

3. API Requirements
   - RESTful API design
   - JSON request/response format
   - API documentation with OpenAPI/Swagger
   - Rate limiting and error handling
```

### 4. Include Quality Requirements

```
Quality Requirements:
- Unit test coverage > 80%
- Integration tests for API endpoints
- Frontend component tests
- Error handling and logging
- Input validation and sanitization
- Security best practices
- Performance optimization
```

## Understanding the Generation Process

### 1. Task Planning

The orchestrator analyzes your specification and creates tasks:

```
1. Project Setup → Backend Agent
2. Database Schema → Database Agent  
3. API Implementation → Backend Agent
4. Frontend Components → Frontend Agent
5. Authentication System → Backend Agent
6. Testing Suite → Testing Agent
7. Documentation → Documentation Agent
```

### 2. Dependency Resolution

Tasks are executed in dependency order:
- Database schema before API implementation
- API endpoints before frontend integration
- Core features before testing
- Everything before documentation

### 3. Agent Specialization

Each agent focuses on their expertise:
- **Frontend Agent**: React components, CSS, client-side logic
- **Backend Agent**: API endpoints, business logic, server setup
- **Database Agent**: Schema design, migrations, ORM models
- **Testing Agent**: Unit tests, integration tests, test utilities
- **Documentation Agent**: README, API docs, user guides

## Output Structure

Generated projects typically follow this structure:

```
my-project/
├── README.md                 # Project overview and setup
├── requirements.txt          # Python dependencies
├── package.json             # Node.js dependencies (if applicable)
├── docker-compose.yml       # Docker configuration
├── .gitignore              # Git ignore rules
├── backend/                # Backend code
│   ├── app/
│   ├── models/
│   ├── api/
│   └── tests/
├── frontend/               # Frontend code
│   ├── src/
│   ├── public/
│   └── tests/
├── database/               # Database files
│   ├── migrations/
│   └── schema.sql
├── docs/                   # Documentation
│   ├── api.md
│   └── deployment.md
└── PROJECT_SUMMARY.md      # Generation summary
```

## Managing Agents

### 1. List Available Agents

```bash
python main.py agents
```

This shows:
- Agent names and types
- Enabled/disabled status
- Model configurations
- Capabilities

### 2. Configure Agents

Edit `models/config.yaml` to customize agents:

```yaml
agents:
  frontend:
    enabled: true
    model: "local_coder"
    max_retries: 3
  
  backend:
    enabled: true
    model: "local_coder"
    max_retries: 3
  
  testing:
    enabled: false  # Disable if not needed
```

### 3. Agent-Specific Instructions

You can provide agent-specific guidance in your specification:

```
Frontend Requirements:
- Use React with functional components and hooks
- Implement responsive design with CSS Grid
- Use Material-UI for component library
- Include loading states and error handling

Backend Requirements:
- Use FastAPI with async/await patterns
- Implement proper error handling and logging
- Use Pydantic for request/response validation
- Include API versioning (v1 prefix)

Database Requirements:
- Use PostgreSQL with SQLAlchemy ORM
- Implement proper indexing for performance
- Include database migrations
- Use connection pooling
```

## Configuration Management

### 1. Validate Configuration

```bash
python main.py config --validate
```

### 2. Create Default Configuration

```bash
python main.py config --create-default
```

### 3. View Configuration

```bash
python main.py config
```

## Tips and Best Practices

### 1. Start Small

Begin with simple projects to understand the system:

```
Create a simple Python CLI tool that:
- Takes user input
- Processes the input
- Saves results to a file
- Includes basic error handling
- Has unit tests
```

### 2. Iterate and Refine

Use dry-run mode to refine your specifications:

1. Write initial specification
2. Run dry-run to see planned tasks
3. Adjust specification if needed
4. Generate the project

### 3. Review Generated Code

Always review the generated code:
- Check for security issues
- Verify business logic
- Test functionality
- Customize as needed

### 4. Use Version Control

Initialize git in generated projects:

```bash
cd generated-project
git init
git add .
git commit -m "Initial generated code"
```

### 5. Customize After Generation

The generated code is a starting point:
- Add custom business logic
- Integrate with external services
- Customize UI/UX
- Add additional features

## Troubleshooting

### 1. Generation Fails

- Check the logs for detailed error messages
- Validate your configuration
- Ensure API keys are set correctly
- Try a simpler specification first

### 2. Poor Code Quality

- Provide more detailed specifications
- Include quality requirements
- Review and customize generated code
- Consider using better models

### 3. Missing Features

- Be more explicit in your specification
- Check if relevant agents are enabled
- Add feature-specific requirements
- Generate additional components manually

### 4. Performance Issues

- Use local models for faster generation
- Enable model quantization
- Reduce specification complexity
- Run on machines with more resources

## Examples

Check the `examples/` directory for sample specifications and generated projects:

- `examples/todo-app/` - Complete web application
- `examples/cli-tool/` - Simple command-line utility
- `examples/api-service/` - REST API service
- `examples/data-pipeline/` - Data processing pipeline

Each example includes:
- Original specification
- Generated code
- Customization notes
- Deployment instructions