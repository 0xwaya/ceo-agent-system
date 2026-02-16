# CEO Executive Agent - Test Suite

## Running Tests

### Install Test Dependencies
```bash
pip3 install -r tests/requirements.txt
```

### Run All Tests
```bash
pytest tests/ -v
```

### Run with Coverage Report
```bash
pytest tests/ --cov=. --cov-report=html
```

### Run Specific Test File
```bash
pytest tests/test_api_endpoints.py -v
```

### Run Specific Test Class
```bash
pytest tests/test_api_endpoints.py::TestAPIEndpoints -v
```

### Run Specific Test Function
```bash
pytest tests/test_api_endpoints.py::TestAPIEndpoints::test_index_route -v
```

## Test Structure

- `conftest.py` - Pytest configuration and fixtures
- `test_api_endpoints.py` - API endpoint tests
- `test_agents.py` - Agent module tests
- `test_integration.py` - Integration and SocketIO tests

## Test Categories

### Unit Tests
- API endpoints (`test_api_endpoints.py`)
- Agent modules (`test_agents.py`)
- Validation functions
- Guard rails
- Logging

### Integration Tests
- Full orchestration workflow
- Agent execution flow
- SocketIO events (`test_integration.py`)

### Security Tests
- XSS prevention
- SQL injection prevention
- Input sanitization
- Content type validation

### Optional Voice Tests
- `test_voice_free.py` requires Google Cloud speech/TTS packages.
- If `google-cloud-speech` / `google-cloud-texttospeech` are not installed, pytest auto-skips this test.
- Install optional voice dependencies to run it end-to-end.

## Coverage Goals

- **Overall Coverage:** 80%+
- **Critical Paths:** 95%+
  - API endpoints
  - Agent execution
  - Validation/sanitization

## Continuous Integration

### GitHub Actions Example
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r tests/requirements.txt
      - name: Run tests
        run: pytest tests/ --cov=. --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Test Data

See `conftest.py` for fixtures:
- `sample_company_info` - Test company data
- `sample_agent_request` - Test agent request
- `mock_agent_response` - Mock agent response

## Best Practices

1. **Isolation** - Each test should be independent
2. **Fixtures** - Use fixtures for common setup
3. **Assertions** - Clear, specific assertions
4. **Mocking** - Mock external dependencies
5. **Coverage** - Aim for high test coverage
6. **Speed** - Keep tests fast
7. **Naming** - Descriptive test names

## Common Issues

### Import Errors
If you get import errors, ensure the project root is in Python path:
```python
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))
```

### Database Tests
Mock database calls or use temporary test database.

### Async Tests
Use `pytest-asyncio` for async test functions:
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result == expected
```

## Next Steps

1. Run tests: `pytest tests/ -v`
2. Check coverage: `pytest tests/ --cov=.`
3. Fix failing tests
4. Add more tests for uncovered code
5. Set up CI/CD pipeline
