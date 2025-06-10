"""Agent Builder - Creates new Gradio agents using system prompts and AI generation

This module handles the creation of new agents using prompts from leaked-system-prompts
and the existing agent infrastructure.
"""
import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
import textwrap

# Hugging Face integration  
try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

# Import secure storage from the main package
try:
    from gradio_mcp_playground.secure_storage import SecureStorage, get_secure_storage
except ImportError:
    try:
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
        from gradio_mcp_playground.secure_storage import SecureStorage, get_secure_storage
    except ImportError:
        print("Warning: Could not import secure storage. HF token storage will not be available.")
        SecureStorage = None
        get_secure_storage = lambda: None


@dataclass
class AgentBlueprint:
    """Represents an agent to be built"""
    name: str
    description: str
    category: str
    difficulty: str
    features: List[str]
    system_prompt: str
    ui_components: Dict[str, Any]
    dependencies: List[str]
    code_template: str


class SystemPromptManager:
    """Manages fetching and processing system prompts from GitHub"""
    
    def __init__(self, mcp_connections: Dict[str, Any] = None):
        self.mcp_connections = mcp_connections or {}
        self.prompt_cache = {}
        
    async def fetch_system_prompts(self) -> Dict[str, str]:
        """Fetch available system prompts from the GitHub repository"""
        try:
            # Use GitHub MCP to get repository contents
            if "github" in self.mcp_connections:
                github_client = self.mcp_connections["github"]
                
                # Get list of prompt files
                files_result = await github_client.call_tool(
                    "f1e_get_file_contents",
                    {
                        "owner": "jujumilk3",
                        "repo": "leaked-system-prompts",
                        "path": ""
                    }
                )
                
                prompts = {}
                if files_result and isinstance(files_result, list):
                    for file_info in files_result:
                        if file_info.get("type") == "file" and file_info.get("name", "").endswith(".md"):
                            name = file_info["name"].replace(".md", "")
                            # Only include relevant prompts for agent building
                            if any(keyword in name.lower() for keyword in [
                                "claude", "cursor", "v0", "github-copilot", "openai", "anthropic"
                            ]):
                                prompts[name] = file_info["path"]
                
                return prompts
                
        except Exception as e:
            print(f"Error fetching system prompts: {e}")
            
        # Return fallback prompts
        return {
            "claude-3.5-sonnet": "High-quality conversational AI assistant",
            "cursor-ide-agent": "Advanced coding assistant with IDE integration", 
            "v0-interface-builder": "UI/UX component generation specialist",
            "github-copilot": "Code generation and completion assistant"
        }
    
    async def get_prompt_content(self, prompt_name: str) -> str:
        """Get the actual content of a system prompt"""
        try:
            # Use GitHub MCP to get the prompt content
            if "github" in self.mcp_connections:
                github_client = self.mcp_connections["github"]
                
                file_result = await github_client.call_tool(
                    "f1e_get_file_contents",
                    {
                        "owner": "jujumilk3",
                        "repo": "leaked-system-prompts", 
                        "path": f"{prompt_name}.md"
                    }
                )
                
                if file_result and "content" in file_result:
                    import base64
                    content = base64.b64decode(file_result["content"]).decode('utf-8')
                    return content
                    
        except Exception as e:
            print(f"Error fetching prompt content for {prompt_name}: {e}")
            
        # Return fallback content based on prompt name
        return self._get_fallback_prompt(prompt_name)
    
    def _get_fallback_prompt(self, prompt_name: str) -> str:
        """Get fallback prompt content for known prompt types"""
        fallback_prompts = {
            "claude-artifacts": "You are Claude, an AI assistant. You excel at generating code artifacts for interactive applications. When creating artifacts, focus on creating complete, functional components that users can interact with.",
            "anthropic-claude-3.5-sonnet": "You are Claude, created by Anthropic. You are helpful, harmless, and honest. You excel at reasoning, analysis, math, coding, creative writing, and answering questions.",
            "v0": "You are v0, Vercel's AI assistant. You excel at creating web applications using React, Next.js, and modern web technologies. You generate complete, runnable code with beautiful UIs.",
            "cursor-ide-sonnet": "You are a powerful AI coding assistant. You excel at understanding code, making precise edits, and helping developers build applications efficiently.",
            "github-copilot-chat": "You are GitHub Copilot, an AI pair programmer. You help developers write better code faster by providing intelligent suggestions and assistance."
        }
        
        return fallback_prompts.get(prompt_name, "You are a helpful AI assistant specialized in creating Gradio applications.")
        if prompt_name in self.prompt_cache:
            return self.prompt_cache[prompt_name]
            
        try:
            if "github" in self.mcp_connections:
                github_client = self.mcp_connections["github"]
                
                # Construct the filename
                filename = f"{prompt_name}.md"
                
                result = await github_client.call_tool(
                    "f1e_get_file_contents",
                    {
                        "owner": "jujumilk3", 
                        "repo": "leaked-system-prompts",
                        "path": filename
                    }
                )
                
                if result and "content" in result:
                    content = result["content"]
                    self.prompt_cache[prompt_name] = content
                    return content
                    
        except Exception as e:
            print(f"Error fetching prompt content for {prompt_name}: {e}")
            
        # Return a basic fallback prompt
        return f"You are a helpful AI assistant specialized in {prompt_name.replace('-', ' ')}."


class AgentCodeGenerator:
    """Generates Gradio agent code using system prompts and templates"""
    
    def __init__(self):
        self.base_template = self._load_base_template()
        
    def _load_base_template(self) -> str:
        """Load the base agent template"""
        return '''"""
{agent_name}

AGENT_INFO = {{
    "name": "{display_name}",
    "description": "{description}",
    "category": "{category}",
    "difficulty": "{difficulty}",
    "features": {features},
    "version": "1.0.0",
    "author": "Agent Builder System"
}}
"""
import gradio as gr
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
{additional_imports}

class {class_name}:
    """Main agent class implementing the core functionality"""
    
    def __init__(self):
        self.system_prompt = """{system_prompt}"""
        self.conversation_history = []
        self.agent_state = {{
            "initialized": True,
            "last_activity": datetime.now(),
            "user_preferences": {{}},
            "session_data": {{}}
        }}
        
    def process_request(self, user_input: str, *args) -> Tuple[str, Any]:
        """Process user request and generate response"""
        try:
            # Add user message to history
            self.conversation_history.append({{
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now()
            }})
            
            # Generate response based on system prompt and context
            response = self._generate_response(user_input, *args)
            
            # Add assistant response to history
            self.conversation_history.append({{
                "role": "assistant", 
                "content": response,
                "timestamp": datetime.now()
            }})
            
            return response, self.agent_state
            
        except Exception as e:
            error_msg = f"Error processing request: {{str(e)}}"
            return error_msg, self.agent_state
    
    def _generate_response(self, user_input: str, *args) -> str:
        """Generate response using the agent's system prompt"""
        # This is where the actual AI/LLM integration would happen
        # For now, provide a structured response based on the system prompt
        
        context = f"""
System: {{self.system_prompt}}

User: {{user_input}}

Based on the system prompt and user input, provide a helpful response.
"""
        
        # Simple response generation - in a real implementation this would
        # integrate with HuggingFace models or other AI services
        response = self._create_contextual_response(user_input)
        
        return response
    
    def _create_contextual_response(self, user_input: str) -> str:
        """Create a contextual response based on the agent's specialization"""
        # Analyze user input and generate appropriate response
        user_lower = user_input.lower()
        
        # Default helpful response
        response = f"""I understand you're asking about: {{user_input}}

As a {category} specialist, I can help you with:
{help_features}

What specific aspect would you like me to focus on?"""
        
        return response
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the conversation history"""
        return self.conversation_history
    
    def clear_conversation(self) -> None:
        """Clear the conversation history"""
        self.conversation_history = []
        self.agent_state["last_activity"] = datetime.now()
    
    def update_preferences(self, preferences: Dict[str, Any]) -> None:
        """Update user preferences"""
        self.agent_state["user_preferences"].update(preferences)

# Create agent instance
{instance_name} = {class_name}()

# Enhanced Gradio interface
{gradio_interface}

if __name__ == "__main__":
    interface.launch(
        server_port=int(os.environ.get('AGENT_PORT', 7860)),
        share=False,
        inbrowser=False
    )
'''

    def generate_gradio_interface(self, blueprint: AgentBlueprint) -> str:
        """Generate the Gradio interface code"""
        
        # Determine interface complexity based on category
        if blueprint.category.lower() in ["data science", "analysis"]:
            return self._generate_data_interface(blueprint)
        elif blueprint.category.lower() in ["automation", "tools"]:
            return self._generate_automation_interface(blueprint)
        elif blueprint.category.lower() in ["creative", "content"]:
            return self._generate_creative_interface(blueprint)
        else:
            return self._generate_default_interface(blueprint)
    
    def _generate_default_interface(self, blueprint: AgentBlueprint) -> str:
        """Generate a default chat-style interface"""
        return f'''with gr.Blocks(title="{blueprint.name}", theme=gr.themes.Soft()) as interface:
    gr.Markdown("""
    # {blueprint.name}
    **{blueprint.description}**
    
    ## Features:
    {chr(10).join(f"- {feature}" for feature in blueprint.features)}
    """)
    
    with gr.Row():
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(
                label="Conversation",
                height=400,
                show_label=True,
                container=True,
                type="messages"
            )
            
            with gr.Row():
                user_input = gr.Textbox(
                    label="Message",
                    placeholder="How can I help you?",
                    lines=2,
                    scale=4,
                    show_label=False
                )
                send_btn = gr.Button("Send", variant="primary", scale=1)
        
        with gr.Column(scale=1):
            clear_btn = gr.Button("Clear Conversation")
            
            gr.Markdown("## Agent Status")
            status_display = gr.JSON(value=agent_instance.agent_state, label="Status")
    
    def handle_message(message, history):
        if not message.strip():
            return history, "", agent_instance.agent_state
        
        response, state = agent_instance.process_request(message)
        
        history.append({{"role": "user", "content": message}})
        history.append({{"role": "assistant", "content": response}})
        
        return history, "", state
    
    def clear_conversation():
        agent_instance.clear_conversation()
        return [], agent_instance.agent_state
    
    send_btn.click(
        handle_message,
        inputs=[user_input, chatbot],
        outputs=[chatbot, user_input, status_display]
    )
    
    user_input.submit(
        handle_message,
        inputs=[user_input, chatbot],
        outputs=[chatbot, user_input, status_display]
    )
    
    clear_btn.click(
        clear_conversation,
        outputs=[chatbot, status_display]
    )'''

    def _generate_data_interface(self, blueprint: AgentBlueprint) -> str:
        """Generate interface for data science agents"""
        return f'''with gr.Blocks(title="{blueprint.name}", theme=gr.themes.Soft()) as interface:
    gr.Markdown("""
    # {blueprint.name}
    **{blueprint.description}**
    """)
    
    with gr.Tab("Data Upload"):
        file_upload = gr.File(
            label="Upload Data",
            file_types=[".csv", ".json", ".xlsx"],
            file_count="single"
        )
        upload_btn = gr.Button("Process Data", variant="primary")
        
    with gr.Tab("Analysis"):
        with gr.Row():
            analysis_input = gr.Textbox(
                label="Analysis Request",
                placeholder="What analysis would you like to perform?",
                lines=3
            )
            analyze_btn = gr.Button("Analyze", variant="primary")
        
        analysis_output = gr.Textbox(
            label="Analysis Results",
            lines=10,
            max_lines=20
        )
        
    with gr.Tab("Visualization"):
        plot_output = gr.Plot(label="Data Visualization")
        
    def process_data(file):
        if file:
            response, _ = agent_instance.process_request(f"Process uploaded file: {{file.name}}")
            return response
        return "Please upload a file first."
    
    def analyze_data(query):
        if query:
            response, _ = agent_instance.process_request(f"Analyze: {{query}}")
            return response
        return "Please enter an analysis request."
    
    upload_btn.click(process_data, inputs=[file_upload], outputs=[analysis_output])
    analyze_btn.click(analyze_data, inputs=[analysis_input], outputs=[analysis_output])'''

    def _generate_automation_interface(self, blueprint: AgentBlueprint) -> str:
        """Generate interface for automation agents"""
        return f'''with gr.Blocks(title="{blueprint.name}", theme=gr.themes.Soft()) as interface:
    gr.Markdown("""
    # {blueprint.name}
    **{blueprint.description}**
    """)
    
    with gr.Tab("Configuration"):
        with gr.Row():
            with gr.Column():
                config_input = gr.JSON(
                    label="Configuration",
                    value={{}},
                    info="Enter your automation configuration"
                )
                save_config_btn = gr.Button("Save Configuration")
                
            with gr.Column():
                status_display = gr.Textbox(
                    label="Status",
                    value="Ready",
                    interactive=False
                )
                
    with gr.Tab("Control"):
        with gr.Row():
            start_btn = gr.Button("Start", variant="primary")
            stop_btn = gr.Button("Stop", variant="secondary")
            pause_btn = gr.Button("Pause")
            
        logs_output = gr.Textbox(
            label="Logs",
            lines=15,
            max_lines=25,
            autoscroll=True
        )
        
    def start_automation():
        response, state = agent_instance.process_request("START_AUTOMATION")
        return response, "Running"
    
    def stop_automation():
        response, state = agent_instance.process_request("STOP_AUTOMATION")
        return response, "Stopped"
        
    start_btn.click(start_automation, outputs=[logs_output, status_display])
    stop_btn.click(stop_automation, outputs=[logs_output, status_display])'''

    def _generate_creative_interface(self, blueprint: AgentBlueprint) -> str:
        """Generate interface for creative agents"""
        return f'''with gr.Blocks(title="{blueprint.name}", theme=gr.themes.Soft()) as interface:
    gr.Markdown("""
    # {blueprint.name}
    **{blueprint.description}**
    """)
    
    with gr.Tab("Creation"):
        with gr.Row():
            with gr.Column():
                prompt_input = gr.Textbox(
                    label="Creative Prompt",
                    placeholder="Describe what you want to create...",
                    lines=4
                )
                
                style_dropdown = gr.Dropdown(
                    choices=["Default", "Professional", "Creative", "Minimal", "Bold"],
                    label="Style",
                    value="Default"
                )
                
                create_btn = gr.Button("Create", variant="primary")
                
            with gr.Column():
                output_display = gr.Textbox(
                    label="Generated Content",
                    lines=15,
                    max_lines=25
                )
                
    with gr.Tab("Gallery"):
        gallery_display = gr.Gallery(
            label="Previous Creations",
            show_label=True,
            elem_id="gallery",
            columns=3,
            rows=2,
            height="auto"
        )
        
    def create_content(prompt, style):
        if prompt:
            response, _ = agent_instance.process_request(f"Create {{style}} content: {{prompt}}")
            return response
        return "Please enter a prompt first."
    
    create_btn.click(
        create_content,
        inputs=[prompt_input, style_dropdown],
        outputs=[output_display]
    )'''

    def generate_agent_code(self, blueprint: AgentBlueprint) -> str:
        """Generate complete agent code from blueprint"""
        
        # Generate class name from agent name
        class_name = "".join(word.capitalize() for word in blueprint.name.replace("-", " ").split())
        if not class_name.endswith("Agent"):
            class_name += "Agent"
            
        instance_name = f"{class_name.lower().replace('agent', '')}_agent"
        
        # Generate additional imports based on category
        additional_imports = self._generate_imports(blueprint)
        
        # Generate help features text
        help_features = "\n".join(f"- {feature}" for feature in blueprint.features)
        
        # Generate Gradio interface
        gradio_interface = self.generate_gradio_interface(blueprint)
        
        # Format the template
        code = self.base_template.format(
            agent_name=f'# {blueprint.name}\n"""{blueprint.description}"""',
            display_name=blueprint.name,
            description=blueprint.description,
            category=blueprint.category,
            difficulty=blueprint.difficulty,
            features=json.dumps(blueprint.features, indent=4),
            system_prompt=blueprint.system_prompt.replace('"""', '\\"\\"\\"'),
            class_name=class_name,
            instance_name=instance_name,
            additional_imports=additional_imports,
            gradio_interface=gradio_interface,
            help_features=help_features
        )
        
        return code
    
    def _generate_imports(self, blueprint: AgentBlueprint) -> str:
        """Generate additional imports based on agent category"""
        imports = []
        
        if blueprint.category.lower() in ["data science", "analysis"]:
            imports.extend([
                "import pandas as pd",
                "import numpy as np", 
                "import matplotlib.pyplot as plt",
                "import plotly.graph_objects as go"
            ])
            
        if blueprint.category.lower() in ["automation"]:
            imports.extend([
                "import asyncio",
                "import threading",
                "from pathlib import Path"
            ])
            
        if blueprint.category.lower() in ["creative", "content"]:
            imports.extend([
                "import re",
                "from PIL import Image"
            ])
            
        return "\n".join(imports)


class AgentBuilder:
    """Main Agent Builder class that orchestrates agent creation"""
    
    def __init__(self):
        self.prompt_manager = SystemPromptManager()
        self.code_generator = AgentCodeGenerator()
        self.agents_dir = Path(__file__).parent.parent / "agents"
        self.agents_dir.mkdir(exist_ok=True)
        
        # Initialize secure storage for HF tokens (same as GMPAgent)
        try:
            self.secure_storage = get_secure_storage() if get_secure_storage else None
        except Exception as e:
            print(f"Warning: Secure storage initialization failed: {e}")
            self.secure_storage = None
        
        # HF model configuration (same as GMPAgent)
        self.hf_model = None
        self.hf_tokenizer = None
        self.current_model_name = None
        self.available_models = [
            "Qwen/Qwen2.5-Coder-32B-Instruct",
            "mistralai/Mixtral-8x7B-Instruct-v0.1", 
            "HuggingfaceH4/zephyr-7b-beta"
        ]
        
    def set_mcp_connections(self, connections: Dict[str, Any]) -> None:
        """Set MCP connections for system prompt fetching"""
        self.prompt_manager.mcp_connections = connections
        
    # HF Token and Model management (same as GMPAgent)
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
            print("Transformers library not available")
            return False
        
        if model_name not in self.available_models:
            print(f"Model {model_name} not in available models")
            return False
        
        try:
            # Get HF token
            hf_token = self.get_hf_token()
            if not hf_token:
                print("No Hugging Face token found")
                return False
            
            print(f"Loading model {model_name}...")
            
            # Load tokenizer and model
            self.hf_tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                token=hf_token,
                trust_remote_code=True
            )
            
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
    
    def get_current_model(self) -> Optional[str]:
        """Get the currently loaded model name"""
        return self.current_model_name
    
    async def generate_hf_response(self, prompt: str, max_length: int = 512) -> Optional[str]:
        """Generate a response using the loaded HF model"""
        if not self.hf_model or not self.hf_tokenizer:
            return None
        
        try:
            # Prepare the prompt for the model (same logic as GMPAgent)
            if "Qwen" in self.current_model_name:
                messages = [
                    {"role": "system", "content": "You are a helpful AI assistant specialized in building Gradio agents and generating code."},
                    {"role": "user", "content": prompt}
                ]
                formatted_prompt = self.hf_tokenizer.apply_chat_template(messages, tokenize=False)
            elif "zephyr" in self.current_model_name:
                messages = [
                    {"role": "system", "content": "You are a helpful AI assistant specialized in building Gradio agents and generating code."},
                    {"role": "user", "content": prompt}
                ]
                formatted_prompt = self.hf_tokenizer.apply_chat_template(messages, tokenize=False)
            else:
                formatted_prompt = f"<s>[INST] You are a helpful AI assistant specialized in building Gradio agents and generating code.\n\n{prompt} [/INST]"
            
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
            "model_loaded": self.hf_model is not None,
            "current_model": self.current_model_name,
            "available_models": self.available_models,
            "has_transformers": HAS_TRANSFORMERS,
            "has_secure_storage": self.secure_storage is not None
        }
    
    async def get_available_system_prompts(self) -> Dict[str, str]:
        """Get available system prompts for agent building"""
        return await self.prompt_manager.fetch_system_prompts()
    
    async def create_agent_blueprint(self, 
                                   agent_name: str,
                                   description: str, 
                                   category: str,
                                   difficulty: str,
                                   features: List[str],
                                   system_prompt_name: str,
                                   custom_requirements: str = "") -> AgentBlueprint:
        """Create an agent blueprint from specifications"""
        
        # Get the system prompt content
        system_prompt_content = await self.prompt_manager.get_prompt_content(system_prompt_name)
        
        # If we have a loaded model, enhance the system prompt
        if custom_requirements and self.hf_model:
            enhancement_prompt = f"""
Based on the following system prompt and requirements, create an enhanced system prompt specifically for a Gradio agent:

Original System Prompt:
{system_prompt_content}

Agent Requirements:
- Name: {agent_name}
- Description: {description}
- Category: {category}
- Features: {', '.join(features)}
- Custom Requirements: {custom_requirements}

Create a tailored system prompt that incorporates the original prompt's style and approach but focuses on the specific agent requirements. The prompt should guide the agent to be helpful in its specialized domain.
"""
            
            enhanced_prompt = await self.generate_hf_response(enhancement_prompt, max_length=800)
            if enhanced_prompt:
                system_prompt_content = enhanced_prompt
        
        # Clean the agent name for file naming
        clean_name = re.sub(r'[^a-zA-Z0-9\-_]', '_', agent_name.lower())
        
        blueprint = AgentBlueprint(
            name=clean_name,
            description=description,
            category=category,
            difficulty=difficulty,
            features=features,
            system_prompt=system_prompt_content,
            ui_components={},
            dependencies=["gradio", "datetime", "typing", "json"],
            code_template=""
        )
        
        return blueprint
    
    async def build_agent(self, blueprint: AgentBlueprint) -> Tuple[bool, str, Path]:
        """Build an agent from a blueprint"""
        try:
            # Generate the agent code
            agent_code = self.code_generator.generate_agent_code(blueprint)
            
            # Create the agent file
            agent_filename = f"{blueprint.name}.py"
            agent_path = self.agents_dir / agent_filename
            
            # Write the code to file
            with open(agent_path, 'w', encoding='utf-8') as f:
                f.write(agent_code)
            
            # Make the file executable
            agent_path.chmod(0o755)
            
            success_msg = f"""✅ Agent '{blueprint.name}' created successfully!

**Location:** {agent_path}
**Category:** {blueprint.category}
**Difficulty:** {blueprint.difficulty}

**Features:**
{chr(10).join(f"• {feature}" for feature in blueprint.features)}

The agent is now available in the agents directory and can be accessed through the control panel."""

            return True, success_msg, agent_path
            
        except Exception as e:
            error_msg = f"❌ Error building agent: {str(e)}"
            return False, error_msg, None
    
    async def process_agent_request(self, user_input: str) -> Tuple[str, Dict[str, Any]]:
        """Process user requests for agent building"""
        
        # Parse the user input to extract agent requirements
        requirements = self._parse_agent_requirements(user_input)
        
        metadata = {
            "action": "agent_builder_response",
            "requirements": requirements
        }
        
        if not requirements["agent_name"]:
            response = """I'd be happy to help you build a new Gradio agent! 

To get started, please provide:

🤖 **Agent Name**: What should your agent be called?
📝 **Description**: What will your agent do?
🏷️ **Category**: Choose from:
   - Data Science
   - Automation  
   - Creative/Content
   - Tools/Utilities
   - Communication
   - Custom

💡 **Features**: What specific capabilities do you want?

**Example:**
"Create a code review agent that analyzes Python code, suggests improvements, and checks for best practices. Category: Tools/Utilities"

What kind of agent would you like to create?"""
            
            metadata["action"] = "request_agent_details"
            
        else:
            # We have enough info to create a blueprint
            try:
                available_prompts = await self.get_available_system_prompts()
                
                response = f"""Perfect! I can help you create the **{requirements['agent_name']}** agent.

**Detected Requirements:**
• **Name**: {requirements['agent_name']}
• **Description**: {requirements['description']}
• **Category**: {requirements['category']}
• **Features**: {', '.join(requirements['features'])}

**Available System Prompts** (choose one for the agent's personality):
{chr(10).join(f"• **{name}**: {desc}" for name, desc in list(available_prompts.items())[:5])}

**Next Steps:**
1. Choose a system prompt style (or say "default")
2. Any additional requirements?
3. I'll build your agent and add it to the agents directory!

Which system prompt style would you like to use?"""

                metadata["action"] = "ready_to_build"
                metadata["requirements"] = requirements
                metadata["available_prompts"] = available_prompts
                
            except Exception as e:
                response = f"❌ Error preparing agent build: {str(e)}"
                metadata["action"] = "error"
        
        return response, metadata
    
    def _parse_agent_requirements(self, user_input: str) -> Dict[str, Any]:
        """Parse user input to extract agent building requirements"""
        
        requirements = {
            "agent_name": "",
            "description": "",
            "category": "Tools/Utilities",
            "difficulty": "Intermediate", 
            "features": [],
            "system_prompt_preference": "default"
        }
        
        # Extract agent name
        name_patterns = [
            r"create (?:a |an )?(.+?) agent",
            r"build (?:a |an )?(.+?) agent", 
            r"make (?:a |an )?(.+?) agent",
            r"agent (?:called |named )?(.+?)(?:\.|,|$)",
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, user_input.lower())
            if match:
                requirements["agent_name"] = match.group(1).strip()
                break
        
        # Extract category
        category_keywords = {
            "data science": ["data", "analysis", "analytics", "statistics", "csv", "excel", "pandas"],
            "automation": ["automate", "schedule", "workflow", "batch", "process", "pipeline"],
            "creative": ["creative", "content", "writing", "generate", "art", "design"],
            "tools": ["tool", "utility", "helper", "converter", "calculator"],
            "communication": ["chat", "translate", "language", "communication", "social"]
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in user_input.lower() for keyword in keywords):
                requirements["category"] = category.title()
                break
        
        # Extract features from common patterns
        feature_patterns = [
            r"that (?:can |will )?(.+?)(?:\.|,|and|$)",
            r"to (.+?)(?:\.|,|and|$)",
            r"for (.+?)(?:\.|,|and|$)"
        ]
        
        for pattern in feature_patterns:
            matches = re.findall(pattern, user_input.lower())
            for match in matches:
                feature = match.strip()
                if len(feature) > 3 and len(feature) < 100:  # Reasonable feature length
                    requirements["features"].append(feature)
        
        # If no features found, try to extract from description
        if not requirements["features"]:
            # Split on common separators and take meaningful parts
            parts = re.split(r'[,.]', user_input)
            for part in parts[1:]:  # Skip first part (likely has agent name)
                cleaned = part.strip()
                if 10 < len(cleaned) < 100:
                    requirements["features"].append(cleaned)
        
        # Set description as the full input if no specific description found
        if not requirements["description"]:
            requirements["description"] = user_input
        
        return requirements

    async def build_from_requirements(self, 
                                    requirements: Dict[str, Any], 
                                    system_prompt_name: str = "claude-3.5-sonnet_20241122",
                                    additional_requirements: str = "") -> Tuple[bool, str, Optional[Path]]:
        """Build an agent from parsed requirements"""
        
        try:
            # Create blueprint
            blueprint = await self.create_agent_blueprint(
                agent_name=requirements["agent_name"],
                description=requirements["description"],
                category=requirements["category"], 
                difficulty=requirements["difficulty"],
                features=requirements["features"],
                system_prompt_name=system_prompt_name,
                custom_requirements=additional_requirements
            )
            
            # Build the agent
            success, message, path = await self.build_agent(blueprint)
            
            return success, message, path
            
        except Exception as e:
            return False, f"❌ Error building agent: {str(e)}", None
