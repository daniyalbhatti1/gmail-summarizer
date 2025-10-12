# Contributing to Gmail Digest

Thank you for your interest in contributing to Gmail Digest! We welcome contributions from everyone.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/yourusername/gmail-digest.git
   cd gmail-digest
   ```

3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

4. Create a branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Guidelines

### Code Style

- We use **Black** for code formatting (line length: 100)
- We use **Ruff** for linting
- All code should have type hints and pass **mypy** checks

Run formatters and linters:
```bash
# Format code
black src/ tests/

# Run linter
ruff check src/ tests/

# Type check
mypy src/
```

### Testing

- All new features must include tests
- Maintain or improve code coverage
- Tests should be in `tests/` directory
- Use fixtures for reusable test data

Run tests:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_classify.py -v
```

### Type Hints

All functions should have type hints:

```python
def example_function(param: str, count: int = 5) -> list[str]:
    """Example function with proper type hints."""
    return [param] * count
```

### Docstrings

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description of function.

    Longer description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When something goes wrong
    """
    pass
```

### Logging

Use the `logging` module instead of `print()`:

```python
import logging

logger = logging.getLogger(__name__)

logger.info("Information message")
logger.warning("Warning message")
logger.error("Error message", exc_info=True)
```

## Contribution Workflow

1. **Make your changes**
   - Write clear, focused commits
   - Follow the code style guidelines
   - Add tests for new functionality

2. **Test your changes**
   ```bash
   # Run tests
   pytest
   
   # Check formatting
   black --check src/ tests/
   
   # Run linter
   ruff check src/ tests/
   
   # Type check
   mypy src/
   ```

3. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: Add new feature description"
   ```

   Commit message format:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation changes
   - `test:` for test additions/changes
   - `refactor:` for code refactoring
   - `style:` for formatting changes
   - `chore:` for maintenance tasks

4. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request**
   - Go to the original repository on GitHub
   - Click "New Pull Request"
   - Select your fork and branch
   - Provide a clear description of your changes

## Pull Request Guidelines

- **Title**: Clear and descriptive (e.g., "Add support for custom time ranges")
- **Description**: Explain what changes you made and why
- **Tests**: Include tests for new functionality
- **Documentation**: Update README.md or other docs if needed
- **Single Purpose**: Each PR should address one feature/fix

### PR Checklist

- [ ] Tests pass (`pytest`)
- [ ] Code is formatted (`black`)
- [ ] Linter passes (`ruff`)
- [ ] Type checking passes (`mypy`)
- [ ] Documentation updated (if needed)
- [ ] Commit messages are clear
- [ ] No sensitive information (tokens, keys) in commits

## Areas for Contribution

Here are some areas where we'd love contributions:

### Features
- Additional email providers (Outlook, Yahoo)
- Slack/Discord notification integrations
- Mobile app or progressive web app
- Advanced thread summarization
- Sentiment analysis
- Smart reply suggestions
- Attachment analysis

### Improvements
- Performance optimizations
- Better classification heuristics
- Enhanced HTML templates
- Internationalization (i18n)
- More comprehensive tests

### Bug Fixes
- Check the [Issues](https://github.com/yourusername/gmail-digest/issues) page
- Reproduce the bug
- Write a failing test
- Fix the bug
- Ensure test passes

### Documentation
- Improve README.md
- Add code examples
- Write tutorials
- Create video guides
- Translate documentation

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Welcome newcomers
- Accept constructive criticism
- Focus on what's best for the community
- Show empathy towards others

### Unacceptable Behavior

- Harassment or discriminatory comments
- Personal attacks
- Publishing others' private information
- Other unprofessional conduct

## Questions?

- Open an [Issue](https://github.com/yourusername/gmail-digest/issues) for bugs or feature requests
- Start a [Discussion](https://github.com/yourusername/gmail-digest/discussions) for questions or ideas
- Check existing issues/discussions before creating new ones

## License

By contributing to Gmail Digest, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🎉

