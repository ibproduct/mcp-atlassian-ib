# MCP Atlassian Integration Extensions

This document outlines the implementation plan for extending the MCP Atlassian integration with additional Confluence and Jira capabilities.

## Project Scope

### New Capabilities

1. Confluence Content Management
   - Create new pages with optional parent relationships
   - Update existing pages with version control

2. Jira Issue Management
   - Create Epic issues
   - Create Story issues with optional Epic linking
   - Update existing issues

## Technical Implementation

### 1. Type System Extensions (types.py)

```python
@dataclass
class ConfluencePageCreate:
    space_key: str          # Target Confluence space
    title: str             # Page title
    content: str           # Page content (markdown/wiki)
    parent_id: Optional[str] # Optional parent page ID

@dataclass
class ConfluencePageUpdate:
    page_id: str           # Page to update
    title: str            # New title
    content: str          # New content
    version: int          # Current version number

@dataclass
class JiraIssueCreate:
    project_key: str       # Target project
    summary: str          # Issue summary
    description: str      # Issue description
    issue_type: str       # 'Epic' or 'Story'
    epic_link: Optional[str] # For stories only

@dataclass
class JiraIssueUpdate:
    issue_key: str        # Issue to update
    fields: Dict[str, any] # Fields to update
```

### 2. Manager Classes

#### ConfluenceManager (confluence.py)
Extends the existing ConfluenceFetcher class with content creation/update capabilities:

```python
class ConfluenceManager(ConfluenceFetcher):
    def create_page(self, create_request: ConfluencePageCreate) -> Document:
        # Content conversion
        # Parent relationship handling
        # Page creation via API
        
    def update_page(self, update_request: ConfluencePageUpdate) -> Document:
        # Version control
        # Content updates
        # Change tracking
```

#### JiraManager (jira.py)
Extends the existing JiraFetcher class with issue creation/update capabilities:

```python
class JiraManager(JiraFetcher):
    def create_issue(self, create_request: JiraIssueCreate) -> Document:
        # Issue type handling
        # Epic/Story specific fields
        # Epic linking for stories
        
    def update_issue(self, update_request: JiraIssueUpdate) -> Document:
        # Field validation
        # Update processing
        # Change tracking
```

### 3. MCP Tool Definitions

New tools to be added to the server:

1. confluence_create_page
   - Create new Confluence pages
   - Handle parent relationships
   - Convert content formats

2. confluence_update_page
   - Update existing pages
   - Handle version control
   - Maintain content integrity

3. jira_create_epic
   - Create Epic issues
   - Handle Epic-specific fields
   - Set up Epic metadata

4. jira_create_story
   - Create Story issues
   - Handle Epic linking
   - Set up Story fields

5. jira_update_issue
   - Update any issue type
   - Handle field validation
   - Process changes

### 4. Implementation Considerations

#### Content Handling
- Markdown to Confluence storage format conversion
- Wiki markup processing
- Attachment handling
- Content validation

#### Error Handling
- Version conflicts
- Permission issues
- Invalid field values
- Missing dependencies
- API failures

#### Validation
- Space/Project existence
- Required fields
- Valid issue types
- Parent/Epic relationships
- User permissions

### 5. Testing Strategy

1. Unit Tests
   - Manager class methods
   - Content conversion
   - Field validation
   - Error handling

2. Integration Tests
   - API interactions
   - Content creation/updates
   - Issue management
   - Error scenarios

3. Tool Interface Tests
   - Input validation
   - Output formatting
   - Error reporting

## Development Phases

1. Phase 1: Core Implementation
   - Type system extensions
   - Basic manager class functionality
   - Essential error handling

2. Phase 2: Tool Integration
   - MCP tool definitions
   - Tool handlers
   - Input/output processing

3. Phase 3: Enhanced Features
   - Content format conversion
   - Advanced validation
   - Relationship handling

4. Phase 4: Testing & Documentation
   - Unit test suite
   - Integration tests
   - API documentation
   - Usage examples

## Success Criteria

1. Functionality
   - All new operations work as specified
   - Proper error handling
   - Data integrity maintained

2. Reliability
   - Stable API interactions
   - Consistent error handling
   - Version control effectiveness

3. Usability
   - Clear tool interfaces
   - Helpful error messages
   - Comprehensive documentation

4. Maintainability
   - Clean code structure
   - Comprehensive tests
   - Clear documentation