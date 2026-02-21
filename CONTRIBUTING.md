# Contributing to CanDelivers

Thank you for your interest in contributing to CanDelivers! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and constructive
- Focus on the code, not the person
- Help others learn and grow
- Report issues professionally

## Getting Started

### Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/candelivers.git
cd candelivers

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (optional but recommended)
pip install pre-commit
pre-commit install
```

### Running Tests Locally

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=services --cov=packages

# Run specific test file
pytest tests/test_optimizer.py

# Run specific test
pytest tests/test_optimizer.py::TestRouteOptimizer::test_single_order_creates_route
```

### Code Quality

```bash
# Format code with black
black .

# Check imports with isort
isort .

# Lint with flake8
flake8

# Type checking with mypy
mypy services packages
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `test/` - Test additions
- `refactor/` - Code refactoring
- `perf/` - Performance improvements

### 2. Make Changes

- Keep commits atomic and well-described
- Write descriptive commit messages
- Update tests for new functionality
- Update documentation if needed

### 3. Ensure Tests Pass

```bash
# Run full test suite
pytest --cov=services --cov=packages

# Must have >85% coverage for new code
# Ensure all 45 tests pass
```

### 4. Code Review Checklist

Before submitting a PR, ensure:

- [ ] All tests pass (`pytest tests/`)
- [ ] Code coverage is >85%
- [ ] Code is formatted with `black`
- [ ] Imports are sorted with `isort`
- [ ] No linting issues (`flake8`)
- [ ] Documentation is updated
- [ ] Commit messages are clear and descriptive
- [ ] No sensitive data is committed

### 5. Submit Pull Request

```bash
git push origin feature/your-feature-name
```

Then open a PR on GitHub with:
- Clear title describing the change
- Description of what was changed and why
- Reference to any related issues (#123)
- Testing instructions if applicable

## Project Structure

```
candelivers/
├── services/                 # Core service implementations
│   ├── routing/             # Route optimization service
│   │   └── src/
│   │       ├── optimizer.py      # VRPTW solver
│   │       ├── constraints.py    # Constraint definitions
│   │       └── distance.py       # Distance calculations
│   ├── order/               # Order management service
│   │   └── src/
│   │       ├── api.py           # FastAPI endpoints
│   │       └── models.py        # Data models
│   └── tracking/            # Tracking service
│       └── src/
│           └── tracker.py       # Vehicle tracking
├── packages/                # Utility packages
│   ├── simulation/          # Simulation engine
│   └── geo/                 # Geospatial utilities
├── tests/                   # Test suite (45 tests)
├── pyproject.toml           # Project configuration
├── docker-compose.yml       # Docker setup
└── README.md               # Documentation
```

## Code Style Guide

### Python Style

- Follow PEP 8
- Use Black for formatting (100-char line length)
- Use type hints for function signatures
- Document public functions with docstrings

### Example Function

```python
def calculate_route_distance(
    orders: List[Order],
    distance_matrix: np.ndarray,
) -> float:
    """Calculate total distance for a route.

    Args:
        orders: List of orders in route
        distance_matrix: Precomputed distance matrix

    Returns:
        Total distance in kilometers
    """
    total = 0.0
    for i in range(len(orders) - 1):
        total += distance_matrix[i][i + 1]
    return total
```

### Docstring Format

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """Brief description.

    Longer description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When something is wrong
    """
    pass
```

## Testing Guidelines

### Test Structure

```python
class TestFeatureName:
    """Test suite for feature."""

    @pytest.fixture
    def setup(self):
        """Setup test fixtures."""
        return ObjectToTest()

    def test_basic_functionality(self, setup):
        """Test basic behavior."""
        result = setup.method()
        assert result == expected

    def test_edge_case(self):
        """Test edge cases."""
        with pytest.raises(ValueError):
            bad_input()
```

### Test Coverage Requirements

- All public functions must be tested
- Edge cases and error conditions
- Integration between components
- Maintain >85% code coverage

### Running Tests

```bash
# Run specific test class
pytest tests/test_optimizer.py::TestRouteOptimizer

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=services --cov=packages --html=coverage.html
```

## Documentation

### Updating README

- Keep getting started section up-to-date
- Document new features with examples
- Update API documentation
- Include architecture diagrams if helpful

### Code Comments

- Comment why, not what
- Keep comments updated with code
- Use docstrings for public APIs

### Example Documentation

```python
def optimize_routes(
    orders: List[Order],
    vehicles: List[Vehicle],
) -> List[Route]:
    """Optimize delivery routes using VRPTW solver.

    Uses nearest-neighbor heuristic for initial solution,
    then applies 2-opt local search for improvement.

    Args:
        orders: Orders to deliver
        vehicles: Available vehicles

    Returns:
        Optimized routes for each vehicle

    Example:
        >>> routes = optimize_routes(orders, vehicles)
        >>> for route in routes:
        ...     print(f"Vehicle {route.vehicle_id}: {route.total_distance}km")
    """
```

## Performance Considerations

### Algorithm Improvements

- Nearest-neighbor construction heuristic
- 2-opt local search (O(n²) iterations)
- Distance matrix caching
- Spatial indexing for large problems

### Optimization Tips

- Profile code before optimizing
- Avoid premature optimization
- Document performance-critical sections
- Include benchmarks for significant changes

## Security Considerations

- Never commit secrets or credentials
- Validate all external inputs
- Use security best practices
- Report vulnerabilities responsibly
- Don't commit database backups

## Common Contributions

### Adding a New Constraint

1. Create constraint class in `constraints.py`
2. Implement `validate()` method
3. Add tests in `test_constraints.py`
4. Update documentation
5. Example: ZoneRestrictionConstraint

### Improving the Optimizer

1. New heuristic? Update `optimizer.py`
2. Add tests showing improvement
3. Document algorithm
4. Benchmark performance
5. Update README with results

### Extending Simulation

1. New event types? Update `engine.py`
2. New scenarios? Add to `scenarios.py`
3. New metrics? Update `metrics.py`
4. Add corresponding tests
5. Document usage in README

## Issues and Discussions

### Reporting Issues

Include:
- Clear description of the problem
- Steps to reproduce
- Expected behavior
- Actual behavior
- System information
- Error messages/logs

### Suggesting Features

Propose:
- Clear use case
- Proposed solution
- Alternative approaches
- Potential impact

## Release Process

Releases follow semantic versioning:
- MAJOR: Breaking changes
- MINOR: New features
- PATCH: Bug fixes

Maintainers handle releases and version bumping.

## Questions?

- Check existing issues and discussions
- Review documentation in README.md
- Ask in GitHub discussions
- Contact: support@candelivers.com

## License

By contributing, you agree that your contributions will be licensed under the same MIT License that covers the project.

---

Thank you for contributing to CanDelivers!
