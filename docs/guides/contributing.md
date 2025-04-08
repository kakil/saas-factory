# Contributing to SaaS Factory 

Thank you for considering contributing to the SaaS Factory! This document provides guidelines and 
instructions for contributing to this project.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please read it before contributing.

## How Can I Contribute?

### Reporting Bugs

Bug reports help us make the SaaS Factory better. When you submit a bug report, please include:

1. A clear and descriptive title
2. Steps to reproduce the issue
3. Expected and actual behavior
4. Screenshots if applicable
5. Environment information (OS, Python version, etc.)

Please use the bug report template when creating an issue.

### Suggesting Enhancements

Enhancement suggestions are always welcome! Please include:

1. A clear and descriptive title
2. A detailed description of the proposed enhancement
3. Any relevant examples or mock-ups
4. Why this enhancement would be useful to most users

### Pull Requests

We actively welcome pull requests. Here's the process:

1. Fork the repository
2. Create a branch for your dfeature or bugfix (`git checkout -b feature/your-feature-name`)
3. Make your changes
4. Add or update tests as needed
5. Run tests to ensure they pass
6. Update documentation if needed
7. Submit a pull request

## Development Setup

## Coding Guidelines

### Python Style Guide

We follow PEP 8 and use tools to help enforce this:

- Use `black` for code formatting:
  ```bash
  black app tests
  ```
- Use `isort` to sort imports:
  ```bash
  isort app tests
  ```
- Use `flake8` to check for errors:
  ```bash
  flake8 app tests
  ```

### Type Hints

Use type hints for all function parameters and return values:

```python
def process_data(data: Dict[str, Any]) -> List[str]:
    # Function implementation
    return result
```

### Documentation

- All modules, classes, and functions should have docstrings
- Use Google-style docstrings:

```python
def function_with_types_in_docstring(param1: int, param2: str) -> bool:
    """Example function with types documented in the docstring.

    Args:
        param1: The first parameter.
        param2: The second parameter.

    Returns:
        True if successful, False otherwise.

    Raises:
        ValueError: If param1 is negative.
    """
```

### Testing

- Write tests for all new features and bug fixes
- Aim for at least 80% code coverage
- Test structure should mirror code structure

## Documentation Maintenance

When updating documentation, you can use the `scripts/docs-structure.sh` utility script to ensure all files are properly organized in the documentation structure. This script:

- Creates the necessary directory structure
- Copies documentation files to the appropriate locations
- Generates a documentation index file

Run it from the project root with:

```bash
./scripts/docs-structure.sh
```

Make it executable:

```bash
chmod +x scripts/docs-structure.sh
```

## Git Workflow

### Branching Strategy

- `main`: The main branch always contains production-ready code
- `develop`: Development branch where features are integrated
- `feature/feature-name`: Feature branches for new features
- `bugfix/bug-name`: Bugfix branches for bug fixes

### Commit Messages

Use conventional commit messages:

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or modifying tests
- `chore`: Updating build tasks, package manager configs, etc.

Example: `feat: add gradient text rendering for titles`

## Release Process

1. Update version number in:
   - `__init__.py`
   - `setup.py`
2. Update CHANGELOG.md
3. Create a GitHub release with release notes
4. Tag the release with version number

## Getting Help

If you have questions about contributing, please:

1. Check existing issues and discussions
2. Create a new discussion if your question hasn't been addressed
3. Reach out to the maintainers directly if needed

Thank you for contributing to the Instagram Carousel Generator!
