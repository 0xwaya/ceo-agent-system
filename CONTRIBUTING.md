# Contributing to CEO Agent System

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Help maintain a positive community

## Getting Started

### 1. Fork the Repository

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/ceo-agent-system.git
cd ceo-agent-system
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Copy environment template
cp .env.example .env

# Edit .env with your settings
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

## Development Workflow

### Code Style

We follow Python best practices:

- **PEP 8** style guide
- **Type hints** for function signatures
- **Docstrings** for all modules, classes, and functions
- **Black** for code formatting (line length: 100)
- **Flake8** for linting
- **Mypy** for type checking

### Format Code

```bash
# Format code
black . --line-length 100

# Check linting
flake8 . --max-line-length=100

# Type check
mypy . --ignore-missing-imports
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_agents.py

# Run specific test
pytest tests/test_agents.py::test_cfo_agent
```

### Code Quality Checklist

- [ ] Code follows PEP 8 style guide
- [ ] All functions have docstrings
- [ ] Type hints added for function signatures
- [ ] Tests added for new features
- [ ] Tests pass locally
- [ ] No linting errors
- [ ] Documentation updated

## Commit Guidelines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

### Examples

```bash
git commit -m "feat(agents): add new marketing agent capabilities"
git commit -m "fix(api): resolve rate limiting issue in /api/execute"
git commit -m "docs(readme): update installation instructions"
```

## Pull Request Process

### 1. Before Submitting

- [ ] Code is formatted with Black
- [ ] All tests pass
- [ ] No linting errors
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)

### 2. Create Pull Request

1. Push your branch to your fork
2. Open a pull request against `main` branch
3. Fill out the PR template
4. Link related issues

### 3. PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests added/updated
- [ ] All tests passing
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
```

### 4. Review Process

- Maintainers will review within 3-5 business days
- Address feedback and update PR
- Squash commits before merging (if requested)

## Project Structure

```
ceo-agent-system/
├── agents/          # Agent implementations
├── services/        # Business logic services
├── utils/           # Utility modules
├── static/          # Frontend assets
├── templates/       # HTML templates
├── tests/           # Test suite
├── docs/            # Additional documentation
├── app.py           # Main Flask application
├── config.py        # Configuration management
└── models.py        # Data models
```

## Areas for Contribution

### High Priority

- [ ] Additional agent types (Sales, HR, Operations)
- [ ] Database persistence (SQLAlchemy integration)
- [ ] Async agent execution
- [ ] API authentication (JWT implementation)
- [ ] Enhanced testing coverage (>80%)

### Medium Priority

- [ ] Admin dashboard improvements
- [ ] Real-time monitoring metrics
- [ ] Export functionality (PDF reports)
- [ ] Multi-language support
- [ ] Performance optimizations

### Documentation

- [ ] API documentation (Swagger/OpenAPI)
- [ ] Deployment guides (Docker, K8s)
- [ ] Video tutorials
- [ ] Use case examples
- [ ] Architecture diagrams

## Questions or Help?

- Open an issue with `question` label
- Check existing issues and discussions
- Review documentation in `/docs`

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
