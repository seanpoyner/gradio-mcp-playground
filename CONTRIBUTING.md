# Contributing to Gradio MCP Playground

Thank you for your interest in contributing to Gradio MCP Playground! We welcome contributions from the community.

## How to Contribute

### Reporting Issues

- Use the GitHub issue tracker to report bugs
- Describe the issue clearly and include steps to reproduce
- Include your environment details (OS, Python version, etc.)

### Submitting Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Write or update tests as needed
5. Ensure all tests pass (`pytest`)
6. Format your code (`black .` and `ruff check .`)
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to your branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/seanpoyner/gradio-mcp-playground.git
cd gradio-mcp-playground

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linters
black .
ruff check .
```

### Code Style

- Follow PEP 8
- Use type hints where appropriate
- Write docstrings for all public functions and classes
- Keep line length under 100 characters
- Use meaningful variable names

### Adding Templates

To add a new template:

1. Create a new directory in `gradio_mcp_playground/templates/`
2. Add an `app.py` file with your Gradio MCP server
3. Include a `requirements.txt` if needed
4. Add a README.md explaining the template
5. Update the registry in `registry.py`

### Testing

- Write tests for new features
- Ensure existing tests pass
- Aim for good test coverage
- Use pytest for testing

### Documentation

- Update documentation for new features
- Include docstrings in your code
- Add examples where appropriate
- Update the README if needed

## Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone.

### Our Standards

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive criticism
- Show empathy towards others

### Enforcement

Instances of unacceptable behavior may be reported to the project maintainers.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
