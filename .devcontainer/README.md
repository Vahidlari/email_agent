# Email Agent Development Container

This devcontainer configuration provides a complete development environment for the Email Agent project.

## Features

- **Base Image**: `ghcr.io/vahidlari/aiapps/ai-dev:main-33e9578`
- **Python Development**: Pre-configured Python environment with linting and formatting tools
- **AI/ML Libraries**: Includes the Ragora package for AI knowledge base integration
- **VS Code Extensions**: Python, Pylance, Flake8, Black formatter, and GitLens extensions

## Setup

1. Open this repository in VS Code
2. When prompted, click "Reopen in Container" or use the command palette: `Remote-Containers: Reopen in Container`
3. The container will build and install dependencies automatically
4. The `ragora` package will be installed via the `postCreateCommand`

## Included Tools

- Python development tools (linting, formatting, type checking)
- VS Code Python extensions
- GitLens for enhanced Git integration and history visualization
- Ragora package for AI agent development

## Usage

Once the container is running, you can start developing your email agent using the Ragora framework for knowledge base integration.