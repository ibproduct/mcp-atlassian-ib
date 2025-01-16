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

[Rest of the original README content...]
