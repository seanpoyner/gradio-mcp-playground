# GMP Agent User Guide

Welcome to the GMP Agent - your intelligent assistant for building and managing MCP servers! This comprehensive guide will help you get the most out of the agent's capabilities.

## 📚 Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Concepts](#basic-concepts)
3. [Using the Chat Interface](#using-the-chat-interface)
4. [Building Your First Server](#building-your-first-server)
5. [Advanced Features](#advanced-features)
6. [Pipeline Builder](#pipeline-builder)
7. [Server Management](#server-management)
8. [Deployment Options](#deployment-options)
9. [Troubleshooting](#troubleshooting)
10. [Tips & Best Practices](#tips--best-practices)

## 🚀 Getting Started

### Prerequisites

Before using the GMP Agent, ensure you have:

- Python 3.8 or higher
- The parent GMP (Gradio MCP Playground) project installed
- Basic understanding of what you want to build

### Installation

1. **Navigate to the agent directory:**
   ```bash
   cd /path/to/gradio-mcp-playground/agent
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Launch the agent:**
   ```bash
   python app.py
   ```

4. **Open your browser** and go to `http://localhost:8080`

### First Launch

When you first open the GMP Agent, you'll see:

- 🤖 **Chat Interface**: The main conversation area
- 🔧 **Pipeline Builder**: Visual tool for complex workflows  
- 🖥️ **Server Manager**: Monitor and control your servers
- 📚 **Help & Examples**: Documentation and sample prompts

## 🧠 Basic Concepts

### What is an MCP Server?

An **MCP Server** is a web application that:
- Provides tools and functions that AI models can use
- Has a web interface built with Gradio
- Follows the Model Context Protocol (MCP) standard
- Can be connected to AI applications and workflows

### What Can You Build?

The GMP Agent can help you create:

- **Simple Tools**: Calculators, text processors, converters
- **Data Tools**: CSV analyzers, chart generators, statistics calculators  
- **AI Tools**: Text summarizers, image classifiers, content generators
- **Complex Pipelines**: Multi-step workflows combining multiple servers
- **Custom Integrations**: API wrappers, database interfaces, automation tools

### How Does It Work?

1. **Describe Your Idea**: Tell the agent what you want to build in plain language
2. **Get Recommendations**: The agent suggests relevant servers and templates
3. **Build Together**: The agent generates code, configurations, and documentation
4. **Test & Deploy**: Use built-in tools to test locally and deploy online

## 💬 Using the Chat Interface

### Starting a Conversation

The chat interface is your primary way to interact with the agent. Here's how to get started:

**Good Opening Messages:**
- "I want to create a calculator server"
- "Build me a tool that can analyze CSV files"
- "Help me understand how MCP servers work"
- "Show me what templates are available"

**Be Specific About:**
- What type of functionality you need
- What kind of data you'll work with
- Any specific requirements or constraints
- Your technical skill level

### Example Conversations

#### Building a Simple Calculator

```
You: Create a basic calculator server

Agent: I'll help you create a calculator server! I found a perfect template that includes:
- Basic arithmetic operations (+, -, *, /)
- Mathematical functions (sin, cos, sqrt, etc.)
- Expression evaluation with error handling
- Clean Gradio interface

Would you like me to create this server for you?

You: Yes, create it

Agent: Perfect! I'm building your calculator server...
[Build progress updates]
✅ Calculator server created successfully!
Location: ./calculator-server/
You can start it with: python app.py
```

#### Building a Data Analysis Tool

```
You: I need a tool that can analyze CSV files and create charts

Agent: Great idea! I'll help you build a data analysis server. Based on your needs, I recommend:

1. **CSV Upload & Processing**: File upload with pandas integration
2. **Data Visualization**: Charts using matplotlib/plotly
3. **Statistical Analysis**: Basic statistics and summaries
4. **Export Options**: Download results and charts

Should I create this as a single comprehensive tool or separate components you can connect together?

You: Single comprehensive tool please

Agent: Building your data analysis server with all features integrated...
```

### Chat Features

#### Context Awareness
The agent remembers your conversation and can reference previous topics:

```
You: Create a calculator
Agent: [Creates calculator]

You: Now add graphing capabilities to it
Agent: I'll modify your calculator server to include graphing...
```

#### Suggestions Panel
Look for the "💡 Context & Suggestions" section for:
- Next steps you can take
- Related functionality you might want
- Tips for improving your server
- Deployment recommendations

#### Quick Examples
Use the dropdown menu for instant examples:
- "Create a basic calculator server"
- "Build an image processing pipeline" 
- "Make a text analyzer with sentiment analysis"
- And more...

## 🔨 Building Your First Server

Let's walk through creating your first MCP server step by step.

### Step 1: Choose Your Project

Think about what you want to build:

**For Beginners:**
- Simple calculator
- Text case converter
- Unit converter
- Basic file processor

**For Intermediate Users:**
- Data analyzer
- Image processor
- API wrapper
- Multi-tool interface

**For Advanced Users:**
- AI-powered tools
- Complex pipelines
- Custom integrations
- Performance-optimized servers

### Step 2: Start the Conversation

Open the chat interface and describe your project:

```
"I want to create a [TYPE] that can [FUNCTION] with [DATA/INPUT]"
```

**Examples:**
- "I want to create a calculator that can handle basic math and scientific functions"
- "I want to create a text tool that can analyze sentiment and word count"
- "I want to create a data tool that can process CSV files and generate charts"

### Step 3: Review Recommendations

The agent will suggest:
- **Relevant templates** that match your needs
- **Similar servers** you can customize
- **Required components** for your functionality
- **Complexity assessment** and time estimates

### Step 4: Confirm and Build

Once you're happy with the recommendation:

```
You: "Yes, create the first option"
   or
You: "Create option 2 but add [SPECIFIC FEATURE]"
   or  
You: "Combine options 1 and 3"
```

### Step 5: Test Your Server

After building, the agent will:
- Show you the generated code
- Provide testing instructions
- Start the server automatically (if requested)
- Give you the access URL

### Step 6: Customize Further

You can ask for modifications:
- "Add a dark mode toggle"
- "Include file upload capability" 
- "Make the interface more colorful"
- "Add input validation"

## 🚀 Advanced Features

### Server Templates

The GMP Agent includes several built-in templates:

#### Basic Templates
- **basic**: Simple single-function server
- **calculator**: Mathematical operations and functions
- **text-processor**: Text manipulation utilities

#### Data Templates  
- **data-analyzer**: CSV processing and analysis
- **file-processor**: File conversion and manipulation
- **api-wrapper**: External API integration

#### AI Templates
- **image-generator**: AI image creation
- **llm-tools**: LLM-powered utilities
- **sentiment-analyzer**: Text sentiment analysis

#### Advanced Templates
- **multi-tool**: Multiple tools in tabs
- **custom-ui**: Advanced Gradio components
- **pipeline**: Connected server workflow

### Customization Options

#### UI Customization
```
You: "Make the interface use a dark theme"
You: "Add a file upload area"
You: "Use tabs instead of a single page"
You: "Add progress bars for long operations"
```

#### Functionality Enhancement
```
You: "Add input validation"
You: "Include error handling for edge cases"
You: "Add support for multiple file formats"
You: "Include data export options"
```

#### Performance Optimization
```
You: "Optimize for large files"
You: "Add caching for repeated operations"
You: "Make it handle multiple users"
You: "Add asynchronous processing"
```

### Integration Capabilities

#### External APIs
```
You: "Connect this to the OpenAI API"
You: "Add weather data from a weather service"
You: "Integrate with Google Sheets"
```

#### Databases
```
You: "Add SQLite database storage"
You: "Connect to a PostgreSQL database"
You: "Include data persistence"
```

#### File Systems
```
You: "Save results to local files"
You: "Add cloud storage integration"
You: "Include backup functionality"
```

## 🔧 Pipeline Builder

The Pipeline Builder lets you create complex workflows by connecting multiple servers.

### When to Use Pipelines

**Good Use Cases:**
- **Content Creation**: Research → Write → Generate Images → Format
- **Data Processing**: Load → Clean → Analyze → Visualize → Report
- **Image Workflow**: Upload → Resize → Filter → Enhance → Save
- **Document Processing**: Upload → Extract → Analyze → Summarize → Export

### Building Your First Pipeline

1. **Open Pipeline Builder** tab
2. **Add Servers** from the library or create new ones
3. **Connect Servers** by defining data flow
4. **Configure Settings** for each component
5. **Test the Pipeline** with sample data
6. **Deploy** when ready

### Pipeline Types

#### Sequential Pipeline
Data flows from one server to the next:
```
Input → Server A → Server B → Server C → Output
```

#### Parallel Pipeline  
Multiple servers process data simultaneously:
```
Input → Server A ↘
       Server B → Combine → Output
       Server C ↗
```

#### Conditional Pipeline
Different paths based on conditions:
```
Input → Analyzer → If condition A: Server X
                → If condition B: Server Y
                → Else: Server Z → Output
```

### Pipeline Configuration

#### Data Flow Settings
- **Data Format**: JSON, Text, Binary, Custom
- **Error Handling**: Stop on error, Skip failed steps, Retry
- **Timeouts**: Per-step and total pipeline timeouts
- **Logging**: Debug, Info, Warning, Error levels

#### Performance Settings
- **Parallel Processing**: Enable concurrent execution
- **Caching**: Store intermediate results
- **Memory Management**: Optimize for large datasets
- **Rate Limiting**: Control processing speed

## 🖥️ Server Management

The Server Manager helps you monitor and control all your MCP servers.

### Server Overview

#### Server Status Dashboard
- **Total Servers**: Count of all your servers
- **Running/Stopped**: Current status overview  
- **Recent Activity**: Latest server events
- **System Resources**: CPU and memory usage

#### Server List
View all servers with:
- Name and description
- Current status (Running/Stopped/Error)
- Port numbers and URLs
- Last modified dates
- Server types and templates

### Server Controls

#### Basic Operations
- **▶️ Start**: Launch a stopped server
- **⏹️ Stop**: Shut down a running server  
- **🔄 Restart**: Restart a server (useful for applying changes)
- **🗑️ Delete**: Remove a server permanently

#### Advanced Operations
- **🌐 Open in Browser**: Quick access to server interface
- **📝 View Code**: Examine server source code
- **⚙️ Edit Config**: Modify server settings
- **💾 Backup**: Create server backup

### Monitoring & Logs

#### Live Monitoring
- **Real-time Logs**: See server activity as it happens
- **Performance Metrics**: CPU, memory, response times
- **Error Tracking**: Monitor and analyze errors
- **Request Statistics**: Usage patterns and trends

#### Log Management
- **Filter by Level**: Error, Warning, Info, Debug
- **Search Logs**: Find specific events or patterns
- **Export Logs**: Download for external analysis
- **Log Retention**: Automatic cleanup of old logs

### Server Settings

#### Global Settings
- **Default Port**: Starting port for new servers
- **Auto-start**: Start servers on system boot
- **Log Retention**: How long to keep log files
- **Memory Limits**: Maximum memory per server

#### Per-Server Settings
- **Port Configuration**: Custom port assignments
- **Public Access**: Enable/disable public URLs
- **Authentication**: Password protection
- **SSL/HTTPS**: Secure connections

## 🌐 Deployment Options

The GMP Agent supports multiple deployment targets for your servers.

### Local Development

**Best For**: Testing, development, private use

**Setup:**
```bash
python app.py
```

**Features:**
- Instant startup
- Easy debugging
- Full console access
- No external dependencies

### Hugging Face Spaces

**Best For**: Public demos, sharing with others, free hosting

**Deployment Process:**
1. Tell the agent: "Deploy to Hugging Face Spaces"
2. Provide your Hugging Face token (one-time setup)
3. Choose space visibility (public/private)
4. Agent handles upload and configuration

**Features:**
- Free hosting
- Automatic SSL
- Global CDN
- Easy sharing with public URLs

### Railway

**Best For**: Production apps, custom domains, scaling

**Deployment Process:**
1. Connect Railway account
2. Agent creates optimized Dockerfile
3. Automatic deployment and scaling
4. Custom domain configuration

**Features:**
- Automatic scaling
- Custom domains
- Database integration
- Production monitoring

### Custom Server

**Best For**: Enterprise, specific requirements, existing infrastructure

**Requirements:**
- Server with Python environment
- Web server (nginx, apache)
- Process manager (systemd, supervisor)
- SSL certificate (optional)

**Agent Assistance:**
- Generates deployment scripts
- Creates systemd service files
- Provides nginx configuration
- Sets up monitoring

### Deployment Best Practices

#### Pre-Deployment Checklist
- ✅ Test server locally
- ✅ Verify all dependencies
- ✅ Check security settings
- ✅ Review resource requirements
- ✅ Test with sample data

#### Security Considerations
- **Environment Variables**: Store sensitive data securely
- **Authentication**: Add password protection if needed
- **Rate Limiting**: Prevent abuse
- **Input Validation**: Sanitize all inputs
- **HTTPS**: Use SSL for production

#### Performance Optimization
- **Caching**: Implement appropriate caching
- **Resource Limits**: Set memory and CPU limits
- **Connection Pooling**: For database connections
- **Monitoring**: Set up health checks

## 🛠️ Troubleshooting

### Common Issues

#### Server Won't Start

**Symptoms**: Error messages when starting server
**Possible Causes**:
- Port already in use
- Missing dependencies
- Configuration errors
- Permission issues

**Solutions**:
```
You: "My server won't start, I'm getting an error about port 7860"
Agent: I see the issue! Port 7860 is already in use. Let me help you:
1. Check what's using the port
2. Choose a different port
3. Update your server configuration
```

#### Server Crashes During Use

**Symptoms**: Server stops unexpectedly
**Possible Causes**:
- Memory issues
- Unhandled exceptions
- Invalid input data
- Resource limits

**Solutions**:
- Check server logs in the Monitoring tab
- Ask the agent: "Help me debug server crashes"
- Review error messages and stack traces

#### Slow Performance

**Symptoms**: Server responds slowly
**Possible Causes**:
- Large file processing
- Inefficient algorithms
- Memory constraints
- Network issues

**Solutions**:
```
You: "My image processing server is very slow"
Agent: Let me help optimize it! I can:
1. Add image compression
2. Implement batch processing
3. Use more efficient algorithms
4. Add progress indicators
```

#### UI Issues

**Symptoms**: Interface doesn't look right
**Possible Causes**:
- Browser compatibility
- CSS conflicts
- Component errors
- Theme issues

**Solutions**:
- Try different browser
- Clear browser cache
- Ask agent for UI fixes
- Check console for errors

### Getting Help

#### From the Agent
```
You: "I'm having trouble with [SPECIFIC ISSUE]"
You: "My server is giving error: [ERROR MESSAGE]"  
You: "How do I fix [PROBLEM]?"
You: "Why isn't [FEATURE] working?"
```

#### Error Messages
When you see error messages:
1. **Copy the full error** text
2. **Share it with the agent** in chat
3. **Describe what you were doing** when it happened
4. **Include any relevant details** about your setup

#### Debug Mode
Enable debug mode for detailed information:
```bash
python app.py --log-level debug
```

### Prevention Tips

#### Regular Maintenance
- Update dependencies regularly
- Monitor server logs
- Test with various inputs
- Backup configurations
- Review performance metrics

#### Best Practices
- Start simple and add complexity gradually
- Test each feature thoroughly
- Use proper error handling
- Document your servers
- Keep backups of working versions

## 💡 Tips & Best Practices

### Effective Communication with the Agent

#### Be Specific
**Instead of**: "Make a tool"
**Try**: "Create a CSV analyzer that can generate bar charts"

**Instead of**: "Add features"  
**Try**: "Add file upload, data validation, and export to PDF"

#### Provide Context
- Mention your skill level
- Describe your use case
- Share any constraints or requirements
- Explain your goals

#### Iterate Gradually
- Start with basic functionality
- Test thoroughly
- Add features one at a time
- Ask for explanations when needed

### Server Design Best Practices

#### User Experience
- **Clear Labels**: Use descriptive input/output labels
- **Help Text**: Add placeholder text and descriptions
- **Error Messages**: Provide helpful error information
- **Progress Indicators**: Show progress for long operations

#### Code Quality
- **Error Handling**: Always validate inputs
- **Documentation**: Add clear docstrings
- **Comments**: Explain complex logic
- **Testing**: Test with various inputs

#### Performance
- **Efficient Algorithms**: Choose appropriate methods
- **Memory Management**: Handle large data carefully
- **Caching**: Cache expensive operations
- **Async Processing**: Use for I/O operations

### Project Organization

#### Server Naming
- Use descriptive names
- Follow consistent conventions
- Avoid special characters
- Keep names reasonable length

#### File Organization
```
my-server/
├── app.py              # Main application
├── requirements.txt    # Dependencies
├── README.md          # Documentation
├── config.json        # Configuration
├── tests/             # Test files
└── docs/              # Additional docs
```

#### Version Control
- Use git for version control
- Commit frequently with clear messages
- Tag stable versions
- Backup before major changes

### Scaling and Growth

#### Starting Small
1. **Build MVP**: Minimum viable product first
2. **Test Early**: Get feedback quickly
3. **Iterate Often**: Make improvements based on use
4. **Document Changes**: Keep track of modifications

#### Growing Your Server
1. **Add Features Gradually**: One at a time
2. **Monitor Performance**: Watch for slowdowns
3. **Get User Feedback**: Listen to your users
4. **Plan for Scale**: Consider future growth

#### Advanced Features
- **API Integration**: Connect to external services
- **Database Storage**: Persist data
- **User Authentication**: Add login systems
- **Custom Themes**: Brand your interface
- **Mobile Optimization**: Make it mobile-friendly

### Community and Sharing

#### Sharing Your Servers
- **Deploy Publicly**: Use Hugging Face Spaces
- **Write Documentation**: Help others understand
- **Share Examples**: Provide sample inputs
- **Get Feedback**: Learn from users

#### Contributing Back
- **Report Issues**: Help improve the agent
- **Share Templates**: Contribute new templates
- **Write Guides**: Help other users
- **Join Discussions**: Participate in community

---

## 🎉 Conclusion

Congratulations! You now have a comprehensive understanding of the GMP Agent. Remember:

- **Start Simple**: Begin with basic servers and grow complexity
- **Ask Questions**: The agent is here to help - don't hesitate to ask
- **Experiment**: Try different approaches and features
- **Share**: Show off your creations to the community
- **Have Fun**: Building with the GMP Agent should be enjoyable!

### Next Steps

1. **Build Your First Server**: Try the examples in this guide
2. **Explore Templates**: Look at different server types
3. **Join the Community**: Connect with other users
4. **Share Your Work**: Deploy and showcase your servers

### Additional Resources

- **[CLAUDE.md](../CLAUDE.md)**: Technical development guide
- **[Examples](../examples/)**: Sample servers and conversations
- **[GitHub Issues](https://github.com/gradio-mcp-playground/issues)**: Report problems or request features

Happy building! 🚀