# GitHub MCP Tools Quick Reference

## Finding Your GitHub Username

The correct way to find your GitHub username using MCP tools:

```python
# CORRECT - Use github_get_authenticated_user with no parameters
github_get_authenticated_user()
# Returns: {'login': 'your_username', 'name': 'Your Name', ...}
```

## Common GitHub Tool Patterns

### 1. Get Authenticated User Info
```python
github_get_authenticated_user()
# No parameters needed - gets info for the user whose token is configured
```

### 2. List Your Repositories
```python
github_list_repos()
# OR
github_list_repos({'owner': 'your_username'})
```

### 3. Search for Users
```python
# CORRECT - Use 'q' parameter
github_search_users({'q': 'search_term'})

# WRONG - Don't use 'username' parameter
github_search_users({'username': 'search_term'})  # This will fail!
```

### 4. Search for Repositories
```python
github_search_repos({'q': 'gradio-mcp-playground'})
```

### 5. Get Repository Details
```python
github_get_repo({'owner': 'seanpoulter', 'repo': 'gradio-mcp-playground'})
```

### 6. Get File Contents
```python
github_get_file_contents({
    'owner': 'seanpoulter',
    'repo': 'gradio-mcp-playground',
    'path': 'README.md'
})
```

## Common Mistakes to Avoid

1. **Wrong parameter names**: Always use 'q' for search queries, not 'username' or 'query'
2. **Missing parameters**: Some tools like `github_get_repo` require both 'owner' and 'repo'
3. **Assuming parameter names**: Check the actual tool signature, don't assume

## Tips for the Agent

- Start with `github_get_authenticated_user()` to get the username
- Use that username in subsequent calls that need an 'owner' parameter
- For search operations, always use the 'q' parameter
- Remember that the GitHub token is already configured, so authentication is automatic