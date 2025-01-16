# Changelog

## [0.2.1] - 2024-01-16

### Fixed
- Jira custom fields handling in issue updates
- Removed hardcoded custom field IDs
- Added better logging for custom field operations
- Improved field ID lookup to handle both names and IDs

## [0.2.0] - 2024-01-16

### Added
- Create and update operations for Confluence pages
- Create and update operations for Jira issues (Epics and Stories)
- Custom fields support, particularly for Acceptance Criteria
- Improved error handling and validation for all operations

### Changed
- Renamed package from mcp-atlassian to mcp-atlassian-ib for IntelligenceBank fork
- Updated server name and logger to reflect IntelligenceBank branding
- Enhanced documentation with new capabilities and examples

### Fixed
- Jira update functionality with proper custom field handling
- Custom field mapping and validation
- REST API implementation for better control

## [0.1.7] - 2024-03-20

### Changed
- Optimized Confluence search performance by removing individual page fetching
- Updated search results format to use pre-generated excerpts

## [0.1.6] - 2024-03-19

### Changed
- Lowered minimum Python version requirement from 3.13 to 3.10 for broader compatibility

## [0.1.5] - 2024-12-19

### Fixed
- Aligned comment metadata keys in Confluence comments endpoint
- Fixed handling of nested structure in Confluence spaces response
- Updated README.md with improved documentation
