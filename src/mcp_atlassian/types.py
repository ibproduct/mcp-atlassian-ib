from dataclasses import dataclass
from typing import Dict, Optional, Any


@dataclass
class Document:
    """Class to represent a document with content and metadata."""

    page_content: str
    metadata: Dict[str, any]


@dataclass
class ConfluencePageCreate:
    """Request parameters for creating a new Confluence page."""

    space_key: str
    title: str
    content: str
    parent_id: Optional[str] = None


@dataclass
class ConfluencePageUpdate:
    """Request parameters for updating an existing Confluence page."""

    page_id: str
    title: str
    content: str
    version: int


@dataclass
class JiraIssueCreate:
    """Request parameters for creating a new Jira issue (Epic or Story)."""

    project_key: str
    summary: str
    description: str
    issue_type: str  # 'Epic' or 'Story'
    epic_link: Optional[str] = None  # For stories only
    custom_fields: Optional[Dict[str, Any]] = None  # Custom fields like Acceptance Criteria
    
    def __post_init__(self):
        """Validate issue_type after initialization."""
        if self.issue_type not in ['Epic', 'Story']:
            raise ValueError("issue_type must be either 'Epic' or 'Story'")
        if self.issue_type == 'Epic' and self.epic_link is not None:
            raise ValueError("Epic issues cannot have an epic_link")
        self.custom_fields = self.custom_fields or {}


@dataclass
class JiraIssueUpdate:
    """Request parameters for updating an existing Jira issue."""

    issue_key: str
    fields: Dict[str, any]  # Fields to update, including custom fields
