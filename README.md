# Atlassian MCP server for IntelligenceBank

Model Context Protocol (MCP) server for Atlassian Cloud products (Confluence and Jira), customized for IntelligenceBank. This integration is designed specifically for Atlassian Cloud instances and does not support Atlassian Server or Data Center deployments.

This is a fork of the original MCP Atlassian project, enhanced with additional capabilities for IntelligenceBank's specific needs.

Repository: https://github.com/ibproduct/mcp-atlassian-ib

## Installation Guide for Non-Developers

This guide will walk you through installing all required components on macOS. Each step includes GUI-based installation options where possible.

### 1. Install Required Software

#### Install Python
1. Visit https://www.python.org/downloads/
2. Download the latest macOS installer (pkg file)
3. Double-click the downloaded file and follow the installation wizard
4. Verify installation by opening Terminal (Applications > Utilities > Terminal) and typing:
   ```bash
   python3 --version
   ```

#### Install Node.js
1. Visit https://nodejs.org/en
2. Download the macOS installer (pkg file) - choose "LTS" version
3. Double-click the downloaded file and follow the installation wizard
4. Verify installation:
   ```bash
   node --version
   npm --version
   ```

#### Install Git
1. Visit https://git-scm.com/download/mac
2. Download the macOS installer
3. Double-click the downloaded file and follow the installation wizard
4. Verify installation:
   ```bash
   git --version
   ```

### 2. Install Claude Desktop App
1. Download and install the Claude desktop app from Anthropic's website
2. Launch the app and sign in with your Claude account

### 3. Get Atlassian API Tokens
1. Go to https://id.atlassian.net/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a name (e.g., "Claude Integration")
4. Copy the generated token and keep it safe - you'll need it later

### 4. Install the MCP Server

1. Open Terminal (Applications > Utilities > Terminal)
2. Run these commands one by one:
   ```bash
   # Clone the repository
   cd ~/Documents
   git clone https://github.com/ibproduct/mcp-atlassian-ib.git
   cd mcp-atlassian-ib

   # Create and activate virtual environment
   python3 -m venv venv
   source venv/bin/activate

   # Install the package
   pip install -e .
   ```

### 5. Configure Claude Desktop

1. Open Finder
2. Press Cmd+Shift+G and enter: `~/Library/Application Support/Claude`
3. If the `Claude` folder doesn't exist, create it
4. Create or edit `claude_desktop_config.json` with this content (replace placeholders with your values):

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/Users/YOUR_USERNAME/Desktop",
        "/Users/YOUR_USERNAME/Downloads",
        "/Users/YOUR_USERNAME/Documents"
      ]
    },
    "mcp-atlassian-ib": {
      "command": "/Users/YOUR_USERNAME/Documents/mcp-atlassian-ib/venv/bin/python",
      "args": [
        "-m",
        "mcp_atlassian_ib.server"
      ],
      "env": {
        "CONFLUENCE_URL": "https://your-domain.atlassian.net/wiki",
        "CONFLUENCE_USERNAME": "your.email@domain.com",
        "CONFLUENCE_API_TOKEN": "your_api_token",
        "JIRA_URL": "https://your-domain.atlassian.net",
        "JIRA_USERNAME": "your.email@domain.com",
        "JIRA_API_TOKEN": "your_api_token"
      }
    }
  }
}
```

Replace:
- `YOUR_USERNAME` with your macOS username
- `your-domain` with your Atlassian domain
- `your.email@domain.com` with your Atlassian email
- `your_api_token` with the API tokens you created earlier

### 6. Start Using the Integration

1. Close and reopen the Claude desktop app
2. The Atlassian integration should now be available
3. Try asking Claude about your Jira issues or Confluence pages

### Troubleshooting

If you encounter any issues:
1. Make sure all paths in the configuration file match your system
2. Verify that the virtual environment is in the correct location
3. Check that your Atlassian API tokens are correct
4. Try closing and reopening the Claude desktop app

For additional help, please open an issue on the GitHub repository.

## Features

- Search and read Confluence spaces/pages
- Create and update Confluence pages
- Get Confluence page comments
- Search and read Jira issues
- Create and update Jira issues (Epics and Stories)
- Custom field support (e.g., Acceptance Criteria)
- Get project issues and metadata

## API

### Resources

- `confluence://{space_key}`: Access Confluence spaces and pages
- `confluence://{space_key}/pages/{title}`: Access specific Confluence pages
- `jira://{project_key}`: Access Jira project and its issues
- `jira://{project_key}/issues/{issue_key}`: Access specific Jira issues

### Tools

#### Confluence Tools

- **confluence_search**
  - Search Confluence content using CQL
  - Inputs:
    - `query` (string): CQL query string
    - `limit` (number, optional): Results limit (1-50, default: 10)
  - Returns:
    - Array of search results with page_id, title, space, url, last_modified, type, and excerpt

- **confluence_get_page**
  - Get content of a specific Confluence page
  - Inputs:
    - `page_id` (string): Confluence page ID
    - `include_metadata` (boolean, optional): Include page metadata (default: true)

- **confluence_create_page**
  - Create a new Confluence page
  - Inputs:
    - `space_key` (string): Space key where the page will be created
    - `title` (string): Page title
    - `content` (string): Page content in wiki markup format
    - `parent_id` (string, optional): Parent page ID

- **confluence_update_page**
  - Update an existing Confluence page
  - Inputs:
    - `page_id` (string): ID of the page to update
    - `title` (string): New page title
    - `content` (string): New page content in wiki markup format
    - `version` (number): Current page version number

- **confluence_get_comments**
  - Get comments for a specific Confluence page
  - Input: `page_id` (string)

#### Jira Tools

- **jira_get_issue**
  - Get details of a specific Jira issue
  - Inputs:
    - `issue_key` (string): Jira issue key (e.g., 'PROJ-123')
    - `expand` (string, optional): Fields to expand

- **jira_create_epic**
  - Create a new Jira epic
  - Inputs:
    - `project_key` (string): Project key where the epic will be created
    - `summary` (string): Epic summary/title
    - `description` (string, optional): Epic description
    - `custom_fields` (object, optional): Custom fields (e.g., Acceptance Criteria)

- **jira_create_story**
  - Create a new Jira story
  - Inputs:
    - `project_key` (string): Project key where the story will be created
    - `summary` (string): Story summary/title
    - `description` (string, optional): Story description
    - `epic_link` (string, optional): Epic key to link the story to
    - `custom_fields` (object, optional): Custom fields (e.g., Acceptance Criteria)

- **jira_update_issue**
  - Update an existing Jira issue
  - Inputs:
    - `issue_key` (string): Key of the issue to update
    - `fields` (object): Fields to update, including custom fields

- **jira_search**
  - Search Jira issues using JQL
  - Inputs:
    - `jql` (string): JQL query string
    - `fields` (string, optional): Comma-separated fields (default: "*all")
    - `limit` (number, optional): Results limit (1-50, default: 10)

- **jira_get_project_issues**
  - Get all issues for a specific Jira project
  - Inputs:
    - `project_key` (string): Project key
    - `limit` (number, optional): Results limit (1-50, default: 10)

### Custom Fields Support

The Jira integration supports custom fields like Acceptance Criteria. When creating or updating issues:

```json
// Example: Creating a story with Acceptance Criteria
{
  "project_key": "PROJ",
  "summary": "Implement new feature",
  "description": "Feature description",
  "custom_fields": {
    "Acceptance Criteria": "1. Criteria one\n2. Criteria two\n3. Criteria three"
  }
}

// Example: Updating an issue's custom fields
{
  "issue_key": "PROJ-123",
  "fields": {
    "Acceptance Criteria": "Updated acceptance criteria",
    "summary": "Updated summary"
  }
}
```

## Configuration

1. Get API tokens from: https://id.atlassian.com/manage-profile/security/api-tokens

2. Create a `.env` file with your credentials:

```bash
CONFLUENCE_URL=https://your-domain.atlassian.net/wiki
CONFLUENCE_USERNAME=your.email@domain.com
CONFLUENCE_API_TOKEN=your_api_token

JIRA_URL=https://your-domain.atlassian.net
JIRA_USERNAME=your.email@domain.com
JIRA_API_TOKEN=your_api_token
```

## Usage with Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mcp-atlassian-ib": {
      "command": "uvx",
      "args": ["mcp-atlassian"],
      "env": {
        "CONFLUENCE_URL": "https://your-domain.atlassian.net/wiki",
        "CONFLUENCE_USERNAME": "your.email@domain.com",
        "CONFLUENCE_API_TOKEN": "your_api_token",
        "JIRA_URL": "https://your-domain.atlassian.net",
        "JIRA_USERNAME": "your.email@domain.com",
        "JIRA_API_TOKEN": "your_api_token"
      }
    }
  }
}
```

<details>
<summary>Alternative configuration using <code>uv</code></summary>

```json
{
  "mcpServers": {
    "mcp-atlassian-ib": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/mcp-atlassian-ib",
        "run",
        "mcp-atlassian"
      ],
      "env": {
        "CONFLUENCE_URL": "https://your-domain.atlassian.net/wiki",
        "CONFLUENCE_USERNAME": "your.email@domain.com",
        "CONFLUENCE_API_TOKEN": "your_api_token",
        "JIRA_URL": "https://your-domain.atlassian.net",
        "JIRA_USERNAME": "your.email@domain.com",
        "JIRA_API_TOKEN": "your_api_token"
      }
    }
  }
}
```
Replace `/path/to/mcp-atlassian-ib` with the actual path where you've cloned the repository.
</details>


## Security

- Never share API tokens
- Keep .env files secure and private
- See [SECURITY.md](SECURITY.md) for best practices

## License

Licensed under MIT - see [LICENSE](LICENSE) file. This is not an official Atlassian product.
