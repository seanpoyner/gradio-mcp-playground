"""LlamaIndex Coding Agent for Gradio MCP Playground

Provides an intelligent coding assistant that can help with MCP server development,
code analysis, and general programming tasks.
"""

from pathlib import Path
from typing import Any, Dict, List

# Optional imports
try:
    from llama_index.core import Document, Settings, VectorStoreIndex
    from llama_index.core.agent import ReActAgent
    from llama_index.core.memory import ChatMemoryBuffer
    from llama_index.core.tools import FunctionTool, QueryEngineTool
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    from llama_index.llms.huggingface_api import HuggingFaceInferenceAPI

    HAS_LLAMAINDEX = True
except ImportError:
    HAS_LLAMAINDEX = False

try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


if HAS_LLAMAINDEX:

    class CodingAgent:
        """LlamaIndex-powered coding agent for MCP development assistance"""

        def __init__(self):
            self.agent = None
            self.llm = None
            self.current_model = None
            self.hf_token = None
            self.memory = ChatMemoryBuffer.from_defaults(token_limit=3000)

            # Available models - CONFIRMED working with HuggingFace Inference API
            self.available_models = {
                # Specialized coding model (confirmed working)
                "Qwen/Qwen2.5-Coder-32B-Instruct": {
                    "name": "Qwen2.5 Coder 32B (CODING SPECIALIST)",
                    "description": "🎯 Specialized 32B coding model - excellent for programming tasks and code analysis",
                    "context_window": 32768,
                    "size": "32B parameters",
                    "strengths": [
                        "Code generation",
                        "Code analysis",
                        "Debugging",
                        "Multiple languages",
                        "Latest architecture",
                    ],
                },
                # Large, powerful model (confirmed working)
                "mistralai/Mixtral-8x7B-Instruct-v0.1": {
                    "name": "Mixtral 8x7B Instruct (LARGE)",
                    "description": "🚀 Massive 8x7B parameter model - excellent for complex coding tasks and reasoning",
                    "context_window": 32768,
                    "size": "8x7B parameters",
                    "strengths": [
                        "Complex reasoning",
                        "Long context",
                        "Code generation",
                        "Multi-step problems",
                    ],
                },
                # Reliable 7B model (confirmed working)
                "HuggingFaceH4/zephyr-7b-beta": {
                    "name": "Zephyr 7B Beta (FAST)",
                    "description": "⚡ Fine-tuned 7B model - fast responses, good for most coding tasks",
                    "context_window": 8192,
                    "size": "7B parameters",
                    "strengths": [
                        "Fast responses",
                        "General coding",
                        "Explanations",
                        "Quick iterations",
                    ],
                },
            }

            self._setup_tools()

        def _setup_tools(self):
            """Setup tools for the coding agent"""
            self.tools = [
                self._create_mcp_help_tool(),
                self._create_code_analyzer_tool(),
                self._create_gradio_helper_tool(),
                self._create_file_reader_tool(),
            ]

            # Add MCP server management tools
            self._add_mcp_management_tools()

        def _create_mcp_help_tool(self) -> FunctionTool:
            """Create tool for MCP-specific help and guidance"""

            def mcp_help(query: str) -> str:
                """Provide help and guidance about MCP (Model Context Protocol) development.

                Args:
                    query: Question about MCP development, servers, or tools
                """
                mcp_knowledge = {
                    "what_is_mcp": "MCP (Model Context Protocol) is a protocol that enables AI models to securely connect to external data sources and tools. It provides a standardized way to expose capabilities to AI applications.",
                    "mcp_server": "An MCP server exposes tools and resources that AI models can use. Servers implement specific capabilities like file operations, API access, or data processing.",
                    "mcp_tools": "MCP tools are functions that AI models can call to perform actions. Each tool has a schema defining its inputs and outputs.",
                    "gradio_integration": "Gradio MCP Playground helps you build Gradio apps that function as MCP servers, making it easy to create interactive UIs for your MCP tools.",
                    "best_practices": [
                        "Always validate inputs in your MCP tools",
                        "Provide clear descriptions for tools and parameters",
                        "Handle errors gracefully and return meaningful messages",
                        "Use appropriate data types in tool schemas",
                        "Test your MCP servers thoroughly before deployment",
                    ],
                }

                query_lower = query.lower()

                if "what is mcp" in query_lower or "what's mcp" in query_lower:
                    return mcp_knowledge["what_is_mcp"]
                elif "server" in query_lower:
                    return mcp_knowledge["mcp_server"]
                elif "tool" in query_lower:
                    return mcp_knowledge["mcp_tools"]
                elif "gradio" in query_lower:
                    return mcp_knowledge["gradio_integration"]
                elif "best practice" in query_lower or "practices" in query_lower:
                    return "MCP Best Practices:\n" + "\n".join(
                        [f"• {practice}" for practice in mcp_knowledge["best_practices"]]
                    )
                else:
                    return f"Here's general guidance about MCP development: {mcp_knowledge['what_is_mcp']} For specific help, ask about MCP servers, tools, or best practices."

            return FunctionTool.from_defaults(fn=mcp_help, name="mcp_help")

        def _create_code_analyzer_tool(self) -> FunctionTool:
            """Create tool for analyzing code"""

            def analyze_code(code: str, language: str = "python") -> str:
                """Analyze code for potential issues, improvements, and best practices.

                Args:
                    code: The code to analyze
                    language: Programming language (default: python)
                """
                try:
                    lines = code.split("\n")
                    analysis = {
                        "line_count": len(lines),
                        "suggestions": [],
                        "potential_issues": [],
                        "security_notes": [],
                    }

                    # Basic Python analysis
                    if language.lower() == "python":
                        for i, line in enumerate(lines, 1):
                            line_stripped = line.strip()

                            # Check for common issues
                            if "print(" in line_stripped and "debug" not in line_stripped.lower():
                                analysis["suggestions"].append(
                                    f"Line {i}: Consider using logging instead of print for production code"
                                )

                            if "except:" in line_stripped:
                                analysis["potential_issues"].append(
                                    f"Line {i}: Bare except clause - consider catching specific exceptions"
                                )

                            if "eval(" in line_stripped or "exec(" in line_stripped:
                                analysis["security_notes"].append(
                                    f"Line {i}: Use of eval/exec can be dangerous - validate inputs carefully"
                                )

                            if "TODO" in line_stripped or "FIXME" in line_stripped:
                                analysis["suggestions"].append(
                                    f"Line {i}: Contains TODO/FIXME comment"
                                )

                    result = f"Code Analysis ({language}):\n"
                    result += f"Lines of code: {analysis['line_count']}\n\n"

                    if analysis["potential_issues"]:
                        result += (
                            "Potential Issues:\n"
                            + "\n".join([f"• {issue}" for issue in analysis["potential_issues"]])
                            + "\n\n"
                        )

                    if analysis["security_notes"]:
                        result += (
                            "Security Notes:\n"
                            + "\n".join([f"• {note}" for note in analysis["security_notes"]])
                            + "\n\n"
                        )

                    if analysis["suggestions"]:
                        result += (
                            "Suggestions:\n"
                            + "\n".join(
                                [f"• {suggestion}" for suggestion in analysis["suggestions"]]
                            )
                            + "\n"
                        )

                    if not any(
                        [
                            analysis["potential_issues"],
                            analysis["security_notes"],
                            analysis["suggestions"],
                        ]
                    ):
                        result += "No obvious issues found. Code looks good!"

                    return result

                except Exception as e:
                    return f"Error analyzing code: {str(e)}"

            return FunctionTool.from_defaults(fn=analyze_code, name="analyze_code")

        def _create_gradio_helper_tool(self) -> FunctionTool:
            """Create tool for Gradio-specific help"""

            def gradio_help(component_type: str = "") -> str:
                """Get help with Gradio components and best practices.

                Args:
                    component_type: Specific Gradio component to get help with
                """
                gradio_help_data = {
                    "textbox": "gr.Textbox() - For text input/output. Use 'lines' parameter for multiline, 'type' for password fields.",
                    "button": "gr.Button() - For user actions. Use 'variant' parameter for styling (primary, secondary, stop).",
                    "dropdown": "gr.Dropdown() - For selection from options. Use 'choices' parameter for options list.",
                    "slider": "gr.Slider() - For numeric input. Set 'minimum', 'maximum', and 'step' parameters.",
                    "file": "gr.File() - For file uploads. Use 'file_types' to restrict allowed types.",
                    "dataframe": "gr.Dataframe() - For tabular data. Set 'headers' and use 'interactive' for editing.",
                    "plot": "gr.Plot() - For matplotlib/plotly charts. Return plot objects from functions.",
                    "interface": "gr.Interface() - Simple way to create UIs with inputs/outputs/function.",
                    "blocks": "gr.Blocks() - More flexible UI builder with layout control using rows/columns.",
                    "general": "Gradio tips: Use clear labels, provide examples, handle errors gracefully, test with different inputs.",
                }

                if component_type.lower() in gradio_help_data:
                    return gradio_help_data[component_type.lower()]
                elif component_type:
                    return f"No specific help found for '{component_type}'. Available components: {', '.join(gradio_help_data.keys())}"
                else:
                    return gradio_help_data["general"]

            return FunctionTool.from_defaults(fn=gradio_help, name="gradio_help")

        def _create_file_reader_tool(self) -> FunctionTool:
            """Create tool for reading project files"""

            def read_project_file(file_path: str) -> str:
                """Read a file from the current project directory.

                Args:
                    file_path: Path to the file relative to project root
                """
                try:
                    # Security: only allow reading from current directory and subdirectories
                    full_path = Path.cwd() / file_path

                    # Check if path is within current directory
                    if not str(full_path.resolve()).startswith(str(Path.cwd().resolve())):
                        return "Error: Can only read files within the current project directory"

                    if not full_path.exists():
                        return f"Error: File '{file_path}' not found"

                    if full_path.is_dir():
                        # List directory contents
                        contents = list(full_path.iterdir())
                        return f"Directory contents of '{file_path}':\n" + "\n".join(
                            [f"• {item.name}" for item in contents]
                        )

                    # Read file content
                    with open(full_path, encoding="utf-8") as f:
                        content = f.read()

                    # Limit content size for display
                    if len(content) > 5000:
                        content = (
                            content[:5000] + "\n... (file truncated, showing first 5000 characters)"
                        )

                    return f"Content of '{file_path}':\n\n{content}"

                except Exception as e:
                    return f"Error reading file '{file_path}': {str(e)}"

            return FunctionTool.from_defaults(fn=read_project_file, name="read_project_file")

        def _add_mcp_management_tools(self):
            """Add MCP server management tools to the agent"""
            try:
                from .mcp_management_tool import create_mcp_management_tools

                mcp_tools = create_mcp_management_tools()
                self.tools.extend(mcp_tools)

                print("DEBUG: Added MCP server management tools to coding agent")
            except ImportError as e:
                print(f"DEBUG: Could not add MCP management tools: {e}")
            except Exception as e:
                print(f"DEBUG: Error adding MCP management tools: {e}")

        def configure_model(self, hf_token: str, model_name: str) -> Dict[str, Any]:
            """Configure the LLM model for the agent"""
            try:
                if not HAS_REQUESTS:
                    return {
                        "success": False,
                        "error": "requests library required for HuggingFace API",
                    }

                # Clean and validate the token
                clean_token = hf_token.strip()
                print(
                    f"DEBUG: Attempting to configure model {model_name} with token length {len(clean_token)}"
                )
                print(f"DEBUG: Token starts with: {clean_token[:10]}...")

                # Validate HuggingFace token
                headers = {
                    "Authorization": f"Bearer {clean_token}",
                    "Content-Type": "application/json",
                    "User-Agent": "gradio-mcp-playground/0.1.0",
                }

                print(f"DEBUG: Request headers: {dict(headers)}")

                try:
                    # Test model access directly instead of whoami (some tokens have limited permissions)
                    model_url = f"https://huggingface.co/api/models/{model_name}"
                    model_response = requests.get(model_url, headers=headers, timeout=10)
                    print(f"DEBUG: Model access test status: {model_response.status_code}")

                    if model_response.status_code == 200:
                        print(f"DEBUG: Model {model_name} is accessible")

                        # Try whoami as secondary validation (but don't fail if it doesn't work)
                        try:
                            response = requests.get(
                                "https://huggingface.co/api/whoami", headers=headers, timeout=5
                            )
                            if response.status_code == 200:
                                user_info = response.json()
                                print(f"DEBUG: HF user info: {user_info}")
                            else:
                                print("DEBUG: Whoami failed but model access works - continuing")
                        except:
                            print(
                                "DEBUG: Whoami endpoint failed but model access works - continuing"
                            )

                    else:
                        print(f"DEBUG: Model access error: {model_response.text[:200]}")
                        return {
                            "success": False,
                            "error": f"Token cannot access model {model_name}. Status: {model_response.status_code}",
                        }

                except requests.exceptions.RequestException as e:
                    print(f"DEBUG: Network exception: {str(e)}")
                    return {
                        "success": False,
                        "error": f"Network error connecting to HuggingFace API: {str(e)}",
                    }

                # Validate model
                if model_name not in self.available_models:
                    return {
                        "success": False,
                        "error": f"Model '{model_name}' not supported. Available models: {list(self.available_models.keys())}",
                    }

                print(f"DEBUG: Creating HuggingFaceInferenceAPI with model {model_name}")

                # Configure LLM
                self.hf_token = clean_token
                self.current_model = model_name

                try:
                    print(f"DEBUG: Creating HuggingFaceInferenceAPI for {model_name}")
                    self.llm = HuggingFaceInferenceAPI(
                        model_name=model_name,
                        token=clean_token,
                        context_window=self.available_models[model_name]["context_window"],
                        timeout=60.0,
                    )
                    print("DEBUG: HuggingFaceInferenceAPI created successfully")

                    # Test the model with a simple prompt (but don't fail if test fails)
                    try:
                        print("DEBUG: Testing model with simple prompt...")
                        test_response = self.llm.complete("Hello, can you help with coding?")
                        print(f"DEBUG: Model test successful: {str(test_response)[:100]}...")
                    except Exception as test_e:
                        print(f"DEBUG: Model test failed, but continuing: {test_e}")
                        # Don't fail configuration - some models might work in chat mode but not complete mode
                        print("DEBUG: Continuing with model configuration despite test failure")

                except Exception as e:
                    print(f"DEBUG: HuggingFaceInferenceAPI creation failed: {str(e)}")
                    return {
                        "success": False,
                        "error": f"Failed to create HuggingFace API client: {str(e)}",
                    }

                # Set global settings
                try:
                    Settings.llm = self.llm
                    print("DEBUG: LLM settings configured")

                    Settings.embed_model = HuggingFaceEmbedding(
                        model_name="sentence-transformers/all-MiniLM-L6-v2"
                    )
                    print("DEBUG: Embedding model configured")
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Failed to configure LlamaIndex settings: {str(e)}",
                    }

                # Create agent
                try:
                    self.agent = ReActAgent.from_tools(
                        tools=self.tools,
                        llm=self.llm,
                        memory=self.memory,
                        verbose=True,
                        system_prompt="""You are an expert software engineer and coding assistant specializing in:

🎯 **Core Expertise:**
- MCP (Model Context Protocol) development and server creation
- Gradio application development and UI design
- Python programming and best practices
- Code analysis, debugging, and optimization
- Software architecture and design patterns
- MCP server management and deployment

🛠 **Your Capabilities:**
- Analyze code for bugs, security issues, and improvements
- Generate clean, efficient, and well-documented code
- Explain complex programming concepts clearly
- Provide step-by-step implementation guidance
- Review and suggest architectural improvements
- **Manage MCP servers**: create, start, stop, delete, and connect to MCP servers
- **Server operations**: list available servers, templates, and active connections
- **Client connections**: connect to and test MCP server endpoints


📋 **Guidelines:**
- Always use your available tools to provide accurate, specific information
- When showing code, explain the logic and reasoning behind it
- Focus on practical, working solutions
- Consider security, performance, and maintainability
- Ask clarifying questions when requirements are unclear
- **IMPORTANT**: When you see "APPROVAL_REQUIRED", explain to the user what command needs approval and ask for their permission

🚀 **Communication Style:**
- Be concise but thorough
- Use code examples liberally
- Structure responses with clear headings and bullet points
- Provide actionable next steps
- Focus on teaching and explaining, not just providing answers

Ready to help with any coding challenge or MCP development task!""",
                    )
                    print("DEBUG: ReActAgent created successfully")
                except Exception as e:
                    return {"success": False, "error": f"Failed to create ReAct agent: {str(e)}"}

                return {
                    "success": True,
                    "model": self.available_models[model_name]["name"],
                    "description": self.available_models[model_name]["description"],
                }

            except Exception as e:
                import traceback

                print(f"DEBUG: Unexpected error in configure_model: {str(e)}")
                print(f"DEBUG: Traceback: {traceback.format_exc()}")
                return {"success": False, "error": f"Unexpected error: {str(e)}"}

        def chat(self, message: str) -> str:
            """Send a message to the coding agent"""
            if not self.agent:
                return "Please configure a model first by providing your HuggingFace API token and selecting a model."

            try:
                response = self.agent.chat(message)
                response_str = str(response)

                # Truncate very long responses to prevent UI issues
                if len(response_str) > 8000:
                    response_str = response_str[:8000] + "\n\n... (response truncated for display)"

                return response_str
            except Exception as e:
                error_msg = str(e)
                if "404" in error_msg and "not found" in error_msg.lower():
                    return f"❌ Model endpoint not available. Try using 'Zephyr 7B Beta' which is confirmed to work.\n\nOriginal error: {error_msg}"
                elif "401" in error_msg or "unauthorized" in error_msg.lower():
                    return f"❌ Authentication failed. Please check your HuggingFace token has the correct permissions.\n\nOriginal error: {error_msg}"
                elif "503" in error_msg or "temporarily unavailable" in error_msg.lower():
                    return f"❌ Model is temporarily unavailable. Please try again in a few minutes.\n\nOriginal error: {error_msg}"
                else:
                    return f"❌ Error processing message: {error_msg}\n\n💡 Try switching to 'Zephyr 7B Beta' model which is confirmed to work."

        def get_available_models(self) -> Dict[str, Dict[str, Any]]:
            """Get list of available models"""
            return self.available_models

        def reset_conversation(self):
            """Reset the conversation memory"""
            self.memory.reset()
            if self.agent:
                self.agent.reset()

        def is_configured(self) -> bool:
            """Check if agent is properly configured"""
            return self.agent is not None and self.llm is not None

else:
    # Dummy class when LlamaIndex is not available
    class CodingAgent:
        def __init__(self):
            raise ImportError(
                "LlamaIndex is required for coding agent functionality. Install with: pip install -e '.[ai]'"
            )

        def get_available_models(self):
            return {}
