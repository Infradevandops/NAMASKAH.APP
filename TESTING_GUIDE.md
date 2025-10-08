# 🧪 Testing Guide - Namaskah.App

## Overview
Comprehensive testing strategy covering unit tests, integration tests, performance tests, and security tests.

## Test Structure

```
tests/
├── conftest.py                 # Test configuration and fixtures
├── test_comprehensive_api.py   # Complete API test suite
├── test_performance.py         # Performance and load tests
├── test_security.py           # Security testing suite
├── test_error_handling.py     # Error handling tests
└── test_*.py                  # Individual component tests
```

## Running Tests

### Basic Test Execution
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m performance   # Performance tests only
pytest -m security      # Security tests only
```

### Test Categories

#### Unit Tests (`@pytest.mark.unit`)
- Test individual functions and classes
- Fast execution (< 1 second each)
- No external dependencies
- High coverage target (90%+)

#### Integration Tests (`@pytest.mark.integration`)
- Test component interactions
- Database operations
- API endpoint flows
- External service mocking

#### Performance Tests (`@pytest.mark.performance`)
- Response time validation
- Load testing
- Resource usage monitoring
- Benchmark comparisons

#### Security Tests (`@pytest.mark.security`)
- Authentication/authorization
- Input validation
- SQL injection protection
- XSS prevention

## Test Configuration

### Environment Variables
```bash
# Test environment setup
TESTING=true
DATABASE_URL=sqlite:///./test.db
JWT_SECRET_KEY=test-secret-key-32-chars-minimum
USE_MOCK_TWILIO=true
USE_MOCK_TEXTVERIFIED=true
LOG_LEVEL=ERROR
RATE_LIMIT_ENABLED=false
```

### Fixtures Available
- `client`: FastAPI test client
- `async_client`: Async HTTP client
- `test_db`: Isolated test database
- `test_user_data`: Sample user data
- `auth_headers`: Authentication headers
- `mock_*_client`: Mocked external services

## Performance Requirements

### Response Time Targets
- Health check: < 100ms average
- Authentication: < 500ms average
- API endpoints: < 1 second average
- Database queries: < 200ms average

### Load Testing Targets
- Concurrent users: 50+
- Requests per second: 100+
- Success rate: 95%+
- Memory usage: Stable under load

## Security Testing

### Authentication Tests
- JWT token validation
- Password strength requirements
- Session management
- Token expiration

### Authorization Tests
- Role-based access control
- Data isolation between users
- Admin endpoint protection
- Resource ownership validation

### Input Validation Tests
- SQL injection protection
- XSS prevention
- File upload validation
- Email/phone validation

## Best Practices

### Writing Tests
1. **Descriptive Names**: Use clear, descriptive test names
2. **Single Responsibility**: One assertion per test when possible
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Independent Tests**: Tests should not depend on each other
5. **Mock External Services**: Use mocks for external dependencies

### Test Data Management
1. **Use Fixtures**: Centralize test data in fixtures
2. **Clean Database**: Each test gets fresh database
3. **Realistic Data**: Use realistic test data
4. **Edge Cases**: Test boundary conditions

### Performance Testing
1. **Baseline Metrics**: Establish performance baselines
2. **Consistent Environment**: Use consistent test environment
3. **Multiple Runs**: Average results over multiple runs
4. **Resource Monitoring**: Monitor CPU, memory, database

## Continuous Integration

### GitHub Actions Workflow
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest --cov=. --junit-xml=test-results.xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit
pre-commit install

# Hooks include:
# - Black (code formatting)
# - isort (import sorting)
# - flake8 (linting)
# - bandit (security)
# - mypy (type checking)
```

## Test Reports

### Coverage Report
- Target: 80%+ overall coverage
- Critical paths: 95%+ coverage
- HTML report: `htmlcov/index.html`
- Terminal report with missing lines

### Performance Report
- Response time percentiles
- Throughput metrics
- Resource usage graphs
- Benchmark comparisons

### Security Report
- Vulnerability scan results
- Authentication test results
- Input validation coverage
- Security header validation

## Debugging Tests

### Common Issues
1. **Database State**: Ensure clean database per test
2. **Async Tests**: Use proper async fixtures
3. **Mock Configuration**: Verify mock setup
4. **Environment Variables**: Check test environment

### Debug Commands
```bash
# Run single test with output
pytest tests/test_auth_api.py::test_user_registration -v -s

# Debug with pdb
pytest --pdb tests/test_auth_api.py

# Show test coverage gaps
pytest --cov=. --cov-report=term-missing
```

## Test Maintenance

### Regular Tasks
1. **Update Test Data**: Keep test data current
2. **Review Coverage**: Identify coverage gaps
3. **Performance Baselines**: Update performance targets
4. **Security Tests**: Add new security tests

### Test Refactoring
1. **Remove Duplicates**: Consolidate similar tests
2. **Update Fixtures**: Keep fixtures current
3. **Improve Assertions**: Make assertions more specific
4. **Documentation**: Keep test documentation updated

## Integration with Development

### Test-Driven Development (TDD)
1. Write failing test first
2. Implement minimal code to pass
3. Refactor while keeping tests green
4. Repeat cycle

### Code Review Checklist
- [ ] Tests cover new functionality
- [ ] Tests follow naming conventions
- [ ] Performance impact considered
- [ ] Security implications tested
- [ ] Documentation updated

## Monitoring and Alerts

### Test Metrics
- Test execution time trends
- Coverage percentage over time
- Flaky test identification
- Performance regression detection

### Alerts
- Test failure notifications
- Coverage drop alerts
- Performance regression alerts
- Security test failures