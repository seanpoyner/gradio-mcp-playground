"""Core Agent Logic

The main GMP Agent class that handles conversations, intent recognition,
and coordinates server building activities.
"""

import asyncio
import json
import re
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Hugging Face integration
try:
    from huggingface_hub import InferenceClient
    HAS_HF_INFERENCE = True
except ImportError:
    HAS_HF_INFERENCE = False

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
    CONFIRM_BUILD = "confirm_build"
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
        self.hf_client = None
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
        
        # Check for follow-up responses first
        if hasattr(self.context, 'last_intent') and self.context.last_intent == "create_server":
            # Check if user is selecting a recommendation
            if any(word in message_lower for word in ["yes", "go ahead", "create", "build", "1", "2", "3", "first", "second", "third", "option"]):
                # Extract selection
                selection = None
                if "1" in user_message or "first" in message_lower or "option 1" in message_lower:
                    selection = 0
                elif "2" in user_message or "second" in message_lower or "option 2" in message_lower:
                    selection = 1
                elif "3" in user_message or "third" in message_lower or "option 3" in message_lower:
                    selection = 2
                elif any(word in message_lower for word in ["yes", "go ahead", "create", "build"]):
                    selection = 0  # Default to first option
                
                return Intent(
                    type=IntentType.CONFIRM_BUILD,
                    confidence=0.9,
                    entities={"selection": selection},
                    requirements={}
                )
        
        # Intent patterns
        create_patterns = [
            r"create|build|make|generate|new",
            r"server|tool|pipeline|application|app",
            r"help.*build.*server|build.*server"  # Added to match user's request
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
        
        # Special case for specific server requests
        if "sentiment analysis" in message_lower:
            entities["server_types"] = entities.get("server_types", [])
            entities["server_types"].append("ai_tool")
            entities["operations"] = entities.get("operations", [])
            entities["operations"].append("sentiment_analysis")
        
        # Determine intent
        if self._matches_patterns(message_lower, create_patterns) or "help me build" in message_lower:
            intent_type = IntentType.CREATE_SERVER
            confidence = 0.8
        elif self._matches_patterns(message_lower, pipeline_patterns):
            intent_type = IntentType.BUILD_PIPELINE
            confidence = 0.7
        elif self._matches_patterns(message_lower, modify_patterns):
            intent_type = IntentType.MODIFY_SERVER
            confidence = 0.6
        elif self._matches_patterns(message_lower, help_patterns) and not "build" in message_lower:
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
        if self.hf_client:
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
        
        elif intent.type == IntentType.CONFIRM_BUILD:
            return await self._handle_confirm_build(intent, user_message)
        
        else:
            return await self._handle_unknown_intent(intent, user_message)
    
    async def _handle_create_server(self, intent: Intent, user_message: str) -> Tuple[str, Dict[str, Any]]:
        """Handle server creation requests"""
        
        # Search for relevant servers
        matching_servers = await self.registry.find_matching_servers(intent.requirements)
        
        if not matching_servers:
            # More conversational responses based on what was detected
            if intent.entities.get("server_types"):
                server_type = intent.entities["server_types"][0]
                response = f"""I see you want to create a {server_type} server! That's a great choice.

To build exactly what you need, could you tell me more about:
- What specific features should it have?
- Who will be using it and for what purpose?
- Any particular integrations or data sources?

For instance, a {server_type} could be simple with just basic functions, or more advanced with additional capabilities. What fits your needs best?"""
            else:
                response = """I'd love to help you create a server! To get started, let me understand what you're trying to build.

Think about:
• **Purpose**: What problem will this solve?
• **Users**: Who will use this tool?
• **Features**: What functionality is essential?

Some popular servers people create:
- 🧮 **Calculators**: From simple math to complex engineering calculations
- 📊 **Data Tools**: Process CSV files, generate reports, create visualizations
- 🖼️ **Image Tools**: Resize, filter, convert, or analyze images
- 🤖 **AI Assistants**: Integrate language models for smart interactions

What type of tool would be most useful for you?"""
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
        
        # Create a more conversational response based on the number of matches
        if len(recommendations) == 1:
            rec = recommendations[0]
            response = f"""Perfect! I found exactly what you're looking for:

**{rec['name']}** - {rec['description']}

This seems like a great match for your needs (confidence: {rec['confidence']:.0%}). 

Should I go ahead and create this server for you? I can also customize it if you have specific requirements in mind."""
        
        elif len(recommendations) == 2:
            response = f"""I found a couple of options that could work well for you:

**Option 1: {recommendations[0]['name']}**
{recommendations[0]['description']}

**Option 2: {recommendations[1]['name']}**  
{recommendations[1]['description']}

Both look promising! Which one aligns better with what you have in mind? Or would you like me to create a custom solution that combines elements from both?"""
        
        else:
            response = f"""Excellent! I found several servers that match what you're looking for:

"""
            
            for i, rec in enumerate(recommendations, 1):
                response += f"""**{i}. {rec['name']}**
   {rec['description']}
   
"""
            
            response += """Each of these could work well for your project. Would you like to:
- Pick one to start with (just tell me the number)
- Hear more details about any of them
- Create a custom server that combines the best features

What sounds good to you?"""
        
        metadata = {
            "action": "show_recommendations",
            "recommendations": recommendations,
            "servers": matching_servers
        }
        
        # Store recommendations in context for follow-up
        self.context.recommendations = recommendations
        self.context.last_intent = "create_server"
        
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
        
        # Check for specific help topics in the message
        message_lower = user_message.lower()
        
        if "gradio" in message_lower:
            response = """Ah, you want to learn about Gradio! It's the foundation for creating amazing user interfaces.

**Gradio Basics:**
• **Components**: Input/output elements like textboxes, images, sliders
• **Interfaces**: Combine components into functional apps
• **Blocks**: Advanced layouts with custom styling and logic
• **Events**: Handle user interactions and updates

I can help you:
- Design intuitive interfaces for your servers
- Use advanced Gradio features like tabs and accordions
- Create interactive dashboards with real-time updates
- Style your apps with themes and custom CSS

What aspect of Gradio would you like to explore?"""
        
        elif "mcp" in message_lower or "protocol" in message_lower:
            response = """Great question about MCP (Model Context Protocol)! It's what makes our servers so powerful.

**MCP Essentials:**
• **Tools**: Define specific functions your server can perform
• **Resources**: Share data and files between servers
• **Communication**: Standard protocol for AI model integration
• **Extensibility**: Easy to add new capabilities

I can show you how to:
- Create MCP-compliant servers from scratch
- Define tools with proper schemas
- Handle errors gracefully
- Integrate with AI models and other services

What part of MCP interests you most?"""
        
        elif "example" in message_lower or "how" in message_lower:
            response = """Let me share some practical examples to get you started!

**Quick Examples:**

🧮 **Simple Calculator**:
"Create a calculator that can do basic math and square roots"

📊 **Data Analyzer**:
"Build a CSV processor that can filter data and create charts"

🖼️ **Image Tool**:
"Make an image resizer that supports multiple formats"

**How to be specific:**
- Include the main functionality you need
- Mention any special requirements
- Describe your target users

Would you like me to walk through creating any of these examples?"""
        
        else:
            response = f"""I'm here to help you succeed! Whether you're new to MCP servers or an experienced developer, I can guide you.

**Quick Start Options:**
• 🎯 **Tell me your goal** - "I need to process customer data"
• 🛠️ **Pick a template** - "Show me data processing templates"
• 📚 **Learn concepts** - "Explain how pipelines work"
• 🚀 **Jump right in** - "Create a text analysis server"

{help_content}

What would you like to explore first? Feel free to ask questions in whatever way feels natural to you!"""
        
        metadata = {"action": "provide_help", "help_type": "general"}
        return response, metadata
    
    async def _handle_confirm_build(self, intent: Intent, user_message: str) -> Tuple[str, Dict[str, Any]]:
        """Handle server build confirmation"""
        
        # Get stored recommendations
        if not hasattr(self.context, 'recommendations') or not self.context.recommendations:
            response = """I don't have any server recommendations saved from our previous conversation.

Could you remind me what type of server you wanted to create? For example:
- "I need a sentiment analysis server"
- "Create a calculator with advanced functions"
- "Build a data processing tool"

Once I understand your needs, I can recommend and build the perfect server for you!"""
            
            # Clear the last intent
            self.context.last_intent = None
            metadata = {"action": "no_recommendations"}
            return response, metadata
        
        # Get the selected recommendation
        selection = intent.entities.get("selection", 0)
        recommendations = self.context.recommendations
        
        if selection >= len(recommendations):
            selection = 0  # Default to first
        
        selected = recommendations[selection]
        
        # Build the server using ServerBuilder
        response = f"""🚀 Great choice! I'm now building your **{selected['name']}** server.

Building your server with:
📝 **Description**: {selected['description']}
🏗️ **Template**: {selected.get('template', 'custom')}

Please wait while I:
1. Generate the server code
2. Set up the configuration
3. Create the necessary files
4. Prepare it for deployment
"""
        
        try:
            # Create server spec from recommendation
            server_spec = {
                "name": selected['name'].lower().replace(" ", "_"),
                "description": selected['description'],
                "template": selected.get('template', 'custom'),
                "tools": [],  # Would be populated based on server type
                "ui_config": {
                    "components": ["inputs", "outputs"],
                    "layout": "simple"
                },
                "dependencies": []
            }
            
            # Use the server builder to generate code
            if hasattr(self, 'server_builder') and self.server_builder:
                build_result = await self.server_builder.build_server(server_spec)
                
                if build_result.get("success"):
                    response += f"""
✅ **Server built successfully!**

📁 **Location**: `{build_result.get('output_dir', 'servers/' + server_spec['name'])}`
📄 **Main file**: `server.py`

**Next steps:**
1. Navigate to the server directory
2. Install dependencies: `pip install -r requirements.txt`
3. Run the server: `python server.py`

Would you like me to:
- Show you the generated code
- Help you customize it further
- Deploy it online
- Create another server
"""
                else:
                    response += f"""
⚠️ There was an issue building the server:
{build_result.get('error', 'Unknown error')}

Don't worry! I can:
- Try a different approach
- Help you build it manually
- Suggest an alternative template

What would you prefer?"""
            else:
                # Fallback without builder - provide manual instructions
                response += f"""
✅ Here's how to create your {selected['name']} server:

**Step 1**: Create a new directory
```bash
mkdir {selected['name'].lower().replace(' ', '_')}
cd {selected['name'].lower().replace(' ', '_')}
```

**Step 2**: I'll help you create the server files:
- `server.py` - Main server implementation
- `requirements.txt` - Dependencies
- `README.md` - Documentation

Would you like me to:
1. Generate the complete server code for you
2. Walk you through building it step by step
3. Show you a similar example to customize

What works best for you?"""
        
        except Exception as e:
            response += f"""
⚠️ I encountered an issue while building the server: {str(e)}

But don't worry! I can still help you create this server. Would you like me to:
1. Try a different approach
2. Provide manual instructions
3. Show you example code to get started

Let me know how you'd like to proceed!"""
        
        # Clear the context
        self.context.last_intent = None
        self.context.recommendations = None
        
        metadata = {
            "action": "build_server",
            "server": selected,
            "status": "completed"
        }
        
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
        
        message_lower = user_message.lower().strip()
        
        # Handle greetings more naturally
        greetings = ["hello", "hi", "hey", "howdy", "greetings", "good morning", "good afternoon", "good evening"]
        if any(greeting in message_lower for greeting in greetings):
            # Check conversation history to see if this is the first greeting
            user_messages = [msg for msg in self.context.messages if msg.role == MessageRole.USER]
            
            if len(user_messages) <= 1:
                # First interaction
                response = """Hey there! 👋 I'm your MCP Agent, ready to help you build amazing servers and tools.

Whether you're looking to create a simple calculator, build a complex data processing pipeline, or deploy a full-featured application, I'm here to guide you through it.

What kind of project do you have in mind today?"""
            else:
                # Return greeting
                response = """Hello again! What can I help you with now? 

Feel free to ask me about building new servers, modifying existing ones, or anything else MCP-related."""
            
            metadata = {"action": "greeting", "conversation_length": len(user_messages)}
            return response, metadata
        
        # Handle "thanks" and appreciation
        if any(word in message_lower for word in ["thanks", "thank you", "appreciate", "helpful", "great"]):
            response = """You're welcome! I'm glad I could help. 

Is there anything else you'd like to work on? I'm here whenever you need assistance with MCP servers, pipelines, or any other development tasks."""
            
            metadata = {"action": "acknowledgment"}
            return response, metadata
        
        # Handle very short or unclear messages
        if len(message_lower.split()) <= 2:
            # Try to be more conversational based on context
            recent_topics = self._get_recent_topics()
            
            if recent_topics:
                response = f"""I see you've been working on {recent_topics[0]}. 

Would you like to continue with that, or is there something else I can help you with?"""
            else:
                response = """I'm here to help, but I need a bit more context. 

Are you looking to:
- Build something new?
- Work on an existing project?
- Learn about MCP servers?
- Get help with a specific problem?

Just let me know what's on your mind!"""
            
            metadata = {"action": "clarification_needed", "message_length": len(message_lower.split())}
            return response, metadata
        
        # Default response for unclear intent, but make it more conversational
        responses = [
            """Hmm, I'm not entirely sure what you're looking for, but I'd love to help! 

Could you tell me more about what you're trying to accomplish? For example:
- Are you building a new tool or application?
- Do you need help with an existing server?
- Looking for specific functionality?

The more details you share, the better I can assist you!""",
            
            """I want to make sure I understand exactly what you need. 

Could you elaborate on your request? Whether it's creating a new server, connecting multiple tools, or solving a specific problem, I'm here to help make it happen.""",
            
            """Let me help you get started! I can assist with various tasks:

• **Building**: Create custom MCP servers tailored to your needs
• **Connecting**: Link multiple tools into powerful pipelines
• **Deploying**: Get your servers online and accessible
• **Learning**: Understand MCP, Gradio, and best practices

What sounds most relevant to your current project?"""
        ]
        
        # Select response based on conversation context
        import random
        response = random.choice(responses)
        
        metadata = {"action": "request_clarification", "original_message": user_message}
        return response, metadata
    
    def _get_recent_topics(self) -> List[str]:
        """Extract recent topics from conversation history"""
        topics = []
        
        # Look at recent assistant messages for context
        recent_messages = [msg for msg in self.context.messages[-6:] if msg.role == MessageRole.ASSISTANT]
        
        for msg in recent_messages:
            if msg.metadata:
                # Extract topics from metadata
                if "recommendations" in msg.metadata:
                    for rec in msg.metadata["recommendations"]:
                        topics.append(rec["name"])
                elif "action" in msg.metadata:
                    action_topics = {
                        "show_recommendations": "server creation",
                        "show_deployment_options": "deployment",
                        "show_management_options": "server management",
                        "show_search_results": "server search",
                        "provide_help": "learning about MCP"
                    }
                    if msg.metadata["action"] in action_topics:
                        topics.append(action_topics[msg.metadata["action"]])
        
        return topics[:3]  # Return top 3 recent topics
    
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
        """Initialize Hugging Face Inference API client"""
        if not HAS_HF_INFERENCE:
            print("huggingface_hub library not available. Install with: pip install huggingface_hub")
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
            print(f"Initializing inference client for {model_name}...")
            
            # Create inference client
            self.hf_client = InferenceClient(
                model=model_name,
                token=hf_token
            )
            
            self.current_model_name = model_name
            print(f"Successfully connected to {model_name} via Inference API")
            return True
            
        except Exception as e:
            print(f"Error connecting to model {model_name}: {e}")
            self.hf_client = None
            self.current_model_name = None
            return False
    
    def unload_hf_model(self) -> None:
        """Disconnect from HF Inference API"""
        if self.hf_client is not None:
            self.hf_client = None
        
        self.current_model_name = None
        print("Disconnected from HF Inference API")
    
    def get_current_model(self) -> Optional[str]:
        """Get the currently loaded model name"""
        return self.current_model_name
    
    async def generate_hf_response(self, prompt: str, max_length: int = 512) -> Optional[str]:
        """Generate a response using the HF Inference API"""
        if not self.hf_client:
            return None
        
        try:
            # Prepare the messages for the model
            messages = [
                {"role": "system", "content": "You are a helpful AI assistant specialized in building MCP servers and helping with code generation."},
                {"role": "user", "content": prompt}
            ]
            
            # Use the inference API
            response = await asyncio.to_thread(
                self.hf_client.chat_completion,
                messages=messages,
                max_tokens=max_length,
                temperature=0.7,
                top_p=0.9
            )
            
            # Extract the response text
            if hasattr(response, 'choices') and len(response.choices) > 0:
                return response.choices[0].message.content.strip()
            else:
                # Fallback for different response formats
                return str(response).strip()
            
        except Exception as e:
            print(f"Error generating HF response: {e}")
            return None
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get current model loading status"""
        return {
            "has_hf_inference": HAS_HF_INFERENCE,
            "has_secure_storage": self.secure_storage is not None,
            "has_token": self.get_hf_token() is not None,
            "current_model": self.current_model_name,
            "model_connected": self.hf_client is not None,
            "available_models": self.available_models
        }
    
    def _build_context_prompt(self, user_message: str, intent: Intent) -> str:
        """Build a sophisticated, context-aware prompt for HF model leveraging advanced prompt engineering techniques"""
        
        # Get comprehensive conversation context
        recent_messages = []
        user_project_mentions = []
        previous_intents = []
        
        for msg in self.context.messages[-8:]:  # Expanded context window
            if msg.role != MessageRole.SYSTEM:
                role_icon = "👤" if msg.role == MessageRole.USER else "🤖"
                recent_messages.append(f"{role_icon} {msg.role.value.title()}: {msg.content}")
                
                # Track what the user has mentioned
                if msg.role == MessageRole.USER:
                    user_project_mentions.append(msg.content)
                
                # Track previous intents for continuity
                if msg.role == MessageRole.ASSISTANT and msg.metadata:
                    if "intent" in msg.metadata:
                        previous_intents.append(msg.metadata["intent"])
        
        # Analyze conversation flow
        is_continuation = len(previous_intents) > 0 and previous_intents[-1] == intent.type.value
        is_first_interaction = len([m for m in self.context.messages if m.role == MessageRole.USER]) <= 1
        
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
        
        # Add conversation flow context
        conversation_flow_context = ""
        if is_first_interaction:
            conversation_flow_context = "This is the user's first interaction. Be welcoming and help them get oriented."
        elif is_continuation:
            conversation_flow_context = "This continues the previous topic. Build on what was discussed."
        else:
            conversation_flow_context = "The user is shifting to a new topic. Acknowledge the transition naturally."
        
        # Construct the comprehensive context prompt
        prompt = f"""{intent_data['context']}

<current_conversation_context>
{conversation_context}
</current_conversation_context>

<conversation_flow>
{conversation_flow_context}
</conversation_flow>

<user_request_analysis>
**Current Message**: {user_message}
**Intent Detected**: {intent.type.value.replace('_', ' ').title()} (Confidence: {intent.confidence:.1%})
**Key Entities**: {entities_summary}
**Requirements**: {requirements_summary}
</user_request_analysis>

<task_instructions>
{intent_data['task_focus']}

**Response Guidelines**:
- Be conversational and friendly, using natural language that flows well
- Match the user's tone and energy level
- Use "I" statements to sound more personable ("I can help", "I found", etc.)
- Acknowledge what the user said before providing new information  
- Include specific examples relevant to their context
- Ask one clear follow-up question when appropriate
- Keep paragraphs short and scannable
- Use occasional enthusiasm when something is exciting or interesting
</task_instructions>

Generate a helpful, conversational response that feels like talking with a knowledgeable friend who happens to be an expert in MCP server development."""

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