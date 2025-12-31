# Talent8 MCP Server for AWS Bedrock

A Model Context Protocol (MCP) server that enables Claude and other MCP clients to retrieve job openings from AWS Bedrock Knowledge Bases.

## Features

- **Retrieval-only access** to AWS Bedrock Knowledge Base using the `retrieve` API
- **`get_job_openings` tool** for searching job openings with customizable parameters
- **Rich metadata** including relevance scores, source information, and job details
- **TDD approach** with comprehensive test coverage
- **SOLID principles** with clean separation of concerns

## Project Structure

```
talent8-mcp/
├── src/
│   ├── server.py           # MCP server with get_job_openings tool
│   ├── bedrock_client.py   # AWS Bedrock Knowledge Base client
│   ├── config.py           # Configuration management
│   └── models.py           # Pydantic data models
├── tests/
│   ├── test_server.py
│   ├── test_bedrock_client.py
│   ├── test_config.py
│   └── test_models.py
├── pyproject.toml          # Poetry dependencies
├── .env.example            # Environment variables template
└── README.md
```

## Prerequisites

- Python 3.10 or higher
- [Poetry](https://python-poetry.org/docs/#installation) for dependency management
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (optional, for faster installs)
- AWS account with:
  - Bedrock Knowledge Base configured with job openings data
  - Appropriate IAM permissions for Bedrock access

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/alexnodejs/talent8-mcp.git
cd talent8-mcp
```

### 2. Install dependencies

Using Poetry:

```bash
poetry install
```

Or using uv (faster):

```bash
uv sync
```

### 3. Configure environment variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your AWS configuration:

```bash
AWS_REGION=us-east-1
BEDROCK_KNOWLEDGE_BASE_ID=your-kb-id-here

# Optional: If not using IAM roles/profiles
# AWS_ACCESS_KEY_ID=your-access-key
# AWS_SECRET_ACCESS_KEY=your-secret-key
```

## AWS Setup

### Knowledge Base Requirements

Your AWS Bedrock Knowledge Base should contain job opening documents. The knowledge base can be populated with:

- PDF documents with job descriptions
- Text files with job postings
- Web pages with job listings
- Any other supported document format

### IAM Permissions

Your AWS credentials need the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:Retrieve",
        "bedrock:GetKnowledgeBase"
      ],
      "Resource": "arn:aws:bedrock:*:*:knowledge-base/*"
    }
  ]
}
```

## Usage

### Running Tests

Run the full test suite:

```bash
poetry run pytest
```

With coverage:

```bash
poetry run pytest --cov=src --cov-report=html
```

### Testing Locally with MCP Inspector

Use the MCP development tools to test your server:

```bash
poetry run mcp dev src/server.py
```

Or with uv:

```bash
uv run mcp dev src/server.py
```

This will open the MCP Inspector in your browser where you can test the `get_job_openings` tool.

### Running the Server Standalone

```bash
poetry run python src/server.py
```

## Integration with Claude Desktop

To use this MCP server with Claude Desktop, add it to your Claude configuration file.

### macOS

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "talent8-bedrock": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/talent8-mcp",
        "run",
        "python",
        "src/server.py"
      ],
      "env": {
        "AWS_REGION": "us-east-1",
        "BEDROCK_KNOWLEDGE_BASE_ID": "your-kb-id"
      }
    }
  }
}
```

### Linux

Edit `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "talent8-bedrock": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/talent8-mcp",
        "run",
        "python",
        "src/server.py"
      ],
      "env": {
        "AWS_REGION": "us-east-1",
        "BEDROCK_KNOWLEDGE_BASE_ID": "your-kb-id"
      }
    }
  }
}
```

### Windows

Edit `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "talent8-bedrock": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\path\\to\\talent8-mcp",
        "run",
        "python",
        "src/server.py"
      ],
      "env": {
        "AWS_REGION": "us-east-1",
        "BEDROCK_KNOWLEDGE_BASE_ID": "your-kb-id"
      }
    }
  }
}
```

### Using Poetry instead of uv

If you prefer Poetry:

```json
{
  "mcpServers": {
    "talent8-bedrock": {
      "command": "poetry",
      "args": [
        "run",
        "python",
        "src/server.py"
      ],
      "cwd": "/absolute/path/to/talent8-mcp",
      "env": {
        "AWS_REGION": "us-east-1",
        "BEDROCK_KNOWLEDGE_BASE_ID": "your-kb-id"
      }
    }
  }
}
```

### Restart Claude Desktop

After updating the configuration, restart Claude Desktop to load the MCP server.

## Using the `get_job_openings` Tool

Once configured, you can use the tool in Claude:

**Example prompts:**

- "Find software engineering positions"
- "Get job openings for data scientists with 5 results"
- "Search for remote product manager roles"

**Tool parameters:**

- `query_text` (required): Search query for job openings
- `max_results` (optional): Maximum results to return (default: 10, max: 100)

**Example output:**

```
Found 2 job opening(s):

--- Job Opening #1 ---
Relevance Score: 95.0%

Software Engineer - Remote Position
Join our engineering team to build innovative solutions...

Metadata:
  - job_id: SE-2024-001
  - department: Engineering
  - location: Remote

Source Type: S3
Location: s3://jobs-bucket/software-engineer.pdf

--- Job Opening #2 ---
Relevance Score: 87.0%

Senior Data Scientist
Looking for an experienced data scientist...

Metadata:
  - job_id: DS-2024-042
  - department: Data Science
  - location: New York, NY

Source Type: S3
Location: s3://jobs-bucket/data-scientist.pdf
```

## Development

### Code Style

The project follows Python best practices:

- Type hints throughout
- Comprehensive docstrings
- Pydantic models for validation
- Error handling with custom exceptions
- Logging to stderr (MCP requirement)

### Adding New Features

1. Write tests first (TDD approach)
2. Implement the feature
3. Ensure all tests pass
4. Update documentation

## Troubleshooting

### Server doesn't start

- Check that environment variables are set correctly
- Verify AWS credentials have proper permissions
- Ensure Knowledge Base ID exists and is accessible

### No results returned

- Verify your Knowledge Base contains relevant documents
- Check that documents are properly indexed
- Try broader search queries

### Claude Desktop doesn't show the tool

- Verify the config file path is correct
- Check that absolute paths are used
- Restart Claude Desktop after config changes
- Check Claude Desktop logs for errors

## License

MIT

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Ensure all tests pass
5. Submit a pull request

For issues and questions, use [GitHub Issues](https://github.com/alexnodejs/talent8-mcp/issues).