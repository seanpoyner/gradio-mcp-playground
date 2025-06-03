#!/usr/bin/env python3

"""Setup script for GMP Agent

GMP Agent is an intelligent coding assistant and GUI application that helps users 
build, configure, and deploy MCP (Model Context Protocol) servers using the 
Gradio MCP Playground toolkit.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
if requirements_file.exists():
    with open(requirements_file, 'r', encoding='utf-8') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
else:
    requirements = [
        "gradio>=4.44.0",
        "pydantic>=2.0.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.20.0",
        "httpx>=0.24.0",
        "aiofiles>=23.0.0",
        "python-multipart>=0.0.6",
        "jinja2>=3.1.0",
        "markdown>=3.4.0",
        "pyyaml>=6.0",
        "rich>=13.0.0",
        "typer>=0.9.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "pillow>=10.0.0",
        "requests>=2.31.0"
    ]

# Development requirements
dev_requirements = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.5.0",
    "pre-commit>=3.4.0"
]

setup(
    name="gmp-agent",
    version="1.0.0",
    author="GMP Team",
    author_email="team@gmp.dev",
    description="Intelligent MCP Server Builder - AI assistant for creating and managing MCP servers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gradio-mcp-playground/agent",
    project_urls={
        "Bug Reports": "https://github.com/gradio-mcp-playground/agent/issues",
        "Source": "https://github.com/gradio-mcp-playground/agent",
        "Documentation": "https://github.com/gradio-mcp-playground/agent/blob/main/docs/user_guide.md"
    },
    
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    include_package_data=True,
    package_data={
        "": ["*.json", "*.md", "*.txt", "*.yaml", "*.yml"],
        "config": ["*.json"],
        "docs": ["*.md"],
        "examples": ["*.py", "*.md", "*.json"]
    },
    
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": dev_requirements,
        "all": requirements + dev_requirements,
        "mcp": ["mcp>=1.0.0"],
        "ai": ["openai>=1.0.0", "anthropic>=0.8.0"],
        "ml": ["torch>=2.0.0", "transformers>=4.30.0", "scikit-learn>=1.3.0"]
    },
    
    entry_points={
        "console_scripts": [
            "gmp-agent=app:main",
            "gmp-agent-dev=app:main",
        ],
    },
    
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: User Interfaces",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Framework :: Gradio",
    ],
    
    keywords=[
        "gradio", "mcp", "model-context-protocol", "ai", "ml", "gui", 
        "web-interface", "server-builder", "automation", "llm", "chatbot"
    ],
    
    zip_safe=False,
    platforms=["any"],
    
    # Metadata
    license="MIT",
    maintainer="GMP Team",
    maintainer_email="team@gmp.dev",
)