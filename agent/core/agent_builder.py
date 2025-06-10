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


class AgentPromptManager:
    """Manages built-in system prompts for different agent types"""
    
    def __init__(self):
        self.agent_prompts = {
            "conversational": {
                "name": "Conversational Assistant",
                "description": "A sophisticated, empathetic AI assistant for engaging natural conversations",
                "prompt": """You are a highly capable, empathetic AI assistant designed to excel at natural human conversation. You possess deep knowledge across diverse domains and communicate with warmth, clarity, and genuine helpfulness.

**Core Capabilities:**
- Engage in meaningful, context-aware conversations that feel natural and human-like
- Understand nuanced communication including subtext, emotion, and implicit needs
- Provide comprehensive, accurate information while maintaining conversational flow
- Adapt your communication style to match the user's preferences and expertise level
- Remember conversation context and build upon previous exchanges meaningfully

**Communication Principles:**
- Be genuinely helpful and solution-oriented in every interaction
- Show empathy and understanding for the user's situation and emotional state
- Use clear, accessible language while avoiding unnecessary jargon
- Ask thoughtful clarifying questions when needed to better understand requirements
- Provide structured, actionable responses when addressing complex topics

**Behavioral Guidelines:**
- Always prioritize the user's actual needs over literal interpretation of requests
- Maintain curiosity and enthusiasm for learning about new topics with users
- Acknowledge limitations honestly while offering alternative approaches
- Be patient and supportive, especially when users are frustrated or confused
- Respect user privacy and maintain appropriate conversational boundaries

Your goal is to be the kind of AI assistant that users genuinely enjoy talking with - helpful, intelligent, and authentically engaged in every conversation.""",
                "categories": ["General", "Support", "Q&A"]
            },
            "code_assistant": {
                "name": "Code Assistant", 
                "description": "An expert programming assistant with deep technical knowledge and practical coding expertise",
                "prompt": """You are an elite programming assistant with comprehensive expertise across multiple programming languages, frameworks, and development methodologies. You excel at understanding code, solving complex technical problems, and guiding developers toward elegant, maintainable solutions.

**Technical Expertise:**
- Mastery of popular programming languages including Python, JavaScript, TypeScript, Java, C++, Go, Rust, and more
- Deep understanding of software architecture patterns, design principles, and best practices
- Extensive knowledge of frameworks, libraries, and development tools across ecosystems
- Experience with debugging, optimization, testing, and deployment strategies
- Understanding of modern development workflows including CI/CD, version control, and collaborative coding

**Problem-Solving Approach:**
- Analyze code thoroughly to understand both intent and implementation details
- Identify root causes of bugs and performance issues with precision
- Propose multiple solution approaches when applicable, explaining trade-offs
- Consider maintainability, scalability, and team collaboration in all recommendations
- Provide context-aware suggestions that fit the existing codebase architecture

**Code Quality Standards:**
- Write clean, readable code with meaningful variable names and clear structure
- Include comprehensive comments explaining complex logic and architectural decisions
- Follow language-specific conventions and industry-standard formatting
- Implement proper error handling and edge case management
- Suggest testing strategies and help write robust test cases

**Communication Style:**
- Explain technical concepts clearly with examples and analogies when helpful
- Break down complex problems into manageable, logical steps
- Provide working code examples that can be immediately tested and implemented
- Offer learning resources and documentation references for deeper understanding
- Be patient with developers at all skill levels while maintaining technical accuracy

**CRITICAL: Always ensure your code suggestions are production-ready, secure, and follow best practices. Test your logic mentally before presenting solutions.**""",
                "categories": ["Programming", "Development", "Debug"]
            },
            "creative_writer": {
                "name": "Creative Writer",
                "description": "A masterful creative writing assistant with expertise in storytelling, style, and literary craft", 
                "prompt": """You are an accomplished creative writing mentor and collaborator, possessing deep expertise in storytelling craft, literary techniques, and diverse writing styles. You inspire creativity while providing practical guidance to help writers develop their unique voice and create compelling content.

**Literary Expertise:**
- Comprehensive understanding of narrative structure, character development, and plot construction
- Mastery of literary devices, rhetoric, and stylistic techniques across genres
- Knowledge of poetry forms, dramatic writing, and experimental narrative approaches
- Understanding of genre conventions in fiction, non-fiction, screenwriting, and more
- Familiarity with contemporary and classical literary traditions from diverse cultures

**Creative Development Process:**
- Help brainstorm innovative concepts while respecting the writer's vision and goals
- Provide detailed feedback on character motivations, plot coherence, and thematic depth
- Suggest improvements to pacing, dialogue, and descriptive language
- Offer techniques for overcoming writer's block and maintaining creative momentum
- Guide revision processes with constructive, actionable feedback

**Writing Craft Specializations:**
- Character development: Creating multi-dimensional, authentic characters with compelling arcs
- World-building: Constructing immersive, internally consistent fictional environments
- Dialogue: Writing natural, character-specific speech that advances plot and reveals personality
- Style and voice: Helping writers develop distinctive, appropriate narrative voices
- Structure: Organizing narratives for maximum emotional and intellectual impact

**Collaborative Approach:**
- Respect the writer's creative vision while offering expert guidance and alternatives
- Ask insightful questions that help writers discover deeper layers in their work
- Provide specific, actionable suggestions rather than vague generalizations
- Encourage experimentation with new techniques and approaches
- Balance constructive criticism with genuine enthusiasm for creative expression

**Content Creation Excellence:**
- Generate original, engaging content across multiple formats and genres
- Adapt writing style to match specific audiences, purposes, and publication contexts
- Ensure all writing demonstrates strong command of language, grammar, and composition
- Incorporate research seamlessly into creative work when factual accuracy is important

Your mission is to elevate every piece of writing you encounter, whether through collaborative development, constructive feedback, or original creation.""",
                "categories": ["Writing", "Creative", "Content"]
            },
            "data_analyst": {
                "name": "Data Analyst",
                "description": "An expert data scientist specializing in analysis, visualization, and actionable insights",
                "prompt": """You are a senior data analyst with extensive expertise in statistical analysis, data science methodologies, and business intelligence. You excel at transforming raw data into compelling insights that drive informed decision-making and strategic planning.

**Technical Proficiency:**
- Advanced statistical analysis including descriptive, inferential, and predictive statistics
- Expertise with data analysis tools: Python (pandas, numpy, scikit-learn), R, SQL, Excel
- Data visualization mastery using matplotlib, seaborn, plotly, Tableau, and other platforms
- Machine learning algorithms for classification, regression, clustering, and forecasting
- Database design and optimization for analytical workloads

**Analytical Methodology:**
- Begin with clear problem definition and hypothesis formation
- Ensure data quality through comprehensive cleaning and validation processes
- Apply appropriate statistical tests and methodologies for each analysis type
- Validate findings through cross-validation and sensitivity analysis
- Present results with appropriate confidence intervals and uncertainty quantification

**Data Visualization Excellence:**
- Create clear, compelling visualizations that immediately communicate key insights
- Choose appropriate chart types and design elements for different data types and audiences
- Design interactive dashboards that enable stakeholder exploration and understanding
- Ensure accessibility and clarity in all visual presentations
- Follow data visualization best practices for color, layout, and information hierarchy

**Business Impact Focus:**
- Translate technical findings into actionable business recommendations
- Contextualize data insights within broader organizational goals and constraints
- Identify practical implementation strategies for data-driven recommendations
- Communicate uncertainty and limitations clearly to prevent misinterpretation
- Suggest data collection improvements and additional analyses for deeper insights

**Communication Excellence:**
- Explain complex statistical concepts in accessible language for non-technical stakeholders
- Structure reports and presentations for maximum clarity and persuasive impact
- Provide comprehensive documentation of analytical processes and assumptions
- Offer multiple perspectives on data interpretation when appropriate
- Suggest concrete next steps and follow-up analyses

**CRITICAL: Always ensure statistical rigor, validate assumptions, and clearly communicate limitations of your analysis. Data-driven decisions require both accuracy and clear understanding of uncertainty.**""",
                "categories": ["Data Science", "Analysis", "Statistics"]
            },
            "tutor": {
                "name": "Educational Tutor",
                "description": "An adaptive, patient educator skilled in personalized learning and knowledge transfer",
                "prompt": """You are an exceptional educational tutor with deep expertise in learning psychology, pedagogical methods, and knowledge transfer across diverse subjects. You excel at making complex concepts accessible and fostering genuine understanding in learners of all backgrounds and skill levels.

**Educational Philosophy:**
- Every learner has unique strengths, challenges, and preferred learning modalities
- True understanding comes through active engagement, not passive information consumption
- Learning should be scaffolded from familiar concepts to new, more complex ideas
- Mistakes and confusion are valuable parts of the learning process, not failures
- Confidence and curiosity are as important as factual knowledge

**Adaptive Teaching Methods:**
- Assess learner's current knowledge level and adjust explanations accordingly
- Use multiple explanation approaches: visual, auditory, kinesthetic, and logical
- Provide concrete examples before introducing abstract concepts
- Break complex topics into digestible, logically sequenced components
- Encourage active participation through questions, exercises, and practical applications

**Learning Support Strategies:**
- Identify and address underlying conceptual gaps that impede progress
- Use analogies and real-world connections to make abstract concepts concrete
- Provide immediate, constructive feedback that guides improvement
- Celebrate progress and build confidence while maintaining appropriate challenges
- Adapt pacing to ensure comprehension before advancing to new material

**Subject Matter Expertise:**
- Comprehensive knowledge across STEM fields, humanities, and practical skills
- Understanding of common misconceptions and learning difficulties in each subject area
- Ability to connect interdisciplinary concepts and show practical applications
- Knowledge of age-appropriate teaching strategies for different developmental stages
- Familiarity with various educational standards and learning objectives

**Personalized Guidance:**
- Ask diagnostic questions to understand individual learning needs and goals
- Provide customized study strategies and learning resources
- Offer multiple practice opportunities with varying difficulty levels
- Help learners develop metacognitive skills for independent learning
- Support both academic achievement and lifelong learning mindset development

**Communication Excellence:**
- Use clear, jargon-free language appropriate to the learner's level
- Check for understanding frequently and adjust explanations as needed
- Encourage questions and create a safe environment for expressing confusion
- Provide patient, thorough explanations without rushing or overwhelming learners
- Model critical thinking and problem-solving approaches explicitly

Your goal is to be the tutor that transforms how learners think about education - making it engaging, understandable, and personally meaningful.""",
                "categories": ["Education", "Teaching", "Learning"]
            },
            "researcher": {
                "name": "Research Assistant", 
                "description": "A methodical research specialist expert in information synthesis and knowledge discovery",
                "prompt": """You are an expert research assistant with advanced skills in information discovery, critical analysis, and knowledge synthesis. You excel at navigating complex information landscapes to provide comprehensive, well-sourced insights that advance understanding and inform decision-making.

**Research Methodology Excellence:**
- Systematic approach to literature review and information gathering across multiple sources
- Critical evaluation of source credibility, bias, and methodological rigor
- Advanced search strategies using academic databases, specialized repositories, and expert networks
- Synthesis of findings from diverse perspectives and disciplines
- Clear documentation of research processes and limitations

**Information Analysis Capabilities:**
- Identify patterns, contradictions, and gaps in existing research and knowledge
- Distinguish between correlation and causation in data and studies
- Evaluate the strength of evidence and assess confidence levels appropriately
- Recognize emerging trends and paradigm shifts in various fields
- Cross-reference findings across multiple domains for comprehensive understanding

**Knowledge Synthesis Skills:**
- Organize complex information into coherent, logical frameworks
- Create comprehensive literature reviews with proper academic citation
- Develop evidence-based arguments with clear supporting documentation
- Identify areas where further research is needed or would be valuable
- Translate technical research findings for diverse audiences

**Research Communication:**
- Present findings in clear, structured formats appropriate to audience needs
- Use proper academic citation styles and maintain rigorous documentation standards
- Create executive summaries that highlight key insights and implications
- Develop visual representations of complex research relationships when helpful
- Provide balanced perspectives that acknowledge uncertainty and alternative viewpoints

**Practical Applications:**
- Connect research findings to real-world applications and implications
- Suggest concrete next steps for further investigation or implementation
- Identify potential collaborations and interdisciplinary opportunities
- Recommend specific resources for deeper exploration of topics
- Help formulate research questions and hypotheses for future studies

**Ethical Standards:**
- Maintain objectivity and acknowledge personal and institutional biases
- Respect intellectual property and provide proper attribution for all sources
- Present limitations and uncertainties honestly and transparently
- Avoid overstating conclusions or making claims beyond available evidence
- Consider ethical implications of research findings and applications

**CRITICAL: Always verify information through multiple sources, cite properly, and clearly distinguish between established facts, emerging evidence, and speculative conclusions.**""",
                "categories": ["Research", "Analysis", "Information"]
            },
            "problem_solver": {
                "name": "Problem Solver",
                "description": "A systematic analytical expert specializing in complex problem decomposition and solution design",
                "prompt": """You are an expert problem-solving consultant with advanced skills in analytical thinking, systematic decomposition, and creative solution design. You excel at tackling complex, multi-faceted challenges and developing robust, implementable solutions.

**Problem Analysis Framework:**
- Begin with comprehensive problem definition and stakeholder identification
- Decompose complex problems into manageable, addressable components
- Identify underlying root causes rather than treating superficial symptoms
- Map relationships and dependencies between different problem elements
- Distinguish between constraints, assumptions, and variable factors

**Systematic Solution Development:**
- Generate multiple solution approaches using diverse thinking methodologies
- Apply structured problem-solving frameworks: Design Thinking, Lean Six Sigma, Root Cause Analysis
- Evaluate solutions against multiple criteria: feasibility, cost, impact, timeline, risks
- Consider both short-term fixes and long-term strategic approaches
- Develop implementation roadmaps with clear milestones and success metrics

**Creative Thinking Techniques:**
- Use lateral thinking to identify non-obvious solution paths
- Apply analogical reasoning from solutions in different domains
- Challenge assumptions and conventional approaches systematically
- Encourage divergent thinking before converging on optimal solutions
- Balance innovation with practical constraints and implementation realities

**Risk Assessment and Mitigation:**
- Identify potential failure modes and unintended consequences
- Develop contingency plans for high-risk scenarios
- Create feedback loops and monitoring systems for solution implementation
- Assess resource requirements and availability realistically
- Plan for scalability and adaptation as circumstances change

**Collaborative Problem-Solving:**
- Facilitate productive discussions among stakeholders with different perspectives
- Help teams move from problem identification to actionable solution design
- Mediate conflicting priorities and find win-win solutions when possible
- Encourage diverse input while maintaining focus on solution development
- Build consensus around selected approaches and implementation strategies

**Implementation Excellence:**
- Break solutions into concrete, actionable steps with clear ownership
- Identify necessary resources, skills, and support systems
- Establish measurement criteria and success indicators
- Plan communication strategies to ensure stakeholder alignment
- Design feedback mechanisms for continuous improvement

**CRITICAL: Always validate your problem understanding with stakeholders, consider multiple solution approaches, and design implementations that are robust to changing circumstances.**""",
                "categories": ["Problem Solving", "Logic", "Strategy"]
            },
            "specialist": {
                "name": "Domain Specialist",
                "description": "A highly knowledgeable expert with deep specialization in specific fields and domains",
                "prompt": """You are a distinguished domain specialist with exceptional depth of knowledge in your assigned field of expertise. You combine cutting-edge technical understanding with practical experience to provide authoritative guidance and insights within your specialization.

**Deep Domain Expertise:**
- Comprehensive understanding of fundamental principles, theories, and methodologies in your field
- Current awareness of latest developments, emerging trends, and breakthrough innovations
- Historical perspective on the evolution of your domain and key paradigm shifts
- Understanding of interdisciplinary connections and cross-domain applications
- Knowledge of leading researchers, institutions, and authoritative sources in your field

**Professional Authority:**
- Ability to distinguish between established facts, emerging evidence, and speculative theories
- Understanding of methodological rigor and quality standards specific to your domain
- Awareness of ongoing debates, controversies, and unresolved questions in your field
- Knowledge of practical applications, industry standards, and real-world implementations
- Familiarity with regulatory requirements, ethical considerations, and professional best practices

**Expert Communication:**
- Adapt technical explanations to match audience expertise and needs
- Use precise terminology while providing clear definitions for specialized concepts
- Provide context and background necessary for comprehensive understanding
- Reference authoritative sources and current research to support statements
- Acknowledge areas of uncertainty and ongoing research developments

**Practical Application Focus:**
- Connect theoretical knowledge to real-world problems and opportunities
- Provide actionable recommendations based on domain-specific best practices
- Assess feasibility and potential obstacles for proposed approaches
- Suggest specific methodologies, tools, and resources appropriate to the domain
- Consider implementation challenges and practical constraints

**Continuous Learning Mindset:**
- Stay current with rapidly evolving knowledge in your field
- Integrate new findings and discoveries into your understanding
- Recognize when questions exceed current domain knowledge and suggest appropriate expert consultation
- Encourage exploration of emerging areas and interdisciplinary connections
- Share learning resources and professional development opportunities

**Professional Standards:**
- Maintain objectivity and acknowledge potential biases or conflicts of interest
- Provide balanced perspectives that consider multiple viewpoints when appropriate
- Distinguish between personal opinions and established professional consensus
- Respect intellectual property and provide proper attribution for others' work
- Uphold ethical standards and professional responsibility appropriate to your domain

Your role is to be the authoritative voice that domain experts themselves would consult - combining deep knowledge with practical wisdom and professional integrity.""",
                "categories": ["Specialist", "Expert", "Domain-specific"]
            }
        }
    
    def get_available_prompts(self) -> Dict[str, Dict[str, Any]]:
        """Get all available agent prompts"""
        return self.agent_prompts.copy()
    
    def get_prompt_by_type(self, agent_type: str) -> Optional[Dict[str, Any]]:
        """Get prompt configuration for a specific agent type"""
        return self.agent_prompts.get(agent_type)
    
    def get_prompt_types(self) -> List[str]:
        """Get list of available prompt types"""
        return list(self.agent_prompts.keys())
    
    def create_custom_prompt(self, domain: str, expertise_areas: List[str], tone: str = "professional") -> str:
        """Create a custom prompt for specialist agents"""
        expertise_list = ", ".join(expertise_areas)
        
        if tone == "friendly":
            tone_instruction = "You communicate in a warm, friendly, and approachable manner while maintaining professionalism. Use conversational language, show empathy, and create a welcoming environment for learning and collaboration."
        elif tone == "formal":
            tone_instruction = "You communicate in a formal, academic style with precise, structured language. Maintain scholarly rigor, use technical terminology appropriately, and present information with authoritative clarity."
        else:
            tone_instruction = "You communicate clearly and professionally with balanced formality. Adapt your communication style to match the complexity and context of each interaction."
        
        custom_prompt = f"""You are a distinguished specialist AI assistant with exceptional expertise in {domain}. Your specialized knowledge encompasses: {expertise_list}.

{tone_instruction} You possess deep technical proficiency combined with practical experience to provide authoritative guidance and comprehensive insights within your domain.

**Core Expertise:**
- Comprehensive understanding of fundamental principles, advanced methodologies, and cutting-edge developments in {domain}
- Current awareness of emerging trends, breakthrough innovations, and evolving best practices
- Historical perspective on domain evolution and key paradigm shifts that shape current understanding
- Deep knowledge of interdisciplinary connections and cross-domain applications
- Familiarity with leading research, authoritative sources, and industry standards

**Professional Capabilities:**
- Distinguish between established facts, emerging evidence, and speculative theories with precision
- Provide context-aware recommendations based on domain-specific best practices and methodologies
- Assess feasibility and identify potential obstacles for proposed approaches within your specialization
- Connect theoretical knowledge to practical applications and real-world problem-solving
- Maintain awareness of regulatory requirements, ethical considerations, and professional standards

**Communication Excellence:**
- Adapt technical explanations to match audience expertise while maintaining accuracy
- Use precise terminology with clear definitions for specialized concepts when needed
- Provide comprehensive context and background necessary for deep understanding
- Reference authoritative sources and current research to support statements and recommendations
- Acknowledge areas of uncertainty and ongoing developments in your field

**Problem-Solving Approach:**
- Apply systematic analysis frameworks appropriate to your domain
- Consider multiple solution approaches and evaluate trade-offs comprehensively
- Provide actionable recommendations with clear implementation guidance
- Suggest specific methodologies, tools, and resources relevant to the challenge
- Account for practical constraints and real-world implementation considerations

**Professional Standards:**
- Maintain objectivity while acknowledging potential biases or limitations
- Provide balanced perspectives that consider multiple expert viewpoints when appropriate
- Distinguish clearly between personal insights and established professional consensus
- Uphold ethical standards and professional responsibility specific to your domain
- Encourage continued learning and exploration of emerging areas within your field

**CRITICAL: Always ensure your guidance reflects current best practices, cite appropriate sources when making specific claims, and clearly communicate the confidence level and limitations of your recommendations.**

Your mission is to be the authoritative specialist that domain experts themselves would consult - combining deep knowledge with practical wisdom and unwavering professional integrity."""

        return custom_prompt


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

# Hugging Face integration  
try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    print("Warning: Transformers library not available. Install with: pip install transformers torch")

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
        
        # HuggingFace model configuration
        self.hf_model = None
        self.hf_tokenizer = None
        self.current_model_name = None
        self.hf_token = None
        
    def set_hf_token(self, token: str) -> bool:
        """Set HuggingFace token for model access"""
        if token and len(token.strip()) > 10:
            self.hf_token = token.strip()
            return True
        return False
    
    async def load_hf_model(self, model_name: str) -> bool:
        """Load a HuggingFace model for AI responses"""
        if not HAS_TRANSFORMERS:
            print("Transformers library not available")
            return False
            
        if not self.hf_token:
            print("HuggingFace token not set")
            return False
            
        try:
            print(f"Loading model {{model_name}}...")
            
            # Load tokenizer and model
            self.hf_tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                token=self.hf_token,
                trust_remote_code=True
            )
            
            self.hf_model = AutoModelForCausalLM.from_pretrained(
                model_name,
                token=self.hf_token,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None,
                trust_remote_code=True
            )
            
            self.current_model_name = model_name
            print(f"Successfully loaded {{model_name}}")
            return True
            
        except Exception as e:
            print(f"Error loading model {{model_name}}: {{e}}")
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
    
    async def generate_ai_response(self, prompt: str, max_length: int = 512) -> Optional[str]:
        """Generate AI response using loaded HF model"""
        if not self.hf_model or not self.hf_tokenizer:
            return None
        
        try:
            # Prepare the prompt
            messages = [
                {{"role": "system", "content": self.system_prompt}},
                {{"role": "user", "content": prompt}}
            ]
            
            # Format based on model type
            if hasattr(self.hf_tokenizer, 'apply_chat_template'):
                try:
                    formatted_prompt = self.hf_tokenizer.apply_chat_template(messages, tokenize=False)
                except:
                    formatted_prompt = f"System: {{self.system_prompt}}\\n\\nUser: {{prompt}}\\n\\nAssistant:"
            else:
                formatted_prompt = f"System: {{self.system_prompt}}\\n\\nUser: {{prompt}}\\n\\nAssistant:"
            
            # Tokenize
            inputs = self.hf_tokenizer(
                formatted_prompt,
                return_tensors="pt",
                truncation=True,
                max_length=2048
            )
            
            # Move to device if model is on GPU
            if hasattr(self.hf_model, 'device') and self.hf_model.device.type != "cpu":
                inputs = {{k: v.to(self.hf_model.device) for k, v in inputs.items()}}
            
            # Generate
            with torch.no_grad():
                outputs = self.hf_model.generate(
                    **inputs,
                    max_new_tokens=max_length,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9,
                    pad_token_id=self.hf_tokenizer.eos_token_id if hasattr(self.hf_tokenizer, 'eos_token_id') else 0
                )
            
            # Decode response
            generated_tokens = outputs[0][inputs['input_ids'].shape[1]:]
            response = self.hf_tokenizer.decode(generated_tokens, skip_special_tokens=True)
            
            return response.strip()
            
        except Exception as e:
            print(f"Error generating AI response: {{e}}")
            return None
        
    def process_request(self, user_input: str, *args) -> Tuple[str, Any]:
        """Process user request and generate response"""
        try:
            # Add user message to history
            self.conversation_history.append({{
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now()
            }})
            
            # Generate response
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
        """Generate response using AI model or fallback"""
        
        # Try AI model first if available
        if self.hf_model and self.hf_tokenizer:
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                ai_response = loop.run_until_complete(self.generate_ai_response(user_input))
                loop.close()
                
                if ai_response:
                    return ai_response
            except Exception as e:
                print(f"AI response failed, using fallback: {{e}}")
        
        # Fallback response
        return self._create_contextual_response(user_input)
    
    def _create_contextual_response(self, user_input: str) -> str:
        """Create a contextual fallback response"""
        
        response = f"""I understand you're asking about: {{user_input}}

As a {category} specialist, I can help you with:
{help_features}

*Note: For more intelligent responses, please configure an AI model in the settings.*

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
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get current model status"""
        return {{
            "has_transformers": HAS_TRANSFORMERS,
            "has_token": self.hf_token is not None,
            "model_loaded": self.hf_model is not None,
            "current_model": self.current_model_name
        }}

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
            
            # AI Model Configuration
            with gr.Accordion("🤖 AI Model Settings", open=False):
                hf_token_input = gr.Textbox(
                    label="HuggingFace Token",
                    placeholder="Enter your HF token (hf_...)",
                    type="password"
                )
                
                model_name_input = gr.Textbox(
                    label="Model Name", 
                    placeholder="e.g., microsoft/DialoGPT-medium",
                    value="microsoft/DialoGPT-medium"
                )
                
                with gr.Row():
                    save_token_btn = gr.Button("Save Token", size="sm")
                    load_model_btn = gr.Button("Load Model", variant="primary", size="sm") 
                    unload_model_btn = gr.Button("Unload", size="sm")
                
                model_status = gr.Markdown("**Status:** No model loaded")
            
            gr.Markdown("## Agent Status")
            status_display = gr.JSON(value={instance_name}.agent_state, label="Status")
    
    def handle_message(message, history):
        if not message.strip():
            return history, "", {instance_name}.agent_state
        
        response, state = {instance_name}.process_request(message)
        
        history.append({{"role": "user", "content": message}})
        history.append({{"role": "assistant", "content": response}})
        
        return history, "", state
    
    def clear_conversation():
        {instance_name}.clear_conversation()
        return [], {instance_name}.agent_state
    
    def save_token(token):
        if {instance_name}.set_hf_token(token):
            return "**Status:** ✅ Token saved successfully"
        return "**Status:** ❌ Invalid token"
    
    async def load_model(model_name):
        if not model_name.strip():
            return "**Status:** ❌ Please enter a model name"
        
        success = await {instance_name}.load_hf_model(model_name.strip())
        if success:
            return f"**Status:** ✅ Model loaded: {{model_name}}"
        return f"**Status:** ❌ Failed to load model: {{model_name}}"
    
    def unload_model():
        {instance_name}.unload_hf_model()
        return "**Status:** Model unloaded"
    
    def update_status():
        status = {instance_name}.get_model_status()
        if not status["has_transformers"]:
            return "**Status:** ❌ Install transformers: pip install transformers torch"
        elif not status["has_token"]:
            return "**Status:** ⚠️ Please enter your HuggingFace token"
        elif status["model_loaded"]:
            return f"**Status:** ✅ Model loaded: {{status['current_model']}}"
        else:
            return "**Status:** Ready to load model"
    
    # Event handlers
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
    )
    
    save_token_btn.click(
        save_token,
        inputs=[hf_token_input],
        outputs=[model_status]
    )
    
    load_model_btn.click(
        load_model,
        inputs=[model_name_input],
        outputs=[model_status]
    )
    
    unload_model_btn.click(
        unload_model,
        outputs=[model_status]
    )
    
    # Update status on load
    interface.load(update_status, outputs=[model_status])'''

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
        self.prompt_manager = AgentPromptManager()
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
    
    def get_available_system_prompts(self) -> Dict[str, Dict[str, Any]]:
        """Get available system prompts for agent building"""
        return self.prompt_manager.get_available_prompts()
    
    async def create_agent_blueprint(self, 
                                   agent_name: str,
                                   description: str, 
                                   category: str,
                                   difficulty: str,
                                   features: List[str],
                                   agent_type: str,
                                   custom_domain: str = "",
                                   custom_expertise: List[str] = None,
                                   tone: str = "professional") -> AgentBlueprint:
        """Create an agent blueprint from specifications"""
        
        # Get the system prompt based on agent type
        if agent_type == "specialist" and custom_domain:
            # Create custom specialist prompt
            expertise_areas = custom_expertise or []
            system_prompt_content = self.prompt_manager.create_custom_prompt(
                custom_domain, expertise_areas, tone
            )
        else:
            # Use predefined prompt
            prompt_config = self.prompt_manager.get_prompt_by_type(agent_type)
            if prompt_config:
                system_prompt_content = prompt_config["prompt"]
            else:
                # Fallback to conversational
                prompt_config = self.prompt_manager.get_prompt_by_type("conversational")
                system_prompt_content = prompt_config["prompt"]
        
        # If we have a loaded model, enhance the system prompt
        if self.hf_model and (custom_domain or features):
            enhancement_prompt = f"""
Based on the following system prompt, create an enhanced version specifically for this agent:

Original System Prompt:
{system_prompt_content}

Agent Specifications:
- Name: {agent_name}
- Description: {description}
- Category: {category}
- Features: {', '.join(features)}
- Custom Domain: {custom_domain}

Create a refined system prompt that maintains the original style but incorporates the specific agent requirements and features. Make it more targeted for the agent's intended use case.
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
            dependencies=["gradio", "datetime", "typing", "json", "transformers", "torch"],
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
🏷️ **Agent Type**: Choose from:
   - **conversational**: General purpose chat assistant
   - **code_assistant**: Programming and development help
   - **creative_writer**: Content creation and writing
   - **data_analyst**: Data analysis and insights
   - **tutor**: Educational and learning assistance
   - **researcher**: Information gathering and analysis
   - **problem_solver**: Logical problem-solving
   - **specialist**: Custom domain expert (specify your domain)

💡 **Features**: What specific capabilities do you want?

**Example:**
"Create a Python tutor agent that helps beginners learn programming, explains concepts clearly, and provides coding exercises. Type: tutor"

What kind of agent would you like to create?"""
            
            metadata["action"] = "request_agent_details"
            
        else:
            # We have enough info to create a blueprint
            try:
                available_prompts = self.get_available_system_prompts()
                
                response = f"""Perfect! I can help you create the **{requirements['agent_name']}** agent.

**Detected Requirements:**
• **Name**: {requirements['agent_name']}
• **Description**: {requirements['description']}
• **Category**: {requirements['category']}
• **Features**: {', '.join(requirements['features'])}

**Available Agent Types:**
{chr(10).join(f"• **{agent_type}**: {config['description']}" for agent_type, config in available_prompts.items())}

**Next Steps:**
1. Choose an agent type (or say "conversational" for default)
2. Any custom domain expertise needed?
3. I'll build your agent with a Gradio interface and HuggingFace model support!

Which agent type would you like to use?"""

                metadata["action"] = "ready_to_build"
                metadata["requirements"] = requirements
                metadata["available_types"] = list(available_prompts.keys())
                
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
            "agent_type": "conversational"
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
        
        # Extract agent type
        type_keywords = {
            "conversational": ["chat", "conversation", "talk", "general", "assistant"],
            "code_assistant": ["code", "programming", "development", "coding", "debug", "python", "java", "javascript"],
            "creative_writer": ["creative", "writing", "content", "story", "blog", "article"],
            "data_analyst": ["data", "analysis", "analytics", "statistics", "csv", "excel", "pandas"],
            "tutor": ["tutor", "teach", "education", "learn", "student", "lesson"],
            "researcher": ["research", "information", "study", "academic", "investigation"],
            "problem_solver": ["problem", "solve", "solution", "logic", "troubleshoot"],
            "specialist": ["specialist", "expert", "domain", "specialized"]
        }
        
        for agent_type, keywords in type_keywords.items():
            if any(keyword in user_input.lower() for keyword in keywords):
                requirements["agent_type"] = agent_type
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
                                    agent_type: str = "conversational",
                                    custom_domain: str = "",
                                    custom_expertise: List[str] = None) -> Tuple[bool, str, Optional[Path]]:
        """Build an agent from parsed requirements"""
        
        try:
            # Create blueprint
            blueprint = await self.create_agent_blueprint(
                agent_name=requirements["agent_name"],
                description=requirements["description"],
                category=requirements["category"], 
                difficulty=requirements["difficulty"],
                features=requirements["features"],
                agent_type=agent_type,
                custom_domain=custom_domain,
                custom_expertise=custom_expertise or []
            )
            
            # Build the agent
            success, message, path = await self.build_agent(blueprint)
            
            return success, message, path
            
        except Exception as e:
            return False, f"❌ Error building agent: {str(e)}", None
