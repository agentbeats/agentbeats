# AgentBeats Assets SDK

## Overview

The AgentBeats Assets SDK provides functionality to upload files to the backend for frontend access. This is a lightweight client that focuses on simplicity and security, letting the backend handle all the heavy lifting.

## Function Reference

### `static_expose()`

Upload a file to the backend for frontend access.

#### Parameters

- `file_path` (str): Path to the file to upload
- `asset_name` (Optional[str]): Custom name for the asset (defaults to filename)
- `battle_id` (Optional[str]): Battle ID for battle assets (required for battle assets)
- `uploaded_by` (Optional[str]): ID of the entity uploading the asset
- `url` (str): Backend server URL (defaults to http://localhost:9000)

#### Returns

- `str`: URL to access the uploaded asset

#### Raises

- `FileNotFoundError`: If the file doesn't exist
- `PermissionError`: If the file can't be read
- `ValueError`: If battle_id is not provided
- `Exception`: If upload fails

#### Example

```python
from agentbeats.utils.assets import static_expose

# Upload a battle report
url = static_expose(
    file_path="/path/to/report.txt",
    asset_name="battle_report.txt",
    battle_id="battle_2024_001",
    uploaded_by="agent_123"
)

print(f"Asset available at: {url}")
```

## Security Features

The SDK is designed with security in mind:

- **Backend-only validation**: All security checks happen server-side
- **No local storage**: Files are uploaded directly to the backend
- **Clean interface**: Minimal attack surface
- **Error handling**: Proper exception handling and reporting

## Backend Integration

The SDK works with the AgentBeats backend which provides:

- File upload endpoints
- Security validation (file type, size, content)
- Asset management and retrieval
- Static asset serving

## Error Handling

The SDK provides clear error messages for common issues:

- File not found
- Permission denied
- Missing required parameters
- Backend upload failures

## Best Practices

1. **Always provide battle_id**: Required for proper asset organization
2. **Use descriptive asset names**: Helps with asset management
3. **Handle exceptions**: Wrap calls in try-catch blocks
4. **Validate file existence**: Check if file exists before uploading
5. **Use appropriate URLs**: Point to the correct backend instance

## Migration from Legacy SDK

If you're migrating from the previous version:

- Remove calls to `get_asset_url()`, `list_exposed_assets()`, etc.
- Use only `static_expose()` for file uploads
- Remove local storage configuration
- Update error handling to use the new exception types

## Configuration

The SDK uses sensible defaults but can be customized:

- Default backend URL: `http://localhost:9000`
- Upload timeout: 30 seconds
- No local storage fallback

## Testing

The SDK includes comprehensive tests:

- File upload functionality
- Error handling
- Integration with backend
- Security validation

Run tests with:
```bash
python tests/test_sdk_upload.py
python tests/test_security.py
``` 