import logging
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
import urllib.parse

from atlassian import Jira
from dotenv import load_dotenv

from .config import JiraConfig
from .preprocessing import TextPreprocessor
from .types import Document, JiraIssueCreate, JiraIssueUpdate

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger("mcp-jira")


class JiraManager:
    """Handles all Jira operations including fetching, creating, and updating issues."""

    # Known custom field mappings - these will be updated during initialization
    CUSTOM_FIELD_MAPPINGS = {
        'Epic Name': 'customfield_10021',
        'Epic Link': 'customfield_10019',
        'Acceptance Criteria': 'customfield_11738',  # Known Acceptance Criteria field
    }

    def __init__(self):
        url = os.getenv("JIRA_URL")
        username = os.getenv("JIRA_USERNAME")
        token = os.getenv("JIRA_API_TOKEN")

        if not all([url, username, token]):
            raise ValueError("Missing required Jira environment variables")

        self.config = JiraConfig(url=url, username=username, api_token=token)
        self.jira = Jira(
            url=self.config.url,
            username=self.config.username,
            password=self.config.api_token,  # API token is used as password
            cloud=True,
        )
        self.preprocessor = TextPreprocessor(self.config.url)
        self._init_custom_fields()

    def _init_custom_fields(self):
        """Initialize custom field mappings from Jira."""
        try:
            fields = self.jira.get_all_fields()
            for field in fields:
                if field.get('custom'):
                    # Store both name and id mapping for better lookup
                    self.CUSTOM_FIELD_MAPPINGS[field['name']] = field['id']
                    # Also store the customfield_XXXXX name as a key
                    if field['id'].startswith('customfield_'):
                        self.CUSTOM_FIELD_MAPPINGS[field['id']] = field['id']
            
            logger.info("Available custom fields:")
            for name, field_id in self.CUSTOM_FIELD_MAPPINGS.items():
                logger.info(f"  {name}: {field_id}")
        except Exception as e:
            logger.error(f"Error initializing custom fields: {str(e)}")

    def _get_custom_field_id(self, field_name: str) -> Optional[str]:
        """Get the custom field ID for a given field name or ID."""
        # If the field_name is already a customfield_XXXXX format, verify it exists
        if field_name.startswith('customfield_'):
            field_id = self.CUSTOM_FIELD_MAPPINGS.get(field_name)
            if field_id:
                return field_id
            logger.warning(f"Unknown custom field ID: {field_name}")
            return None

        # Otherwise, look up by name
        field_id = self.CUSTOM_FIELD_MAPPINGS.get(field_name)
        if not field_id:
            logger.warning(f"Unknown custom field name: {field_name}")
        return field_id

    def _clean_text(self, text: str) -> str:
        """
        Clean text content by:
        1. Processing user mentions and links
        2. Converting HTML/wiki markup to markdown
        """
        if not text:
            return ""

        return self.preprocessor.clean_jira_text(text)

    def get_issue(self, issue_key: str, expand: Optional[str] = None) -> Document:
        """
        Get a single issue with all its details.

        Args:
            issue_key: The issue key (e.g. 'PROJ-123')
            expand: Optional fields to expand

        Returns:
            Document containing issue content and metadata
        """
        try:
            issue = self.jira.issue(issue_key, expand=expand)

            # Process description and comments
            description = self._clean_text(issue["fields"].get("description", ""))

            # Get comments
            comments = []
            if "comment" in issue["fields"]:
                for comment in issue["fields"]["comment"]["comments"]:
                    processed_comment = self._clean_text(comment["body"])
                    created = datetime.fromisoformat(comment["created"].replace("Z", "+00:00"))
                    author = comment["author"].get("displayName", "Unknown")
                    comments.append(
                        {"body": processed_comment, "created": created.strftime("%Y-%m-%d"), "author": author}
                    )

            # Format created date
            created_date = datetime.fromisoformat(issue["fields"]["created"].replace("Z", "+00:00"))
            formatted_created = created_date.strftime("%Y-%m-%d")

            # Get custom fields
            custom_fields = {}
            for field_name, field_id in self.CUSTOM_FIELD_MAPPINGS.items():
                if field_id in issue["fields"]:
                    custom_fields[field_name] = issue["fields"][field_id]

            # Combine content in a more structured way
            content = f"""Issue: {issue_key}
Title: {issue['fields'].get('summary', '')}
Type: {issue['fields']['issuetype']['name']}
Status: {issue['fields']['status']['name']}
Created: {formatted_created}

Description:
{description}

"""
            # Add custom fields to content
            if custom_fields:
                content += "Custom Fields:\n"
                for name, value in custom_fields.items():
                    if value and not name.startswith('customfield_'):
                        content += f"{name}: {value}\n"
                content += "\n"

            content += "Comments:\n" + "\n".join(
                [f"{c['created']} - {c['author']}: {c['body']}" for c in comments]
            )

            # Streamlined metadata with only essential information
            metadata = {
                "key": issue_key,
                "title": issue["fields"].get("summary", ""),
                "type": issue["fields"]["issuetype"]["name"],
                "status": issue["fields"]["status"]["name"],
                "created_date": formatted_created,
                "priority": issue["fields"].get("priority", {}).get("name", "None"),
                "link": f"{self.config.url.rstrip('/')}/browse/{issue_key}",
                "custom_fields": custom_fields
            }

            return Document(page_content=content, metadata=metadata)

        except Exception as e:
            logger.error(f"Error fetching issue {issue_key}: {str(e)}")
            raise

    def search_issues(
        self, jql: str, fields: str = "*all", start: int = 0, limit: int = 50, expand: Optional[str] = None
    ) -> List[Document]:
        """
        Search for issues using JQL.

        Args:
            jql: JQL query string
            fields: Comma-separated string of fields to return
            start: Starting index
            limit: Maximum results to return
            expand: Fields to expand

        Returns:
            List of Documents containing matching issues
        """
        try:
            results = self.jira.jql(jql, fields=fields, start=start, limit=limit, expand=expand)

            documents = []
            for issue in results["issues"]:
                # Get full issue details
                doc = self.get_issue(issue["key"], expand=expand)
                documents.append(doc)

            return documents

        except Exception as e:
            logger.error(f"Error searching issues with JQL {jql}: {str(e)}")
            raise

    def get_project_issues(self, project_key: str, start: int = 0, limit: int = 50) -> List[Document]:
        """
        Get all issues for a project.

        Args:
            project_key: The project key
            start: Starting index
            limit: Maximum results to return

        Returns:
            List of Documents containing project issues
        """
        jql = f"project = {project_key} ORDER BY created DESC"
        return self.search_issues(jql, start=start, limit=limit)

    def create_issue(self, request: JiraIssueCreate) -> Document:
        """Create a new Jira issue (Epic or Story)."""
        try:
            # Validate project exists
            project = self.jira.project(request.project_key)
            if not project:
                raise ValueError(f"Project {request.project_key} does not exist")

            # Prepare fields
            fields = {
                "project": {"key": request.project_key},
                "summary": request.summary,
                "description": request.description,
                "issuetype": {"name": request.issue_type}
            }

            # Handle Epic specific fields
            if request.issue_type == "Epic":
                epic_name_field = self._get_custom_field_id('Epic Name')
                if epic_name_field:
                    fields[epic_name_field] = request.summary

            # Handle Story specific fields
            elif request.issue_type == "Story" and request.epic_link:
                # Validate epic exists
                epic = self.jira.issue(request.epic_link)
                if not epic or epic["fields"]["issuetype"]["name"] != "Epic":
                    raise ValueError(f"Invalid epic link: {request.epic_link}")
                epic_link_field = self._get_custom_field_id('Epic Link')
                if epic_link_field:
                    fields[epic_link_field] = request.epic_link

            # Handle custom fields
            if request.custom_fields:
                for field_name, value in request.custom_fields.items():
                    field_id = self._get_custom_field_id(field_name)
                    if field_id:
                        fields[field_id] = value

            # Create the issue
            issue = self.jira.create_issue(fields=fields)

            # Return the created issue as a Document
            return self.get_issue(issue["key"])

        except Exception as e:
            logger.error(f"Error creating issue: {str(e)}")
            raise

    def update_issue(self, request: JiraIssueUpdate) -> Document:
        """Update an existing Jira issue."""
        try:
            # Validate issue exists
            current_issue = self.jira.issue(request.issue_key)
            if not current_issue:
                raise ValueError(f"Issue {request.issue_key} does not exist")

            # Process fields for update
            fields = {}
            for field_name, value in request.fields.items():
                # Check if it's a custom field
                field_id = self._get_custom_field_id(field_name)
                if field_id:
                    fields[field_id] = value
                else:
                    # Standard field - convert to lowercase for consistency
                    fields[field_name.lower()] = value

            # Log the update request for debugging
            logger.info(f"Updating issue {request.issue_key} with fields: {fields}")

            # Use the Jira API's update_issue method
            self.jira.update_issue_field(
                request.issue_key,
                fields
            )

            # Return the updated issue as a Document
            return self.get_issue(request.issue_key)

        except Exception as e:
            logger.error(f"Error updating issue: {str(e)}")
            raise
