import json
import logging
from collections.abc import Sequence
from typing import Any

from mcp.server import Server
from mcp.types import Resource, TextContent, Tool
from pydantic import AnyUrl

from .confluence import ConfluenceManager
from .jira import JiraManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-atlassian")

# Initialize the managers
confluence_manager = ConfluenceManager()
jira_manager = JiraManager()
app = Server("mcp-atlassian")


@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available Confluence spaces and Jira projects as resources."""
    resources = []

    # Add Confluence spaces
    spaces_response = confluence_manager.get_spaces()
    if isinstance(spaces_response, dict) and "results" in spaces_response:
        spaces = spaces_response["results"]
        resources.extend(
            [
                Resource(
                    uri=AnyUrl(f"confluence://{space['key']}"),
                    name=f"Confluence Space: {space['name']}",
                    mimeType="text/plain",
                    description=space.get("description", {}).get("plain", {}).get("value", ""),
                )
                for space in spaces
            ]
        )

    # Add Jira projects
    try:
        projects = jira_manager.jira.projects()
        resources.extend(
            [
                Resource(
                    uri=AnyUrl(f"jira://{project['key']}"),
                    name=f"Jira Project: {project['name']}",
                    mimeType="text/plain",
                    description=project.get("description", ""),
                )
                for project in projects
            ]
        )
    except Exception as e:
        logger.error(f"Error fetching Jira projects: {str(e)}")

    return resources


@app.read_resource()
async def read_resource(uri: AnyUrl) -> str:
    """Read content from Confluence or Jira."""
    uri_str = str(uri)

    # Handle Confluence resources
    if uri_str.startswith("confluence://"):
        parts = uri_str.replace("confluence://", "").split("/")

        # Handle space listing
        if len(parts) == 1:
            space_key = parts[0]
            documents = confluence_manager.get_space_pages(space_key)
            content = []
            for doc in documents:
                content.append(f"# {doc.metadata['title']}\n\n{doc.page_content}\n---")
            return "\n\n".join(content)

        # Handle specific page
        elif len(parts) >= 3 and parts[1] == "pages":
            space_key = parts[0]
            title = parts[2]
            doc = confluence_manager.get_page_by_title(space_key, title)

            if not doc:
                raise ValueError(f"Page not found: {title}")

            return doc.page_content

    # Handle Jira resources
    elif uri_str.startswith("jira://"):
        parts = uri_str.replace("jira://", "").split("/")

        # Handle project listing
        if len(parts) == 1:
            project_key = parts[0]
            issues = jira_manager.get_project_issues(project_key)
            content = []
            for issue in issues:
                content.append(f"# {issue.metadata['key']}: {issue.metadata['title']}\n\n{issue.page_content}\n---")
            return "\n\n".join(content)

        # Handle specific issue
        elif len(parts) >= 3 and parts[1] == "issues":
            issue_key = parts[2]
            issue = jira_manager.get_issue(issue_key)
            return issue.page_content

    raise ValueError(f"Invalid resource URI: {uri}")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available Confluence and Jira tools."""
    return [
        Tool(
            name="confluence_search",
            description="Search Confluence content using CQL",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "CQL query string (e.g. 'type=page AND space=DEV')"},
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of results (1-50)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50,
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="confluence_get_page",
            description="Get content of a specific Confluence page by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {"type": "string", "description": "Confluence page ID"},
                    "include_metadata": {
                        "type": "boolean",
                        "description": "Whether to include page metadata",
                        "default": True,
                    },
                },
                "required": ["page_id"],
            },
        ),
        Tool(
            name="confluence_create_page",
            description="Create a new Confluence page",
            inputSchema={
                "type": "object",
                "properties": {
                    "space_key": {"type": "string", "description": "Space key where the page will be created"},
                    "title": {"type": "string", "description": "Page title"},
                    "content": {"type": "string", "description": "Page content in wiki markup format"},
                    "parent_id": {
                        "type": "string",
                        "description": "Optional parent page ID",
                        "default": None,
                    },
                },
                "required": ["space_key", "title", "content"],
            },
        ),
        Tool(
            name="confluence_update_page",
            description="Update an existing Confluence page",
            inputSchema={
                "type": "object",
                "properties": {
                    "page_id": {"type": "string", "description": "ID of the page to update"},
                    "title": {"type": "string", "description": "New page title"},
                    "content": {"type": "string", "description": "New page content in wiki markup format"},
                    "version": {"type": "number", "description": "Current page version number"},
                },
                "required": ["page_id", "title", "content", "version"],
            },
        ),
        Tool(
            name="confluence_get_comments",
            description="Get comments for a specific Confluence page",
            inputSchema={
                "type": "object",
                "properties": {"page_id": {"type": "string", "description": "Confluence page ID"}},
                "required": ["page_id"],
            },
        ),
        Tool(
            name="jira_get_issue",
            description="Get details of a specific Jira issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {"type": "string", "description": "Jira issue key (e.g., 'PROJ-123')"},
                    "expand": {"type": "string", "description": "Optional fields to expand", "default": None},
                },
                "required": ["issue_key"],
            },
        ),
        Tool(
            name="jira_create_epic",
            description="Create a new Jira epic",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_key": {"type": "string", "description": "Project key where the epic will be created"},
                    "summary": {"type": "string", "description": "Epic summary/title"},
                    "description": {"type": "string", "description": "Epic description"},
                    "custom_fields": {
                        "type": "object",
                        "description": "Custom fields (e.g., Acceptance Criteria)",
                        "additionalProperties": True,
                        "default": {},
                    },
                },
                "required": ["project_key", "summary"],
            },
        ),
        Tool(
            name="jira_create_story",
            description="Create a new Jira story",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_key": {"type": "string", "description": "Project key where the story will be created"},
                    "summary": {"type": "string", "description": "Story summary/title"},
                    "description": {"type": "string", "description": "Story description"},
                    "epic_link": {
                        "type": "string",
                        "description": "Optional epic key to link the story to",
                        "default": None,
                    },
                    "custom_fields": {
                        "type": "object",
                        "description": "Custom fields (e.g., {'Acceptance Criteria': 'Criteria here'})",
                        "additionalProperties": True,
                        "default": {},
                    },
                },
                "required": ["project_key", "summary"],
            },
        ),
        Tool(
            name="jira_update_issue",
            description="Update an existing Jira issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "issue_key": {"type": "string", "description": "Key of the issue to update"},
                    "fields": {
                        "type": "object",
                        "description": "Fields to update, including custom fields (e.g., {'summary': 'New title', 'Acceptance Criteria': 'New criteria'})",
                        "additionalProperties": True,
                    },
                },
                "required": ["issue_key", "fields"],
            },
        ),
        Tool(
            name="jira_search",
            description="Search Jira issues using JQL",
            inputSchema={
                "type": "object",
                "properties": {
                    "jql": {"type": "string", "description": "JQL query string"},
                    "fields": {"type": "string", "description": "Comma-separated fields to return", "default": "*all"},
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of results (1-50)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50,
                    },
                },
                "required": ["jql"],
            },
        ),
        Tool(
            name="jira_get_project_issues",
            description="Get all issues for a specific Jira project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_key": {"type": "string", "description": "The project key"},
                    "limit": {
                        "type": "number",
                        "description": "Maximum number of results (1-50)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50,
                    },
                },
                "required": ["project_key"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
    """Handle tool calls for Confluence and Jira operations."""
    try:
        # Confluence tools
        if name == "confluence_search":
            limit = min(int(arguments.get("limit", 10)), 50)
            documents = confluence_manager.search(arguments["query"], limit)
            search_results = [
                {
                    "page_id": doc.metadata["page_id"],
                    "title": doc.metadata["title"],
                    "space": doc.metadata["space"],
                    "url": doc.metadata["url"],
                    "last_modified": doc.metadata["last_modified"],
                    "type": doc.metadata["type"],
                    "excerpt": doc.page_content,
                }
                for doc in documents
            ]
            return [TextContent(type="text", text=json.dumps(search_results, indent=2))]

        elif name == "confluence_get_page":
            doc = confluence_manager.get_page_content(arguments["page_id"])
            include_metadata = arguments.get("include_metadata", True)
            result = {"content": doc.page_content, "metadata": doc.metadata} if include_metadata else {"content": doc.page_content}
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "confluence_create_page":
            doc = confluence_manager.create_page(
                ConfluencePageCreate(
                    space_key=arguments["space_key"],
                    title=arguments["title"],
                    content=arguments["content"],
                    parent_id=arguments.get("parent_id"),
                )
            )
            return [TextContent(type="text", text=json.dumps({"content": doc.page_content, "metadata": doc.metadata}, indent=2))]

        elif name == "confluence_update_page":
            doc = confluence_manager.update_page(
                ConfluencePageUpdate(
                    page_id=arguments["page_id"],
                    title=arguments["title"],
                    content=arguments["content"],
                    version=arguments["version"],
                )
            )
            return [TextContent(type="text", text=json.dumps({"content": doc.page_content, "metadata": doc.metadata}, indent=2))]

        elif name == "confluence_get_comments":
            comments = confluence_manager.get_page_comments(arguments["page_id"])
            formatted_comments = [
                {
                    "author": comment.metadata["author_name"],
                    "created": comment.metadata["last_modified"],
                    "content": comment.page_content,
                }
                for comment in comments
            ]
            return [TextContent(type="text", text=json.dumps(formatted_comments, indent=2))]

        # Jira tools
        elif name == "jira_get_issue":
            doc = jira_manager.get_issue(arguments["issue_key"], expand=arguments.get("expand"))
            result = {"content": doc.page_content, "metadata": doc.metadata}
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "jira_create_epic":
            doc = jira_manager.create_issue(
                JiraIssueCreate(
                    project_key=arguments["project_key"],
                    summary=arguments["summary"],
                    description=arguments.get("description", ""),
                    issue_type="Epic",
                    custom_fields=arguments.get("custom_fields", {}),
                )
            )
            return [TextContent(type="text", text=json.dumps({"content": doc.page_content, "metadata": doc.metadata}, indent=2))]

        elif name == "jira_create_story":
            doc = jira_manager.create_issue(
                JiraIssueCreate(
                    project_key=arguments["project_key"],
                    summary=arguments["summary"],
                    description=arguments.get("description", ""),
                    issue_type="Story",
                    epic_link=arguments.get("epic_link"),
                    custom_fields=arguments.get("custom_fields", {}),
                )
            )
            return [TextContent(type="text", text=json.dumps({"content": doc.page_content, "metadata": doc.metadata}, indent=2))]

        elif name == "jira_update_issue":
            doc = jira_manager.update_issue(
                JiraIssueUpdate(
                    issue_key=arguments["issue_key"],
                    fields=arguments["fields"],
                )
            )
            return [TextContent(type="text", text=json.dumps({"content": doc.page_content, "metadata": doc.metadata}, indent=2))]

        elif name == "jira_search":
            limit = min(int(arguments.get("limit", 10)), 50)
            documents = jira_manager.search_issues(
                arguments["jql"], fields=arguments.get("fields", "*all"), limit=limit
            )
            search_results = [
                {
                    "key": doc.metadata["key"],
                    "title": doc.metadata["title"],
                    "type": doc.metadata["type"],
                    "status": doc.metadata["status"],
                    "created_date": doc.metadata["created_date"],
                    "priority": doc.metadata["priority"],
                    "link": doc.metadata["link"],
                    "excerpt": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                }
                for doc in documents
            ]
            return [TextContent(type="text", text=json.dumps(search_results, indent=2))]

        elif name == "jira_get_project_issues":
            limit = min(int(arguments.get("limit", 10)), 50)
            documents = jira_manager.get_project_issues(arguments["project_key"], limit=limit)
            project_issues = [
                {
                    "key": doc.metadata["key"],
                    "title": doc.metadata["title"],
                    "type": doc.metadata["type"],
                    "status": doc.metadata["status"],
                    "created_date": doc.metadata["created_date"],
                    "link": doc.metadata["link"],
                }
                for doc in documents
            ]
            return [TextContent(type="text", text=json.dumps(project_issues, indent=2))]

        raise ValueError(f"Unknown tool: {name}")

    except Exception as e:
        logger.error(f"Tool execution error: {str(e)}")
        raise RuntimeError(f"Tool execution failed: {str(e)}")


async def main():
    # Import here to avoid issues with event loops
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
