# TARS - Your AI Assistant 

TARS is an AI-powered assistant that helps you manage your digital life across email, Slack, Twitter, and more. It leverages advanced language models and a extensible tool system to understand your requests and take appropriate actions on your behalf.

## Key Features

- Natural language interaction via Slack, web interface, and other surfaces
- Intelligent email management - summarization, classification, response suggestions
- Integration with Slack for managing messages and notifications 
- Customizable tools for extending TARS' capabilities

## Architecture Overview

TARS consists of the following main components:

- **Agent**: The core intelligence that understands user requests and determines the appropriate actions to take. Implemented using the `AgentManager` class in `graphs/agent.py`.

- **Tools**: Modular functions that the agent can use to perform specific tasks, such as fetching emails, posting Slack messages, reading images, etc. Defined in `graphs/custom_tools.py`.

- **Surfaces**: Interfaces for users to interact with TARS, currently supporting Slack and a web interface. Implemented in the `surfaces/` directory.

## Setup and Installation 

1. Clone the repository: `git clone https://github.com/yourusername/TARS.git`

2. Install uv (modern Python package manager):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   source $HOME/.local/bin/env
   ```

3. Install the project dependencies using uv:
   ```bash
   uv sync
   ```

4. Set up the necessary API credentials:
   - Gmail API: Follow the instructions in `retrievers/gmail.py` to set up Gmail API access.
   - Slack API: Set the `SLACK_BOT_TOKEN` and `SLACK_USER_TOKEN` environment variables with your Slack app credentials.
   - OpenAI API: Set the `OPENAI_API_KEY` environment variable with your OpenAI API key.

5. Run the web interface: 
   ```bash
   uv run streamlit run surfaces/web/web.py
   ```

## Docker Setup

You can also run TARS using Docker:

```bash
docker-compose up
```

This will build the Docker image using uv for dependency management and start the application.

## Usage Examples

Here's an example of how to interact with TARS via the web interface:

1. Go to `http://localhost:8501` in your web browser.

2. Type in a request, such as "Summarize my unread emails from the past day".

3. Click the "Send" button to submit your request.

4. TARS will process your request and display the response in the chat interface.

## GitHub Actions for Deployment

TARS now includes GitHub Actions workflows for automated deployment to AWS managed Kubernetes, utilizing the GitHub Container Registry for Docker images. These workflows are triggered by changes to specific branches:

- **Stage Deployment**: Triggered by changes to the `stage` branch. The workflow builds the Docker image, pushes it to the GitHub Container Registry, and deploys it to the staging environment on Kubernetes.
- **Prod Deployment**: Triggered by changes to the `main` branch. Similar to the stage deployment, it builds, pushes, and deploys the Docker image, but targets the production environment.

To trigger a deployment, simply push your changes to the corresponding branch. The workflows are defined in `.github/workflows/deployment-stage.yml` and `.github/workflows/deployment-prod.yml`.

## API Invocation

To interact with TARS' APIs, you'll need an API key for authentication. This section outlines how to obtain an API key and use it to invoke the chat endpoint.

### Using the API Key

Once you have your API key, you can use it to authenticate your requests to the chat endpoint. Here's an example `curl` command to invoke the chat API:

```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -H "x-api-key: YOUR_API_KEY_HERE" \
     -d '{"message": "Hello, TARS!", "user_name": "John Doe"}'
```

Replace `YOUR_API_KEY_HERE` with your actual API key. The response will contain the chat response from TARS.

## Contributing

We welcome contributions to help improve TARS! To get started:

1. Fork the repository and create a new branch for your feature or bug fix.

2. Make your changes, following the existing code style and conventions.

3. Write tests to cover your changes and ensure that the existing tests still pass.

4. Submit a pull request describing your changes and why they should be merged.

## Directory Structure

- `graphs/`: Contains the core agent logic and tool definitions.
- `retrievers/`: Modules for retrieving data from external sources (Gmail, Google Calendar, etc.)
- `surfaces/`: User interface implementations (Slack, web).
