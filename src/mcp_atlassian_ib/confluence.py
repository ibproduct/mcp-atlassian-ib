import logging
import os
from typing import Optional

from atlassian import Confluence
from dotenv import load_dotenv

from .config import ConfluenceConfig
from .preprocessing import TextPreprocessor
from .types import ConfluencePageCreate, ConfluencePageUpdate, Document

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger("mcp-atlassian")


class ConfluenceManager:
    """Handles all Confluence operations including fetching, creating, and updating content."""

    def __init__(self):
        url = os.getenv("CONFLUENCE_URL")
        username = os.getenv("CONFLUENCE_USERNAME")
        token = os.getenv("CONFLUENCE_API_TOKEN")

        if not all([url, username, token]):
            raise ValueError("Missing required Confluence environment variables")

        self.config = ConfluenceConfig(url=url, username=username, api_token=token)
        self.confluence = Confluence(
            url=self.config.url,
            username=self.config.username,
            password=self.config.api_token,  # API token is used as password
            cloud=True,
        )
        self.preprocessor = TextPreprocessor(self.config.url, self.confluence)

    def _process_html_content(self, html_content: str, space_key: str) -> tuple[str, str]:
        return self.preprocessor.process_html_content(html_content, space_key)

    def get_spaces(self, start: int = 0, limit: int = 10):
        """Get all available spaces."""
        return self.confluence.get_all_spaces(start=start, limit=limit)

    def get_page_content(self, page_id: str, clean_html: bool = True) -> Document:
        """Get content of a specific page."""
        page = self.confluence.get_page_by_id(page_id=page_id, expand="body.storage,version,space")
        space_key = page.get("space", {}).get("key", "")

        content = page["body"]["storage"]["value"]
        processed_html, processed_markdown = self._process_html_content(content, space_key)

        # Get author information from version
        version = page.get("version", {})
        author = version.get("by", {})

        metadata = {
            "page_id": page_id,
            "title": page["title"],
            "version": version.get("number"),
            "url": f"{self.config.url}/wiki/spaces/{space_key}/pages/{page_id}",
            "space_key": space_key,
            "author_name": author.get("displayName"),
            "space_name": page.get("space", {}).get("name", ""),
            "last_modified": version.get("when"),
        }

        return Document(page_content=processed_markdown if clean_html else processed_html, metadata=metadata)

    def get_page_by_title(self, space_key: str, title: str, clean_html: bool = True) -> Optional[Document]:
        """Get page content by space key and title."""
        try:
            page = self.confluence.get_page_by_title(space=space_key, title=title, expand="body.storage,version")

            if not page:
                return None

            content = page["body"]["storage"]["value"]
            if clean_html:
                content = self._clean_html_content(content)

            metadata = {
                "page_id": page["id"],
                "title": page["title"],
                "version": page.get("version", {}).get("number"),
                "space_key": space_key,
                "url": f"{self.config.url}/wiki/spaces/{space_key}/pages/{page['id']}",
            }

            return Document(page_content=content, metadata=metadata)

        except Exception as e:
            logger.error(f"Error fetching page: {str(e)}")
            return None

    def get_space_pages(
        self, space_key: str, start: int = 0, limit: int = 10, clean_html: bool = True
    ) -> list[Document]:
        """Get all pages from a specific space."""
        pages = self.confluence.get_all_pages_from_space(
            space=space_key, start=start, limit=limit, expand="body.storage"
        )

        documents = []
        for page in pages:
            content = page["body"]["storage"]["value"]
            if clean_html:
                content = self._clean_html_content(content)

            metadata = {
                "page_id": page["id"],
                "title": page["title"],
                "space_key": space_key,
                "version": page.get("version", {}).get("number"),
                "url": f"{self.config.url}/wiki/spaces/{space_key}/pages/{page['id']}",
            }

            documents.append(Document(page_content=content, metadata=metadata))

        return documents

    def get_page_comments(self, page_id: str, clean_html: bool = True) -> list[Document]:
        """Get all comments for a specific page."""
        page = self.confluence.get_page_by_id(page_id=page_id, expand="space")
        space_key = page.get("space", {}).get("key", "")
        space_name = page.get("space", {}).get("name", "")

        comments = self.confluence.get_page_comments(content_id=page_id, expand="body.view.value,version", depth="all")[
            "results"
        ]

        comment_documents = []
        for comment in comments:
            body = comment["body"]["view"]["value"]
            processed_html, processed_markdown = self._process_html_content(body, space_key)

            # Get author information from version.by instead of author
            author = comment.get("version", {}).get("by", {})

            metadata = {
                "page_id": page_id,
                "comment_id": comment["id"],
                "last_modified": comment.get("version", {}).get("when"),
                "type": "comment",
                "author_name": author.get("displayName"),
                "space_key": space_key,
                "space_name": space_name,
            }

            comment_documents.append(
                Document(page_content=processed_markdown if clean_html else processed_html, metadata=metadata)
            )

        return comment_documents

    def search(self, cql: str, limit: int = 10) -> list[Document]:
        """Search content using Confluence Query Language (CQL)."""
        try:
            results = self.confluence.cql(cql=cql, limit=limit)
            documents = []

            for result in results.get("results", []):
                content = result.get("content", {})
                if content.get("type") == "page":
                    metadata = {
                        "page_id": content["id"],
                        "title": result["title"],
                        "space": result.get("resultGlobalContainer", {}).get("title"),
                        "url": f"{self.config.url}{result['url']}",
                        "last_modified": result.get("lastModified"),
                        "type": content["type"],
                    }

                    # Use the excerpt as page_content since it's already a good summary
                    documents.append(Document(page_content=result.get("excerpt", ""), metadata=metadata))

            return documents
        except Exception as e:
            logger.error(f"Search failed with error: {str(e)}")
            return []

    def create_page(self, request: ConfluencePageCreate) -> Document:
        """Create a new Confluence page."""
        try:
            # Validate space exists
            space = self.confluence.get_space(request.space_key)
            if not space:
                raise ValueError(f"Space {request.space_key} does not exist")

            # Convert content to storage format if needed
            # The atlassian package handles this conversion internally

            # Create the page
            page = self.confluence.create_page(
                space=request.space_key,
                title=request.title,
                body=request.content,
                parent_id=request.parent_id,
                representation="wiki"
            )

            # Return the created page as a Document
            return self.get_page_content(page["id"])

        except Exception as e:
            logger.error(f"Error creating page: {str(e)}")
            raise

    def update_page(self, request: ConfluencePageUpdate) -> Document:
        """Update an existing Confluence page."""
        try:
            # Get current page to verify version
            current_page = self.confluence.get_page_by_id(
                page_id=request.page_id,
                expand="version"
            )

            if not current_page:
                raise ValueError(f"Page {request.page_id} does not exist")

            current_version = current_page["version"]["number"]
            if current_version != request.version:
                raise ValueError(
                    f"Version conflict: current version is {current_version}, "
                    f"but update requested for version {request.version}"
                )

            # Update the page
            page = self.confluence.update_page(
                page_id=request.page_id,
                title=request.title,
                body=request.content,
                representation="wiki"
            )

            # Return the updated page as a Document
            return self.get_page_content(page["id"])

        except Exception as e:
            logger.error(f"Error updating page: {str(e)}")
            raise
