# Open Issues and Future Improvements

This document tracks known issues, bugs, and planned improvements for the Gradio MCP Playground project.

## 🐛 Known Issues

### High Priority

1. **API Key Security**
   - Issue: API keys were previously exposed in git history
   - Status: Fixed in latest commit, but git history still contains exposed keys
   - Action: Ensure that credentials are protected from accidental exposure in all future testing.
   - Related: #security
   - **⚠️ URGENT**: Exposed keys need to be revoked immediately
   - Keys are now encrypted using SecureTokenStorage

2. **Agent Stops Using Tools After First MCP Call**
   - Issue: ReAct agent switches to just answering instead of continuing to use tools after first successful MCP tool call
   - Status: Added explicit instructions in system prompt to continue using tools
   - Action: Monitor agent behavior and consider implementing a more robust solution if issue persists
   - Related: #agent-behavior

3. **Token Limit Exceeded with Large MCP Tool Outputs**
   - Issue: MCP tools can return very large outputs (e.g., GitHub search returning entire movie scripts) that exceed model context limits
   - Status: ✅ Fixed - Implemented output truncation at 15,000 characters
   - Action: Monitor for any edge cases where truncation might cut off important information
   - Related: #mcp-tools #context-limits

### Medium Priority

3. **MCP Client Library Issues**
   - Issue: Python MCP client library has async/event loop conflicts
   - Status: Workaround implemented with custom client
   - Action: Monitor upstream library for fixes

4. **Server Startup Messages**
   - Issue: Some MCP servers print messages to stdout/stderr that interfere with JSON-RPC
   - Status: Filtering implemented, but may need refinement for new servers
   - Action: Test with more MCP server types

5. **Tool Discovery Timing**
   - Issue: Tools from MCP servers may not be immediately available after installation
   - Status: Requires dashboard restart
   - Action: Implement hot-reload for newly installed servers

### Low Priority

6. **Node.js Dependency**
   - Issue: Requires Node.js installed for MCP servers
   - Status: Expected behavior, but could be clearer
   - Action: Add Node.js installation check and helpful error messages

7. **Windows Path Handling in WSL**
   - Issue: MCP servers running in WSL need proper path translation
   - Status: Implemented path translator, but needs more testing
   - Action: Test with various path formats and edge cases

## ✨ Planned Features

### Short Term (Next Release)

1. **Hot Reload MCP Tools**
   - Allow adding MCP servers without restarting the dashboard
   - Refresh tool list dynamically

2. **MCP Server Health Monitoring**
   - Show server status in UI
   - Automatic restart for crashed servers
   - Health check endpoints

3. **Improved API Key Management UI**
   - Modal dialog for API key input
   - Key validation before storage
   - Show which servers have stored keys

4. **Better Error Messages**
   - User-friendly error messages for common issues
   - Troubleshooting guide in UI
   - Automatic error recovery suggestions

### Medium Term

5. **MCP Server Templates**
   - Pre-configured server setups for common use cases
   - One-click installation for server bundles
   - Community-contributed templates

6. **Advanced Path Management**
   - GUI for managing allowed paths for filesystem server
   - Path aliases and shortcuts
   - Cross-platform path validation

7. **MCP Server Development Tools**
   - Built-in server testing interface
   - Server debugging tools
   - Performance monitoring

8. **Multi-User Support**
   - User-specific server configurations
   - Shared vs private servers
   - Access control for tools

### Long Term

9. **MCP Server Marketplace**
   - Browse and install community servers
   - Rate and review servers
   - Automatic dependency resolution

10. **Cloud MCP Servers**
    - Support for remote MCP servers
    - Server hosting service
    - Distributed server management

## 🔧 Technical Debt

1. **Code Organization**
   - Some files have grown too large (e.g., web_ui.py, coding_agent.py)
   - Consider splitting into smaller, focused modules

2. **Test Coverage**
   - Need more comprehensive tests for MCP integration
   - Integration tests for server communication
   - Cross-platform testing automation

3. **Documentation**
   - API documentation for custom MCP client
   - Developer guide for creating MCP servers
   - Troubleshooting guide expansion

4. **Type Hints**
   - Add comprehensive type hints throughout codebase
   - Use mypy for type checking in CI

5. **Async/Await Consistency**
   - Some code mixes sync and async patterns
   - Standardize on async where appropriate

## 🤝 Contributing

If you'd like to help with any of these issues:

1. Check if an issue already exists on GitHub
2. Comment on the issue to indicate you're working on it
3. Submit a PR with your fix
4. Include tests where applicable

## 📋 Issue Labels

- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Improvements or additions to documentation
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention is needed
- `security`: Security-related issues

## 🔄 Last Updated

- Date: June 9, 2025
- Version: After implementing output truncation for MCP tools
- Next Review: June 16, 2025
- Recent changes: 
  - Added issue #2 about agent stopping tool use after first MCP call
  - Added issue #3 about token limit exceeded with large outputs (now fixed)
  - Implemented 15,000 character truncation for MCP tool outputs