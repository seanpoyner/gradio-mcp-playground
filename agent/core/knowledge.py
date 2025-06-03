"""Knowledge Base Module

Expert knowledge about Gradio, MCP protocol, and GMP toolkit for providing
intelligent assistance and recommendations.
"""

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class KnowledgeItem:
    """Represents a piece of knowledge"""
    topic: str
    content: str
    examples: List[str]
    related_topics: List[str]
    difficulty_level: str  # "beginner", "intermediate", "advanced"


class KnowledgeBase:
    """Expert knowledge base for Gradio, MCP, and GMP"""
    
    def __init__(self):
        self.knowledge_items = {}
        self._initialize_knowledge()
    
    def _initialize_knowledge(self) -> None:
        """Initialize the knowledge base with expert information"""
        
        # Gradio Knowledge
        self._add_gradio_knowledge()
        
        # MCP Protocol Knowledge
        self._add_mcp_knowledge()
        
        # GMP Toolkit Knowledge
        self._add_gmp_knowledge()
        
        # Best Practices
        self._add_best_practices()
        
        # Common Patterns
        self._add_common_patterns()
    
    def _add_gradio_knowledge(self) -> None:
        """Add Gradio-specific knowledge"""
        
        self.knowledge_items["gradio_basics"] = KnowledgeItem(
            topic="Gradio Basics",
            content="""
Gradio is a Python library for creating web interfaces for machine learning models and functions.

Key Concepts:
- Interface: Simple function-to-UI wrapper
- Blocks: More flexible layout system
- Components: Input/output elements like Textbox, Button, Image
- Events: User interactions that trigger functions

Basic Structure:
```python
import gradio as gr

def my_function(input_text):
    return f"You said: {input_text}"

demo = gr.Interface(
    fn=my_function,
    inputs=gr.Textbox(label="Input"),
    outputs=gr.Textbox(label="Output")
)

demo.launch()
```
            """,
            examples=[
                "Simple text processor",
                "Image classifier",
                "Calculator interface"
            ],
            related_topics=["gradio_components", "gradio_blocks", "gradio_events"],
            difficulty_level="beginner"
        )
        
        self.knowledge_items["gradio_components"] = KnowledgeItem(
            topic="Gradio Components",
            content="""
Gradio provides many input and output components:

Input Components:
- Textbox: Text input
- Number: Numeric input
- Slider: Range selection
- Dropdown: Selection from options
- Checkbox: Boolean input
- File: File upload
- Image: Image upload
- Audio: Audio upload

Output Components:
- Textbox: Text display
- Image: Image display
- Audio: Audio playback
- Video: Video playback
- HTML: Custom HTML
- JSON: Structured data
- Plot: Charts and graphs

Layout Components:
- Row: Horizontal layout
- Column: Vertical layout
- Tabs: Tabbed interface
- Accordion: Collapsible sections
            """,
            examples=[
                "Multi-input form",
                "File processing interface",
                "Data visualization dashboard"
            ],
            related_topics=["gradio_blocks", "gradio_layout"],
            difficulty_level="intermediate"
        )
        
        self.knowledge_items["gradio_blocks"] = KnowledgeItem(
            topic="Gradio Blocks",
            content="""
Blocks provide more control over layout and interactivity:

```python
with gr.Blocks() as demo:
    gr.Markdown("# My App")
    
    with gr.Row():
        input_box = gr.Textbox(label="Input")
        output_box = gr.Textbox(label="Output")
    
    btn = gr.Button("Process")
    btn.click(my_function, inputs=input_box, outputs=output_box)
```

Key Features:
- Custom layouts with Row/Column
- Multiple event handlers
- State management
- Dynamic UI updates
- Custom CSS and theming
            """,
            examples=[
                "Multi-step workflow",
                "Interactive dashboard",
                "Complex form processing"
            ],
            related_topics=["gradio_events", "gradio_state"],
            difficulty_level="intermediate"
        )
    
    def _add_mcp_knowledge(self) -> None:
        """Add MCP protocol knowledge"""
        
        self.knowledge_items["mcp_basics"] = KnowledgeItem(
            topic="MCP Protocol Basics",
            content="""
Model Context Protocol (MCP) enables AI applications to securely access external data and tools.

Core Concepts:
- Servers: Provide tools and resources to AI applications
- Clients: AI applications that use MCP servers
- Tools: Functions that can be called by AI models
- Resources: Data sources like files, databases, APIs

MCP Server Structure:
- Tool definitions with schemas
- Request/response handling
- Security and authentication
- Error handling and validation

Benefits:
- Standardized integration
- Secure tool access
- Composable architecture
- AI model compatibility
            """,
            examples=[
                "File system access",
                "Database queries",
                "API integrations",
                "Custom tool development"
            ],
            related_topics=["mcp_servers", "mcp_tools", "mcp_security"],
            difficulty_level="intermediate"
        )
        
        self.knowledge_items["mcp_tools"] = KnowledgeItem(
            topic="MCP Tools",
            content="""
MCP tools are functions that AI models can call to perform actions:

Tool Definition:
```python
{
    "name": "calculate",
    "description": "Perform mathematical calculations",
    "input_schema": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Mathematical expression to evaluate"
            }
        },
        "required": ["expression"]
    }
}
```

Best Practices:
- Clear, descriptive names
- Detailed descriptions
- Proper input validation
- Comprehensive error handling
- Appropriate response formats
            """,
            examples=[
                "Calculator functions",
                "File operations",
                "Data processing",
                "API calls"
            ],
            related_topics=["mcp_schemas", "mcp_validation"],
            difficulty_level="intermediate"
        )
    
    def _add_gmp_knowledge(self) -> None:
        """Add GMP toolkit knowledge"""
        
        self.knowledge_items["gmp_cli"] = KnowledgeItem(
            topic="GMP CLI Commands",
            content="""
The GMP CLI provides commands for managing Gradio MCP servers:

Core Commands:
- `gmp setup`: Configure GMP environment
- `gmp server create <name>`: Create new server
- `gmp server list`: Show all servers
- `gmp server start <name>`: Start a server
- `gmp server stop <name>`: Stop a server
- `gmp registry search <query>`: Find servers
- `gmp dashboard`: Launch web dashboard

Server Management:
- Template-based creation
- Configuration management
- Lifecycle operations
- Deployment support

Registry Operations:
- Search available servers
- Browse categories
- Install from templates
- Publish custom servers
            """,
            examples=[
                "Creating a calculator server",
                "Deploying to Hugging Face",
                "Managing multiple servers",
                "Searching for templates"
            ],
            related_topics=["gmp_templates", "gmp_deployment"],
            difficulty_level="beginner"
        )
        
        self.knowledge_items["gmp_templates"] = KnowledgeItem(
            topic="GMP Templates",
            content="""
GMP provides templates for common server types:

Available Templates:
- basic: Simple single-tool server
- calculator: Mathematical operations
- image-generator: AI image generation
- data-analyzer: CSV and data analysis
- file-processor: File manipulation
- web-scraper: Web data extraction
- llm-tools: LLM-powered utilities
- api-wrapper: External API integration
- multi-tool: Multiple tools in tabs

Template Structure:
- app.py: Main application file
- requirements.txt: Dependencies
- README.md: Documentation
- config.json: Configuration (optional)

Customization:
- Modify templates for specific needs
- Add custom components
- Integrate external services
- Create reusable patterns
            """,
            examples=[
                "Customizing calculator template",
                "Adding new tool to multi-tool",
                "Creating domain-specific template",
                "Template inheritance patterns"
            ],
            related_topics=["gmp_customization", "gradio_components"],
            difficulty_level="intermediate"
        )
    
    def _add_best_practices(self) -> None:
        """Add best practices knowledge"""
        
        self.knowledge_items["ui_design"] = KnowledgeItem(
            topic="UI Design Best Practices",
            content="""
Guidelines for creating effective Gradio interfaces:

Layout Principles:
- Clear visual hierarchy
- Logical grouping of elements
- Consistent spacing and alignment
- Responsive design considerations

User Experience:
- Intuitive input/output flow
- Clear labels and descriptions
- Helpful error messages
- Progress indicators for long operations
- Keyboard shortcuts where appropriate

Performance:
- Lazy loading for heavy components
- Efficient state management
- Minimal re-rendering
- Appropriate caching strategies

Accessibility:
- Descriptive labels
- Keyboard navigation
- Screen reader compatibility
- Color contrast considerations
            """,
            examples=[
                "Multi-step wizard interface",
                "Real-time data dashboard",
                "File processing workflow",
                "Form validation patterns"
            ],
            related_topics=["gradio_blocks", "performance_optimization"],
            difficulty_level="intermediate"
        )
        
        self.knowledge_items["error_handling"] = KnowledgeItem(
            topic="Error Handling",
            content="""
Robust error handling for MCP servers:

Error Types:
- Input validation errors
- Processing exceptions
- External service failures
- Resource limitations
- Network timeouts

Best Practices:
- Validate inputs early
- Provide clear error messages
- Log errors for debugging
- Graceful degradation
- User-friendly error display

Implementation:
```python
def process_data(input_data):
    try:
        # Validate input
        if not input_data:
            return "Error: Input is required"
        
        # Process data
        result = perform_operation(input_data)
        return result
        
    except ValueError as e:
        return f"Invalid input: {str(e)}"
    except Exception as e:
        logger.error(f"Processing error: {e}")
        return "An error occurred during processing"
```
            """,
            examples=[
                "Input validation patterns",
                "API error handling",
                "File processing errors",
                "Resource limit handling"
            ],
            related_topics=["input_validation", "logging"],
            difficulty_level="intermediate"
        )
    
    def _add_common_patterns(self) -> None:
        """Add common implementation patterns"""
        
        self.knowledge_items["data_processing"] = KnowledgeItem(
            topic="Data Processing Patterns",
            content="""
Common patterns for data processing in MCP servers:

File Upload Processing:
```python
def process_file(file):
    if file is None:
        return "Please upload a file"
    
    try:
        # Read file based on type
        if file.name.endswith('.csv'):
            df = pd.read_csv(file.name)
        elif file.name.endswith('.json'):
            with open(file.name) as f:
                data = json.load(f)
        
        # Process data
        result = analyze_data(data)
        return result
        
    except Exception as e:
        return f"Error processing file: {e}"
```

Batch Processing:
- Progress tracking
- Error recovery
- Partial results
- Memory management

Real-time Processing:
- Streaming data
- WebSocket connections
- Event-driven updates
- Rate limiting
            """,
            examples=[
                "CSV analysis pipeline",
                "Image batch processing",
                "Real-time data monitoring",
                "Multi-file workflows"
            ],
            related_topics=["file_handling", "performance_optimization"],
            difficulty_level="intermediate"
        )
        
        self.knowledge_items["integration_patterns"] = KnowledgeItem(
            topic="Integration Patterns",
            content="""
Patterns for integrating external services:

API Integration:
```python
import httpx

async def call_external_api(data):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.example.com/process",
            json=data,
            timeout=30.0
        )
        return response.json()
```

Database Integration:
- Connection pooling
- Transaction management
- Query optimization
- Error recovery

Authentication:
- API keys management
- OAuth flows
- Token refresh
- Secure storage

Rate Limiting:
- Request throttling
- Backoff strategies
- Queue management
- Error handling
            """,
            examples=[
                "REST API wrapper",
                "Database query interface",
                "OAuth authentication flow",
                "Rate-limited service calls"
            ],
            related_topics=["api_integration", "security"],
            difficulty_level="advanced"
        )
    
    def get_help_content(self, query: str) -> str:
        """Get help content based on query"""
        
        query_lower = query.lower()
        
        # Match specific topics
        for topic_id, item in self.knowledge_items.items():
            if any(keyword in query_lower for keyword in topic_id.split("_")):
                return self._format_help_item(item)
        
        # General help based on keywords
        if "gradio" in query_lower:
            return self._get_gradio_help()
        elif "mcp" in query_lower:
            return self._get_mcp_help()
        elif "gmp" in query_lower:
            return self._get_gmp_help()
        elif any(word in query_lower for word in ["error", "problem", "issue"]):
            return self._get_troubleshooting_help()
        else:
            return self._get_general_help()
    
    def _format_help_item(self, item: KnowledgeItem) -> str:
        """Format a knowledge item for display"""
        
        help_text = f"\n## {item.topic}\n\n{item.content.strip()}\n"
        
        if item.examples:
            help_text += f"\n**Examples:**\n"
            for example in item.examples:
                help_text += f"- {example}\n"
        
        if item.related_topics:
            help_text += f"\n**Related Topics:** {', '.join(item.related_topics)}\n"
        
        return help_text
    
    def _get_gradio_help(self) -> str:
        """Get Gradio-specific help"""
        return """
## Gradio Help

Gradio is the UI framework we use for creating web interfaces. Here are key concepts:

**Interface vs Blocks:**
- Use `gr.Interface` for simple function wrappers
- Use `gr.Blocks` for complex layouts and interactions

**Common Components:**
- `gr.Textbox()`: Text input/output
- `gr.Button()`: Clickable buttons
- `gr.File()`: File uploads
- `gr.Image()`: Image handling
- `gr.Plot()`: Charts and graphs

**Layout:**
- `gr.Row()`: Horizontal arrangement
- `gr.Column()`: Vertical arrangement
- `gr.Tab()`: Tabbed interface

**Events:**
- `.click()`: Button clicks
- `.change()`: Input changes
- `.submit()`: Form submissions

Need help with a specific component or pattern? Just ask!
        """
    
    def _get_mcp_help(self) -> str:
        """Get MCP protocol help"""
        return """
## MCP Protocol Help

MCP (Model Context Protocol) enables AI applications to access external tools and data.

**Key Concepts:**
- **Servers**: Provide tools and resources
- **Tools**: Functions AI models can call
- **Schemas**: Define tool inputs and outputs

**Tool Definition:**
Tools need clear names, descriptions, and input schemas. The AI model uses these to understand how to call your tools.

**Best Practices:**
- Use descriptive tool names and descriptions
- Validate all inputs thoroughly
- Handle errors gracefully
- Return structured, useful outputs

**Common Patterns:**
- Data processing tools
- File manipulation utilities
- API integration wrappers
- Calculation and analysis tools

Want to learn about implementing specific MCP features? Let me know!
        """
    
    def _get_gmp_help(self) -> str:
        """Get GMP toolkit help"""
        return """
## GMP Toolkit Help

The Gradio MCP Playground (GMP) toolkit helps you build and manage MCP servers.

**Key Commands:**
- `gmp setup`: First-time configuration
- `gmp server create <name>`: Create new server
- `gmp server list`: View your servers
- `gmp dashboard`: Web management interface

**Templates:**
GMP includes templates for common server types:
- Calculator servers
- Data analysis tools
- Image processing utilities
- API wrappers
- Multi-tool interfaces

**Workflow:**
1. Choose or create a template
2. Customize for your needs
3. Test locally
4. Deploy when ready

**Integration:**
GMP servers work seamlessly with AI applications that support MCP protocol.

Need help with a specific GMP command or workflow? Just ask!
        """
    
    def _get_troubleshooting_help(self) -> str:
        """Get troubleshooting help"""
        return """
## Troubleshooting Help

Common issues and solutions:

**Server Won't Start:**
- Check port availability
- Verify dependencies are installed
- Review error logs
- Validate configuration files

**Tools Not Working:**
- Verify input schemas
- Check function implementations
- Test with simple inputs
- Review error messages

**UI Issues:**
- Check component compatibility
- Verify event handlers
- Test with different browsers
- Review CSS conflicts

**Performance Problems:**
- Optimize heavy operations
- Implement proper caching
- Use async/await appropriately
- Monitor resource usage

**Deployment Issues:**
- Check environment variables
- Verify network connectivity
- Review security settings
- Test locally first

For specific errors, share the error message and I can provide targeted help!
        """
    
    def _get_general_help(self) -> str:
        """Get general help"""
        return """
## General Help

I can help you with:

**Building Servers:**
- Choose the right template
- Implement custom functionality
- Design effective user interfaces
- Handle errors and edge cases

**Technical Questions:**
- Gradio component usage
- MCP protocol implementation
- GMP toolkit commands
- Integration patterns

**Best Practices:**
- Code organization
- Security considerations
- Performance optimization
- User experience design

**Deployment:**
- Local testing
- Cloud deployment
- Configuration management
- Monitoring and maintenance

Just describe what you're trying to accomplish or ask about specific topics!
        """
    
    def get_recommendations(self, context: Dict[str, Any]) -> List[str]:
        """Get recommendations based on context"""
        
        recommendations = []
        
        # Analyze current project context
        if context.get("server_type") == "calculator":
            recommendations.extend([
                "Consider adding advanced mathematical functions",
                "Implement expression validation for security",
                "Add support for multiple number formats",
                "Include mathematical constant definitions"
            ])
        
        elif context.get("server_type") == "data_analyzer":
            recommendations.extend([
                "Add data visualization capabilities",
                "Implement statistical analysis functions",
                "Support multiple file formats (CSV, Excel, JSON)",
                "Include data cleaning utilities"
            ])
        
        elif context.get("complexity") == "beginner":
            recommendations.extend([
                "Start with simple Interface components",
                "Focus on clear input/output patterns",
                "Add comprehensive error handling",
                "Include helpful user guidance"
            ])
        
        elif context.get("complexity") == "advanced":
            recommendations.extend([
                "Use Blocks for complex layouts",
                "Implement state management",
                "Add asynchronous processing",
                "Consider performance optimization"
            ])
        
        return recommendations[:5]  # Return top 5 recommendations
    
    def validate_implementation(self, code: str) -> Dict[str, Any]:
        """Validate implementation against best practices"""
        
        issues = []
        suggestions = []
        
        # Check for basic error handling
        if "try:" not in code and "except:" not in code:
            issues.append("Missing error handling - consider adding try/except blocks")
        
        # Check for input validation
        if "if" not in code or "return" not in code:
            suggestions.append("Add input validation to handle edge cases")
        
        # Check for documentation
        if '"""' not in code:
            suggestions.append("Add docstrings to document your functions")
        
        # Check for Gradio best practices
        if "gr.Interface" in code and "gr.Blocks" in code:
            suggestions.append("Choose either Interface or Blocks - mixing both can be confusing")
        
        # Check for security issues
        if "eval(" in code:
            issues.append("Using eval() can be dangerous - consider safer alternatives")
        
        return {
            "issues": issues,
            "suggestions": suggestions,
            "overall_score": max(0, 10 - len(issues) * 2 - len(suggestions))
        }
    
    def get_code_examples(self, topic: str) -> List[str]:
        """Get code examples for a specific topic"""
        
        examples = {
            "basic_interface": [
                '''import gradio as gr

def greet(name):
    return f"Hello {name}!"

demo = gr.Interface(fn=greet, inputs="text", outputs="text")
demo.launch()''',
                
                '''import gradio as gr

def calculate(expression):
    try:
        result = eval(expression)
        return str(result)
    except:
        return "Error: Invalid expression"

demo = gr.Interface(
    fn=calculate,
    inputs=gr.Textbox(label="Expression"),
    outputs=gr.Textbox(label="Result")
)
demo.launch()'''
            ],
            
            "blocks_layout": [
                '''import gradio as gr

with gr.Blocks() as demo:
    gr.Markdown("# My Calculator")
    
    with gr.Row():
        input_box = gr.Textbox(label="Expression")
        result_box = gr.Textbox(label="Result")
    
    calculate_btn = gr.Button("Calculate")
    
    def calculate(expr):
        try:
            return str(eval(expr))
        except:
            return "Error"
    
    calculate_btn.click(calculate, input_box, result_box)

demo.launch()'''
            ],
            
            "file_processing": [
                '''import gradio as gr
import pandas as pd

def analyze_csv(file):
    if file is None:
        return "Please upload a CSV file"
    
    try:
        df = pd.read_csv(file.name)
        summary = f"Rows: {len(df)}, Columns: {len(df.columns)}"
        return summary
    except Exception as e:
        return f"Error: {str(e)}"

demo = gr.Interface(
    fn=analyze_csv,
    inputs=gr.File(label="Upload CSV"),
    outputs=gr.Textbox(label="Analysis")
)
demo.launch()'''
            ]
        }
        
        return examples.get(topic, [])
    
    def search_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """Search knowledge base"""
        
        results = []
        query_lower = query.lower()
        
        for topic_id, item in self.knowledge_items.items():
            score = 0
            
            # Search in topic
            if query_lower in item.topic.lower():
                score += 0.5
            
            # Search in content
            if query_lower in item.content.lower():
                score += 0.3
            
            # Search in examples
            for example in item.examples:
                if query_lower in example.lower():
                    score += 0.2
            
            if score > 0:
                results.append({
                    "topic_id": topic_id,
                    "item": item,
                    "score": score
                })
        
        # Sort by relevance
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:5]  # Return top 5 results