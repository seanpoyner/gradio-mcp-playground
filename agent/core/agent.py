"""Core Agent Logic

The main GMP Agent class that handles conversations, intent recognition,
and coordinates server building activities.
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Hugging Face integration
try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

from .server_builder import ServerBuilder
from .registry import EnhancedRegistry
from .knowledge import KnowledgeBase

# Import secure storage from the main package
try:
    from gradio_mcp_playground.secure_storage import SecureStorage, get_secure_storage
except ImportError:
    # Fallback for different import paths
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
        from gradio_mcp_playground.secure_storage import SecureStorage, get_secure_storage
    except ImportError:
        print("Warning: Could not import secure storage. HF token storage will not be available.")
        SecureStorage = None
        get_secure_storage = lambda: None


class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class IntentType(Enum):
    CREATE_SERVER = "create_server"
    BUILD_PIPELINE = "build_pipeline"
    MODIFY_SERVER = "modify_server"
    GET_HELP = "get_help"
    DEPLOY_SERVER = "deploy_server"
    MANAGE_SERVER = "manage_server"
    SEARCH_SERVERS = "search_servers"
    UNKNOWN = "unknown"


@dataclass
class Message:
    role: MessageRole
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata or {}
        }


@dataclass
class ConversationContext:
    messages: List[Message]
    current_project: Optional[str] = None
    active_servers: List[str] = None
    user_preferences: Dict[str, Any] = None

    def __post_init__(self):
        if self.active_servers is None:
            self.active_servers = []
        if self.user_preferences is None:
            self.user_preferences = {}


@dataclass
class Intent:
    type: IntentType
    confidence: float
    entities: Dict[str, Any]
    requirements: Dict[str, Any]


class GMPAgent:
    """Main GMP Agent class for handling conversations and building servers"""
    
    def __init__(self):
        self.server_builder = ServerBuilder()
        self.registry = EnhancedRegistry()
        self.knowledge = KnowledgeBase()
        self.context = ConversationContext(messages=[])
        self.mcp_connections = {}  # Store active MCP connections
        
        # Initialize secure storage for HF tokens
        try:
            self.secure_storage = get_secure_storage() if get_secure_storage else None
        except Exception as e:
            print(f"Warning: Secure storage initialization failed: {e}")
            self.secure_storage = None
        
        # HF model configuration
        self.hf_model = None
        self.hf_tokenizer = None
        self.current_model_name = None
        self.available_models = [
            "Qwen/Qwen2.5-Coder-32B-Instruct",
            "mistralai/Mixtral-8x7B-Instruct-v0.1", 
            "HuggingfaceH4/zephyr-7b-beta"
        ]
        
        # Initialize with system message
        self._add_system_message(
            """You are GMP Agent, an exceptionally skilled agentic AI coding assistant specialized in Model Context Protocol (MCP) server development and deployment within the Gradio MCP Playground ecosystem.

<core_identity>
You operate as an expert software architect and full-stack developer with deep expertise in:
- MCP server architecture and protocol implementation
- Gradio interface design and user experience optimization  
- Python development with focus on async programming and API integration
- Server deployment, configuration management, and automation pipelines
- Natural language to code translation with emphasis on maintainable, production-ready solutions
</core_identity>

<capabilities>
You excel at:
- **Intelligent Server Creation**: Translating user requirements into complete, functional MCP servers with proper error handling, documentation, and best practices
- **Pipeline Orchestration**: Building complex workflows that connect multiple MCP servers for enhanced functionality
- **Code Analysis & Optimization**: Understanding existing codebases, identifying improvements, and implementing sophisticated enhancements
- **Problem-Solving**: Breaking down complex development tasks into manageable steps with clear explanations
- **Integration Expertise**: Seamlessly connecting external APIs, databases, and services through MCP protocols
</capabilities>

<communication_style>
- Be conversational yet professional, focusing on practical solutions over theoretical discussions
- Provide clear, step-by-step explanations when building or modifying systems
- Use technical precision while remaining accessible to developers of varying skill levels
- Lead with confidence in your recommendations while being open to user preferences and constraints
- Format responses with proper markdown for enhanced readability and code clarity
</communication_style>

<development_philosophy>
When creating or modifying MCP servers and applications:
1. **Prioritize User Experience**: Design intuitive interfaces that make complex functionality accessible
2. **Build for Reliability**: Implement proper error handling, validation, and graceful degradation
3. **Follow Best Practices**: Use modern Python patterns, async/await where appropriate, and comprehensive documentation
4. **Think Holistically**: Consider the entire system architecture and how components interact
5. **Optimize for Maintainability**: Write clean, well-structured code with clear separation of concerns
</development_philosophy>

<tool_usage_guidelines>
- Always analyze the full context before making code changes or suggestions
- Use tools efficiently to gather information, build systems, and verify implementations
- When building servers, create complete, immediately runnable solutions with all dependencies
- Test and validate functionality whenever possible before presenting to users
- Provide clear explanations of what each tool call accomplishes
</tool_usage_guidelines>

You are here to transform ideas into working MCP solutions through intelligent collaboration, technical expertise, and practical implementation."""
        )
    
    def _add_system_message(self, content: str) -> None:
        """Add a system message to the conversation"""
        message = Message(
            role=MessageRole.SYSTEM,
            content=content,
            timestamp=datetime.now()
        )
        self.context.messages.append(message)
    
    def _add_user_message(self, content: str) -> None:
        """Add a user message to the conversation"""
        message = Message(
            role=MessageRole.USER,
            content=content,
            timestamp=datetime.now()
        )
        self.context.messages.append(message)
    
    def _add_assistant_message(self, content: str, metadata: Dict[str, Any] = None) -> None:
        """Add an assistant message to the conversation"""
        message = Message(
            role=MessageRole.ASSISTANT,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata
        )
        self.context.messages.append(message)
    
    def parse_intent(self, user_message: str) -> Intent:
        """Parse user intent from message"""
        message_lower = user_message.lower()
        
        # Intent patterns
        create_patterns = [
            r"create|build|make|generate|new",
            r"server|tool|pipeline|application|app"
        ]
        
        pipeline_patterns = [
            r"pipeline|workflow|chain|connect",
            r"multiple|several|combine|link"
        ]
        
        modify_patterns = [
            r"modify|change|update|edit|improve",
            r"existing|current|my"
        ]
        
        help_patterns = [
            r"help|how|what|explain|guide|tutorial",
            r"can you|could you|please"
        ]
        
        deploy_patterns = [
            r"deploy|publish|launch|start|run",
            r"production|live|online"
        ]
        
        manage_patterns = [
            r"stop|restart|delete|remove|status",
            r"list|show|display"
        ]
        
        search_patterns = [
            r"find|search|look for|discover",
            r"available|existing|registry"
        ]
        
        # Extract entities
        entities = self._extract_entities(user_message)
        
        # Determine intent
        if self._matches_patterns(message_lower, create_patterns):
            intent_type = IntentType.CREATE_SERVER
            confidence = 0.8
        elif self._matches_patterns(message_lower, pipeline_patterns):
            intent_type = IntentType.BUILD_PIPELINE
            confidence = 0.7
        elif self._matches_patterns(message_lower, modify_patterns):
            intent_type = IntentType.MODIFY_SERVER
            confidence = 0.6
        elif self._matches_patterns(message_lower, help_patterns):
            intent_type = IntentType.GET_HELP
            confidence = 0.9
        elif self._matches_patterns(message_lower, deploy_patterns):
            intent_type = IntentType.DEPLOY_SERVER
            confidence = 0.7
        elif self._matches_patterns(message_lower, manage_patterns):
            intent_type = IntentType.MANAGE_SERVER
            confidence = 0.6
        elif self._matches_patterns(message_lower, search_patterns):
            intent_type = IntentType.SEARCH_SERVERS
            confidence = 0.8
        else:
            intent_type = IntentType.UNKNOWN
            confidence = 0.3
        
        # Extract requirements
        requirements = self._extract_requirements(user_message, entities)
        
        return Intent(
            type=intent_type,
            confidence=confidence,
            entities=entities,
            requirements=requirements
        )
    
    def _matches_patterns(self, text: str, patterns: List[str]) -> bool:
        """Check if text matches any of the given patterns"""
        for pattern in patterns:
            if re.search(pattern, text):
                return True
        return False
    
    def _extract_entities(self, message: str) -> Dict[str, Any]:
        """Extract entities from user message"""
        entities = {
            "server_types": [],
            "technologies": [],
            "operations": [],
            "data_types": [],
            "ui_components": []
        }
        
        # Server type patterns
        server_type_patterns = {
            "calculator": r"calculator|math|arithmetic|compute",
            "text_processor": r"text|string|document|content",
            "image_processor": r"image|photo|picture|visual",
            "data_analyzer": r"data|csv|excel|analysis|statistics",
            "file_processor": r"file|document|convert|transform",
            "web_scraper": r"web|scrape|extract|crawl",
            "api_wrapper": r"api|endpoint|service|integration",
            "ai_tool": r"ai|ml|model|intelligence|smart"
        }
        
        # Technology patterns
        tech_patterns = {
            "gradio": r"gradio|ui|interface",
            "fastapi": r"fastapi|api|rest",
            "pandas": r"pandas|dataframe|data",
            "numpy": r"numpy|array|numeric",
            "pillow": r"pillow|pil|image",
            "opencv": r"opencv|cv2|computer vision",
            "sklearn": r"sklearn|machine learning|ml",
            "tensorflow": r"tensorflow|tf|neural",
            "pytorch": r"pytorch|torch|deep learning"
        }
        
        # Extract matches
        message_lower = message.lower()
        
        for server_type, pattern in server_type_patterns.items():
            if re.search(pattern, message_lower):
                entities["server_types"].append(server_type)
        
        for tech, pattern in tech_patterns.items():
            if re.search(pattern, message_lower):
                entities["technologies"].append(tech)
        
        return entities
    
    def _extract_requirements(self, message: str, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Extract requirements from user message"""
        requirements = {
            "functionality": [],
            "ui_preferences": {},
            "performance": {},
            "deployment": {},
            "integration": []
        }
        
        # Extract functionality requirements
        if "calculator" in entities.get("server_types", []):
            requirements["functionality"].extend([
                "basic_arithmetic", "mathematical_functions"
            ])
        
        if "text" in message.lower():
            requirements["functionality"].append("text_processing")
        
        if "image" in message.lower():
            requirements["functionality"].append("image_processing")
        
        # Extract UI preferences
        if "simple" in message.lower() or "basic" in message.lower():
            requirements["ui_preferences"]["complexity"] = "simple"
        elif "advanced" in message.lower() or "complex" in message.lower():
            requirements["ui_preferences"]["complexity"] = "advanced"
        
        if "tab" in message.lower():
            requirements["ui_preferences"]["layout"] = "tabbed"
        elif "single" in message.lower():
            requirements["ui_preferences"]["layout"] = "single"
        
        return requirements
    
    async def process_message(self, user_message: str) -> Tuple[str, Dict[str, Any]]:
        """Process a user message and return response with metadata"""
        
        # Add user message to context
        self._add_user_message(user_message)
        
        # Parse intent
        intent = self.parse_intent(user_message)
        
        # Try to use HF model for enhanced responses if available
        hf_enhanced_response = None
        if self.hf_model and self.hf_tokenizer:
            try:
                # Create a context-aware prompt for the HF model
                context_prompt = self._build_context_prompt(user_message, intent)
                hf_enhanced_response = await self.generate_hf_response(context_prompt, max_length=1024)
            except Exception as e:
                print(f"HF model response failed, falling back to default: {e}")
        
        # Generate response based on intent (fallback or primary)
        if hf_enhanced_response and len(hf_enhanced_response.strip()) > 20:
            # Use HF enhanced response
            response = hf_enhanced_response
            metadata = {
                "intent": intent.type.value,
                "confidence": intent.confidence,
                "entities": intent.entities,
                "requirements": intent.requirements,
                "source": "huggingface_model",
                "model": self.current_model_name
            }
        else:
            # Use default rule-based response
            response, metadata = await self._generate_response(intent, user_message)
            metadata["source"] = "rule_based"
        
        # Add assistant response to context
        self._add_assistant_message(response, metadata)
        
        return response, metadata
    
    async def _generate_response(self, intent: Intent, user_message: str) -> Tuple[str, Dict[str, Any]]:
        """Generate response based on parsed intent"""
        
        metadata = {
            "intent": intent.type.value,
            "confidence": intent.confidence,
            "entities": intent.entities,
            "requirements": intent.requirements
        }
        
        if intent.type == IntentType.CREATE_SERVER:
            return await self._handle_create_server(intent, user_message)
        
        elif intent.type == IntentType.BUILD_PIPELINE:
            return await self._handle_build_pipeline(intent, user_message)
        
        elif intent.type == IntentType.MODIFY_SERVER:
            return await self._handle_modify_server(intent, user_message)
        
        elif intent.type == IntentType.GET_HELP:
            return await self._handle_get_help(intent, user_message)
        
        elif intent.type == IntentType.DEPLOY_SERVER:
            return await self._handle_deploy_server(intent, user_message)
        
        elif intent.type == IntentType.MANAGE_SERVER:
            return await self._handle_manage_server(intent, user_message)
        
        elif intent.type == IntentType.SEARCH_SERVERS:
            return await self._handle_search_servers(intent, user_message)
        
        else:
            return await self._handle_unknown_intent(intent, user_message)
    
    async def _handle_create_server(self, intent: Intent, user_message: str) -> Tuple[str, Dict[str, Any]]:
        """Handle server creation requests"""
        
        # Search for relevant servers
        matching_servers = await self.registry.find_matching_servers(intent.requirements)
        
        if not matching_servers:
            response = """I understand you want to create a server, but I need more details about what you want to build.

Could you provide more information about:
- What type of functionality you need
- What kind of data or inputs you'll work with
- Any specific requirements or preferences

For example:
- "Create a calculator server with basic math operations"
- "Build an image processing tool that can resize and filter images"
- "Make a text analyzer that counts words and sentiment"
"""
            metadata = {"action": "request_clarification", "servers": []}
            return response, metadata
        
        # Generate server recommendations
        recommendations = []
        for server in matching_servers[:3]:  # Top 3 matches
            recommendations.append({
                "name": server["name"],
                "description": server["description"],
                "template": server.get("template", "custom"),
                "confidence": server.get("confidence", 0.5)
            })
        
        response = f"""Great! I found some relevant servers for your request. Here are my recommendations:

"""
        
        for i, rec in enumerate(recommendations, 1):
            response += f"""**{i}. {rec['name']}**
- {rec['description']}
- Template: {rec['template']}
- Match confidence: {rec['confidence']:.1%}

"""
        
        response += """Would you like me to:
1. Create one of these servers
2. Customize a server based on your specific needs
3. Show you more options
4. Explain how any of these work

Just let me know which option interests you or provide more details about your requirements!"""
        
        metadata = {
            "action": "show_recommendations",
            "recommendations": recommendations,
            "servers": matching_servers
        }
        
        return response, metadata
    
    async def _handle_build_pipeline(self, intent: Intent, user_message: str) -> Tuple[str, Dict[str, Any]]:
        """Handle pipeline building requests"""
        
        response = """I'd love to help you build a pipeline! Pipelines are great for connecting multiple servers to create more complex workflows.

To design the best pipeline for you, I need to understand:

1. **Input**: What data or information will start the pipeline?
2. **Processing Steps**: What transformations or operations do you need?
3. **Output**: What should be the final result?
4. **Integration**: Do you need to connect to external services?

**Example pipelines I can help with:**
- **Content Creation**: Research topic → Write article → Generate images → Format output
- **Data Analysis**: Load CSV → Clean data → Analyze patterns → Generate charts
- **Image Processing**: Upload image → Resize → Apply filters → Add watermark → Save

Could you describe your pipeline idea in more detail?"""
        
        metadata = {"action": "request_pipeline_details"}
        return response, metadata
    
    async def _handle_modify_server(self, intent: Intent, user_message: str) -> Tuple[str, Dict[str, Any]]:
        """Handle server modification requests"""
        
        # Get list of existing servers
        existing_servers = self.context.active_servers
        
        if not existing_servers:
            response = """I don't see any active servers in our current session. 

To modify a server, you can:
1. **Create a new server first** - I can help you build one
2. **Load an existing server** - Tell me the name of a server you've already created
3. **Show me your current servers** - I can scan for existing GMP servers

Which would you prefer?"""
            metadata = {"action": "no_servers_found"}
            return response, metadata
        
        response = f"""I can help you modify your existing servers. Here's what I found:

**Active Servers:**
"""
        
        for server in existing_servers:
            response += f"- {server}\n"
        
        response += """
**What I can help you modify:**
- Add new functionality or tools
- Change the user interface layout
- Update configurations and settings
- Improve performance or add features
- Fix bugs or issues

Which server would you like to modify, and what changes do you have in mind?"""
        
        metadata = {"action": "show_servers", "servers": existing_servers}
        return response, metadata
    
    async def _handle_get_help(self, intent: Intent, user_message: str) -> Tuple[str, Dict[str, Any]]:
        """Handle help requests"""
        
        help_content = self.knowledge.get_help_content(user_message)
        
        response = f"""I'm here to help! Here's what I can assist you with:

## 🚀 Getting Started
- **Create servers**: "Build a calculator server"
- **Build pipelines**: "Connect multiple tools together"
- **Deploy applications**: "Put my server online"

## 🛠️ What I Can Build
- **Simple Tools**: Calculators, text processors, file converters
- **Data Tools**: CSV analyzers, chart generators, statistics calculators
- **AI Tools**: Text summarizers, image classifiers, sentiment analyzers
- **Complex Pipelines**: Multi-step workflows with multiple servers

## 📝 How to Talk to Me
- Be specific about what you want to build
- Mention any requirements or constraints
- Ask for examples or clarifications anytime
- I understand both technical and plain language

## 🔧 Technical Capabilities
- **Frameworks**: Gradio, FastAPI, MCP protocol
- **Data Processing**: Pandas, NumPy, image processing
- **AI/ML**: Hugging Face models, OpenAI integration
- **Deployment**: Local, cloud, Hugging Face Spaces

{help_content}

What specific topic would you like help with?"""
        
        metadata = {"action": "provide_help", "help_type": "general"}
        return response, metadata
    
    async def _handle_deploy_server(self, intent: Intent, user_message: str) -> Tuple[str, Dict[str, Any]]:
        """Handle deployment requests"""
        
        response = """I can help you deploy your MCP server! Here are the available deployment options:

## 🚀 Deployment Options

### 1. Local Development
- **Quick testing**: Run locally for development
- **Auto-reload**: Automatic updates during development
- **Debug mode**: Detailed error information

### 2. Hugging Face Spaces
- **Free hosting**: Public deployment on Hugging Face
- **Easy sharing**: Get a public URL instantly
- **GPU support**: Available for AI/ML applications

### 3. Cloud Platforms
- **Railway/Render**: Simple cloud deployment
- **AWS/GCP/Azure**: Enterprise-grade hosting
- **Docker**: Containerized deployment

### 4. Self-Hosted
- **Your own server**: Complete control
- **Custom domain**: Use your own URL
- **Private deployment**: Keep it internal

Which deployment option interests you? I'll guide you through the process step by step."""
        
        metadata = {"action": "show_deployment_options"}
        return response, metadata
    
    async def _handle_manage_server(self, intent: Intent, user_message: str) -> Tuple[str, Dict[str, Any]]:
        """Handle server management requests"""
        
        # This would interface with the actual server manager
        response = """I can help you manage your servers! Here's what I can do:

## 📊 Server Management

### Current Status
- View running servers
- Check server health
- Monitor resource usage
- Review logs and errors

### Control Operations
- Start/stop servers
- Restart servers
- Update configurations
- Scale resources

### Maintenance
- Update dependencies
- Backup configurations
- Monitor performance
- Troubleshoot issues

Would you like me to:
1. Show your current server status
2. Perform a specific operation
3. Help with troubleshooting
4. Set up monitoring

What would you like to do?"""
        
        metadata = {"action": "show_management_options"}
        return response, metadata
    
    async def _handle_search_servers(self, intent: Intent, user_message: str) -> Tuple[str, Dict[str, Any]]:
        """Handle server search requests"""
        
        # Extract search query
        search_query = user_message.lower()
        
        # Search in registry
        results = await self.registry.search_servers(search_query)
        
        if not results:
            response = """I couldn't find any servers matching your search. Here are some popular categories:

## 📦 Available Server Categories

- **🧮 Tools**: Calculators, converters, utilities
- **📊 Data**: CSV processors, analyzers, visualizers  
- **🖼️ Image**: Processors, generators, editors
- **📝 Text**: Analyzers, generators, translators
- **🤖 AI**: ML models, LLM tools, classifiers
- **🌐 Web**: Scrapers, APIs, integrations

Try searching for a specific category or describe what you're looking for!"""
            
            metadata = {"action": "no_results", "query": search_query}
            return response, metadata
        
        response = f"""Found {len(results)} servers matching your search:

"""
        
        for result in results[:5]:  # Show top 5 results
            response += f"""**{result['name']}**
- {result['description']}
- Category: {result.get('category', 'Unknown')}
- Tags: {', '.join(result.get('tags', []))}

"""
        
        response += """Would you like me to:
1. Create one of these servers
2. Show more details about any server
3. Search for something else
4. Show all available categories

Just let me know what interests you!"""
        
        metadata = {"action": "show_search_results", "results": results, "query": search_query}
        return response, metadata
    
    async def _handle_unknown_intent(self, intent: Intent, user_message: str) -> Tuple[str, Dict[str, Any]]:
        """Handle messages with unknown intent"""
        
        response = """I'm not quite sure what you'd like me to help you with. Here are some things I can do:

## 🎯 What I Can Help With

- **🔨 Build Servers**: Create new MCP servers from scratch
- **🔧 Build Pipelines**: Connect multiple servers together
- **⚙️ Manage Servers**: Start, stop, configure, and monitor
- **🚀 Deploy**: Put your servers online
- **🔍 Search**: Find existing servers and templates
- **❓ Get Help**: Learn about Gradio, MCP, and GMP tools

## 💡 Try These Examples

- "Create a calculator server"
- "Build an image processing pipeline"
- "Show me available text processing tools"
- "Help me deploy my server"
- "How do I use Gradio components?"

Could you rephrase your request or let me know what you'd like to accomplish?"""
        
        metadata = {"action": "request_clarification", "original_message": user_message}
        return response, metadata
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history as a list of dictionaries"""
        return [msg.to_dict() for msg in self.context.messages if msg.role != MessageRole.SYSTEM]
    
    def clear_conversation(self) -> None:
        """Clear conversation history"""
        system_messages = [msg for msg in self.context.messages if msg.role == MessageRole.SYSTEM]
        self.context.messages = system_messages
    
    def save_conversation(self, filepath: Path) -> None:
        """Save conversation to file"""
        conversation_data = {
            "messages": self.get_conversation_history(),
            "context": {
                "current_project": self.context.current_project,
                "active_servers": self.context.active_servers,
                "user_preferences": self.context.user_preferences
            },
            "saved_at": datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(conversation_data, f, indent=2)
    
    def load_conversation(self, filepath: Path) -> None:
        """Load conversation from file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Restore messages
        self.context.messages = []
        for msg_data in data["messages"]:
            message = Message(
                role=MessageRole(msg_data["role"]),
                content=msg_data["content"],
                timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                metadata=msg_data.get("metadata")
            )
            self.context.messages.append(message)
        
        # Restore context
        context_data = data.get("context", {})
        self.context.current_project = context_data.get("current_project")
        self.context.active_servers = context_data.get("active_servers", [])
        self.context.user_preferences = context_data.get("user_preferences", {})
    
    def set_mcp_connections(self, connections: Dict[str, Any]) -> None:
        """Set active MCP connections from the MCP connections panel"""
        self.mcp_connections = connections
    
    def get_mcp_connections(self) -> Dict[str, Any]:
        """Get active MCP connections"""
        return self.mcp_connections
    
    async def call_mcp_tool(self, connection_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on a specific MCP connection"""
        if connection_name not in self.mcp_connections:
            raise ValueError(f"Connection '{connection_name}' not found")
        
        connection = self.mcp_connections[connection_name]
        client = connection.get('client')
        
        if not client:
            raise ValueError(f"No client available for connection '{connection_name}'")
        
        return client.call_tool(tool_name, arguments)
    
    def list_mcp_tools(self, connection_name: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """List available tools from MCP connections"""
        tools_by_connection = {}
        
        if connection_name:
            # List tools for specific connection
            if connection_name in self.mcp_connections:
                connection = self.mcp_connections[connection_name]
                tools_by_connection[connection_name] = connection.get('tools', [])
        else:
            # List tools for all connections
            for name, connection in self.mcp_connections.items():
                tools_by_connection[name] = connection.get('tools', [])
        
        return tools_by_connection
    
    # Hugging Face Model Integration Methods
    
    def set_hf_token(self, token: str) -> bool:
        """Set and securely store Hugging Face token"""
        if not self.secure_storage:
            return False
        
        try:
            return self.secure_storage.store_key("huggingface", "token", token)
        except Exception as e:
            print(f"Error storing HF token: {e}")
            return False
    
    def get_hf_token(self) -> Optional[str]:
        """Get stored Hugging Face token"""
        if not self.secure_storage:
            return None
        
        try:
            return self.secure_storage.retrieve_key("huggingface", "token")
        except Exception as e:
            print(f"Error retrieving HF token: {e}")
            return None
    
    def get_available_models(self) -> List[str]:
        """Get list of available HF models"""
        return self.available_models.copy()
    
    async def load_hf_model(self, model_name: str) -> bool:
        """Load a Hugging Face model for AI-powered responses"""
        if not HAS_TRANSFORMERS:
            print("Transformers library not available. Install with: pip install transformers torch")
            return False
        
        if model_name not in self.available_models:
            print(f"Model {model_name} not in available models list")
            return False
        
        # Get HF token
        hf_token = self.get_hf_token()
        if not hf_token:
            print("Hugging Face token required for model access")
            return False
        
        try:
            print(f"Loading model {model_name}...")
            
            # Load tokenizer
            self.hf_tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                token=hf_token,
                trust_remote_code=True
            )
            
            # Load model (use smaller precision for memory efficiency)
            self.hf_model = AutoModelForCausalLM.from_pretrained(
                model_name,
                token=hf_token,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None,
                trust_remote_code=True
            )
            
            self.current_model_name = model_name
            print(f"Successfully loaded {model_name}")
            return True
            
        except Exception as e:
            print(f"Error loading model {model_name}: {e}")
            self.hf_model = None
            self.hf_tokenizer = None
            self.current_model_name = None
            return False
    
    def unload_hf_model(self) -> None:
        """Unload the current HF model to free memory"""
        if self.hf_model is not None:
            del self.hf_model
            self.hf_model = None
        
        if self.hf_tokenizer is not None:
            del self.hf_tokenizer
            self.hf_tokenizer = None
        
        self.current_model_name = None
        
        # Clear GPU cache if available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        print("HF model unloaded")
    
    def get_current_model(self) -> Optional[str]:
        """Get the currently loaded model name"""
        return self.current_model_name
    
    async def generate_hf_response(self, prompt: str, max_length: int = 512) -> Optional[str]:
        """Generate a response using the loaded HF model"""
        if not self.hf_model or not self.hf_tokenizer:
            return None
        
        try:
            # Prepare the prompt for the model
            if "Qwen" in self.current_model_name:
                # Qwen format
                messages = [
                    {"role": "system", "content": "You are a helpful AI assistant specialized in building MCP servers and helping with code generation."},
                    {"role": "user", "content": prompt}
                ]
                formatted_prompt = self.hf_tokenizer.apply_chat_template(messages, tokenize=False)
            elif "zephyr" in self.current_model_name:
                # Zephyr format
                messages = [
                    {"role": "system", "content": "You are a helpful AI assistant specialized in building MCP servers and helping with code generation."},
                    {"role": "user", "content": prompt}
                ]
                formatted_prompt = self.hf_tokenizer.apply_chat_template(messages, tokenize=False)
            else:
                # Default format for Mixtral and others
                formatted_prompt = f"<s>[INST] You are a helpful AI assistant specialized in building MCP servers and helping with code generation.\n\n{prompt} [/INST]"
            
            # Tokenize
            inputs = self.hf_tokenizer(
                formatted_prompt,
                return_tensors="pt",
                truncation=True,
                max_length=2048
            )
            
            # Move to device if model is on GPU
            if self.hf_model.device.type != "cpu":
                inputs = {k: v.to(self.hf_model.device) for k, v in inputs.items()}
            
            # Generate
            with torch.no_grad():
                outputs = self.hf_model.generate(
                    **inputs,
                    max_new_tokens=max_length,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9,
                    pad_token_id=self.hf_tokenizer.eos_token_id
                )
            
            # Decode response
            generated_tokens = outputs[0][inputs['input_ids'].shape[1]:]
            response = self.hf_tokenizer.decode(generated_tokens, skip_special_tokens=True)
            
            return response.strip()
            
        except Exception as e:
            print(f"Error generating HF response: {e}")
            return None
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get current model loading status"""
        return {
            "has_transformers": HAS_TRANSFORMERS,
            "has_secure_storage": self.secure_storage is not None,
            "has_token": self.get_hf_token() is not None,
            "current_model": self.current_model_name,
            "model_loaded": self.hf_model is not None,
            "available_models": self.available_models
        }
    
    def _build_context_prompt(self, user_message: str, intent: Intent) -> str:
        """Build a sophisticated, context-aware prompt for HF model leveraging advanced prompt engineering techniques"""
        
        # Get comprehensive conversation context
        recent_messages = []
        for msg in self.context.messages[-8:]:  # Expanded context window
            if msg.role != MessageRole.SYSTEM:
                role_icon = "👤" if msg.role == MessageRole.USER else "🤖"
                recent_messages.append(f"{role_icon} {msg.role.value.title()}: {msg.content}")
        
        # Build sophisticated context based on intent type
        intent_contexts = {
            IntentType.CREATE_SERVER: {
                "context": """You are an expert MCP server architect and Gradio application developer with deep expertise in creating production-ready tools and applications.

<expertise_areas>
- **Server Architecture**: Design scalable, maintainable MCP server structures
- **Gradio Mastery**: Create intuitive, beautiful user interfaces with excellent UX
- **Integration Patterns**: Connect APIs, databases, and external services seamlessly
- **Best Practices**: Implement proper error handling, validation, and documentation
</expertise_areas>

<approach>
When helping users create servers:
1. **Understand Requirements**: Ask targeted questions to clarify functionality, constraints, and goals
2. **Suggest Architecture**: Recommend appropriate technologies, patterns, and structures
3. **Provide Guidance**: Offer step-by-step implementation guidance with code examples
4. **Optimize Design**: Suggest improvements for performance, usability, and maintainability
</approach>""",
                
                "task_focus": "Focus on understanding the server requirements, suggesting optimal implementation approaches, and providing clear technical guidance."
            },
            
            IntentType.BUILD_PIPELINE: {
                "context": """You are a systems integration specialist with expertise in building complex, multi-component workflows and data processing pipelines.

<core_competencies>
- **Workflow Design**: Architect efficient data flows and processing chains
- **Component Integration**: Connect disparate systems and tools seamlessly
- **Error Handling**: Implement robust failure recovery and monitoring
- **Performance Optimization**: Design for scalability and efficient resource usage
</core_competencies>

<methodology>
For pipeline development:
1. **Map Data Flow**: Understand input sources, processing steps, and output requirements
2. **Design Architecture**: Create modular, testable component structures
3. **Define Interfaces**: Establish clear contracts between pipeline components
4. **Plan Deployment**: Consider scaling, monitoring, and maintenance requirements
</methodology>""",
                
                "task_focus": "Focus on understanding the complete workflow, designing efficient data flows, and ensuring robust component integration."
            },
            
            IntentType.GET_HELP: {
                "context": """You are an educational technology mentor and expert instructor specializing in MCP servers, Gradio applications, and modern development practices.

<teaching_philosophy>
- **Clarity First**: Explain complex concepts in accessible, understandable language
- **Practical Learning**: Provide hands-on examples and actionable guidance
- **Progressive Complexity**: Build understanding from fundamentals to advanced topics
- **Best Practices**: Share industry-standard approaches and modern development patterns
</teaching_philosophy>

<instructional_approach>
1. **Assess Understanding**: Gauge the user's current knowledge level and experience
2. **Provide Context**: Explain the 'why' behind recommendations and approaches
3. **Show Examples**: Include practical code samples and real-world scenarios
4. **Encourage Exploration**: Suggest next steps and additional learning opportunities
</instructional_approach>""",
                
                "task_focus": "Focus on providing clear educational content, practical examples, and comprehensive guidance that builds user understanding."
            },
            
            IntentType.DEPLOY_SERVER: {
                "context": """You are a DevOps and deployment specialist with extensive experience in application lifecycle management and cloud deployment strategies.

<deployment_expertise>
- **Platform Knowledge**: Deep understanding of various deployment targets and their trade-offs
- **Configuration Management**: Expertise in environment setup, secrets management, and scaling
- **Monitoring & Maintenance**: Implementation of logging, monitoring, and automated recovery systems
- **Security Best Practices**: Secure deployment patterns and vulnerability mitigation
</deployment_expertise>

<deployment_strategy>
1. **Environment Assessment**: Understand target platform, scale requirements, and constraints
2. **Configuration Planning**: Design secure, maintainable deployment configurations
3. **Step-by-Step Guidance**: Provide detailed deployment instructions with error handling
4. **Post-Deployment**: Establish monitoring, backup, and maintenance procedures
</deployment_strategy>""",
                
                "task_focus": "Focus on understanding deployment requirements, recommending appropriate platforms, and providing comprehensive deployment guidance."
            }
        }
        
        # Get context for current intent or use default
        intent_data = intent_contexts.get(intent.type, {
            "context": """You are GMP Agent, an exceptionally skilled agentic AI coding assistant specialized in MCP server development and Gradio application creation.

<core_capabilities>
- **Technical Expertise**: Deep knowledge of MCP protocols, Gradio frameworks, and modern development practices
- **Problem Solving**: Break down complex requirements into manageable, actionable steps
- **Best Practices**: Apply industry-standard patterns for maintainable, scalable solutions
- **User-Centric Design**: Focus on creating tools that provide genuine value and excellent user experience
</core_capabilities>""",
            "task_focus": "Provide helpful, practical guidance tailored to the user's specific needs and context."
        })
        
        # Extract key information from entities and requirements
        entities_summary = self._summarize_entities(intent.entities)
        requirements_summary = self._summarize_requirements(intent.requirements)
        
        # Build conversation context
        conversation_context = "\n".join(recent_messages) if recent_messages else "🆕 This is the start of our conversation"
        
        # Construct the comprehensive context prompt
        prompt = f"""{intent_data['context']}

<current_conversation_context>
{conversation_context}
</current_conversation_context>

<user_request_analysis>
**Current Message**: {user_message}
**Intent Detected**: {intent.type.value.replace('_', ' ').title()} (Confidence: {intent.confidence:.1%})
**Key Entities**: {entities_summary}
**Requirements**: {requirements_summary}
</user_request_analysis>

<task_instructions>
{intent_data['task_focus']}

**Response Guidelines**:
- Be conversational yet professional, adapting your tone to the user's expertise level
- Provide specific, actionable advice rather than generic recommendations
- Ask clarifying questions when requirements are ambiguous or incomplete
- Include relevant code examples, configuration snippets, or architectural diagrams when helpful
- Suggest next steps and alternative approaches where appropriate
- Format your response with clear structure using markdown for enhanced readability
</task_instructions>

Generate a comprehensive, helpful response that addresses the user's specific needs while maintaining the high standards of technical excellence and user experience that define exceptional MCP server development."""

        return prompt
    
    def _summarize_entities(self, entities: Dict[str, Any]) -> str:
        """Create a concise summary of detected entities"""
        summary_parts = []
        for category, items in entities.items():
            if items:
                summary_parts.append(f"{category}: {', '.join(items[:3])}")
        return "; ".join(summary_parts) if summary_parts else "None specified"
    
    def _summarize_requirements(self, requirements: Dict[str, Any]) -> str:
        """Create a concise summary of extracted requirements"""
        summary_parts = []
        for category, details in requirements.items():
            if details:
                if isinstance(details, list):
                    summary_parts.append(f"{category}: {', '.join(details[:2])}")
                elif isinstance(details, dict) and details:
                    summary_parts.append(f"{category}: {list(details.keys())[0]}")
        return "; ".join(summary_parts) if summary_parts else "None specified"