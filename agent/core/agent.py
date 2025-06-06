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

from .server_builder import ServerBuilder
from .registry import EnhancedRegistry
from .knowledge import KnowledgeBase


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
        
        # Initialize with system message
        self._add_system_message(
            "I am the GMP Agent, an intelligent assistant for building and managing "
            "MCP servers using the Gradio MCP Playground toolkit. I can help you "
            "create servers, build pipelines, and deploy applications in natural language."
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
        
        # Generate response based on intent
        response, metadata = await self._generate_response(intent, user_message)
        
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