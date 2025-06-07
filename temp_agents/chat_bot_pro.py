"""
💬 Chat Bot Pro Agent

AGENT_INFO = {
    "name": "💬 Chat Bot Pro",
    "description": "Advanced conversational AI with memory, multiple personalities, and context awareness",
    "category": "AI Assistant",
    "difficulty": "Advanced",
    "features": [
        "Conversation memory and context tracking",
        "Multiple personality modes (Friendly, Professional, Witty, Sage)",
        "Sentiment analysis and topic extraction",
        "Conversation export and history management",
        "Contextual response generation",
        "Real-time chat interface with timestamps"
    ],
    "version": "1.0.0",
    "author": "Agent System"
}
"""

import gradio as gr
import random
import datetime
import json
import re
from typing import List, Dict, Tuple
import os

class AdvancedChatBot:
    def __init__(self):
        self.conversation_history: List[Dict] = []
        self.user_profile = {
            "name": None,
            "preferences": {},
            "conversation_topics": [],
            "sentiment_history": []
        }
        self.personality_mode = "friendly"
        self.context_memory = {}
        self.session_stats = {
            "messages_sent": 0,
            "session_start": datetime.datetime.now(),
            "topics_discussed": set()
        }
        
        self.personalities = {
            "friendly": {
                "description": "Warm, encouraging, and supportive",
                "response_style": "casual",
                "emoji_usage": "high"
            },
            "professional": {
                "description": "Formal, efficient, and business-focused",
                "response_style": "formal",
                "emoji_usage": "minimal"
            },
            "witty": {
                "description": "Clever, humorous, and entertaining",
                "response_style": "playful",
                "emoji_usage": "medium"
            },
            "sage": {
                "description": "Wise, thoughtful, and philosophical",
                "response_style": "contemplative",
                "emoji_usage": "minimal"
            }
        }
        
        self.conversation_starters = [
            "What's been on your mind lately?",
            "Tell me about something that made you smile today!",
            "What's a goal you're working towards?",
            "If you could learn any skill instantly, what would it be?",
            "What's your favorite way to unwind?"
        ]
        
        self.response_templates = {
            "greeting": [
                "Hello! I'm excited to chat with you today! 😊",
                "Hey there! What brings you here today?",
                "Hi! I'm here and ready to have a great conversation!"
            ],
            "farewell": [
                "It was wonderful chatting with you! Take care! 👋",
                "Thanks for the great conversation! Until next time!",
                "Goodbye! Looking forward to our next chat!"
            ],
            "encouragement": [
                "That sounds really interesting! Tell me more!",
                "I love your perspective on this!",
                "You're making some great points!"
            ]
        }
    
    def set_personality(self, personality: str) -> str:
        """Change bot personality mode"""
        if personality in self.personalities:
            self.personality_mode = personality
            profile = self.personalities[personality]
            self._add_system_message(f"Personality changed to: {personality}")
            return f"🎭 **Personality updated to {personality.title()}**\n\n{profile['description']}"
        return "❌ Invalid personality mode"
    
    def _add_system_message(self, message: str):
        """Add system message to conversation history"""
        self.conversation_history.append({
            "type": "system",
            "content": message,
            "timestamp": datetime.datetime.now().isoformat()
        })
    
    def _detect_sentiment(self, message: str) -> str:
        """Simple sentiment detection"""
        positive_words = ["happy", "great", "awesome", "good", "love", "excellent", "wonderful", "amazing"]
        negative_words = ["sad", "bad", "terrible", "awful", "hate", "horrible", "disappointed", "frustrated"]
        
        message_lower = message.lower()
        pos_count = sum(1 for word in positive_words if word in message_lower)
        neg_count = sum(1 for word in negative_words if word in message_lower)
        
        if pos_count > neg_count:
            return "positive"
        elif neg_count > pos_count:
            return "negative"
        else:
            return "neutral"
    
    def _extract_topics(self, message: str) -> List[str]:
        """Extract potential conversation topics"""
        # Simple keyword extraction
        topics = []
        topic_patterns = [
            r"\b(work|job|career)\b",
            r"\b(family|friends|relationships)\b", 
            r"\b(travel|vacation|trip)\b",
            r"\b(food|cooking|restaurant)\b",
            r"\b(movies|books|music)\b",
            r"\b(sports|exercise|fitness)\b",
            r"\b(technology|AI|computer)\b",
            r"\b(weather|nature|outdoors)\b"
        ]
        
        for pattern in topic_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                topic = re.search(pattern, message, re.IGNORECASE).group(1)
                topics.append(topic)
                self.session_stats["topics_discussed"].add(topic)
        
        return topics
    
    def _generate_contextual_response(self, user_message: str) -> str:
        """Generate contextual response based on personality and history"""
        personality = self.personalities[self.personality_mode]
        sentiment = self._detect_sentiment(user_message)
        topics = self._extract_topics(user_message)
        
        # Store user message
        self.conversation_history.append({
            "type": "user",
            "content": user_message,
            "sentiment": sentiment,
            "topics": topics,
            "timestamp": datetime.datetime.now().isoformat()
        })
        
        # Track sentiment history
        self.user_profile["sentiment_history"].append(sentiment)
        if len(self.user_profile["sentiment_history"]) > 10:
            self.user_profile["sentiment_history"] = self.user_profile["sentiment_history"][-10:]
        
        # Generate response based on personality
        if self.personality_mode == "friendly":
            response = self._generate_friendly_response(user_message, sentiment, topics)
        elif self.personality_mode == "professional":
            response = self._generate_professional_response(user_message, sentiment, topics)
        elif self.personality_mode == "witty":
            response = self._generate_witty_response(user_message, sentiment, topics)
        elif self.personality_mode == "sage":
            response = self._generate_sage_response(user_message, sentiment, topics)
        else:
            response = "I appreciate you sharing that with me. Could you tell me more?"
        
        # Store bot response
        self.conversation_history.append({
            "type": "bot",
            "content": response,
            "personality": self.personality_mode,
            "timestamp": datetime.datetime.now().isoformat()
        })
        
        self.session_stats["messages_sent"] += 1
        return response
    
    def _generate_friendly_response(self, message: str, sentiment: str, topics: List[str]) -> str:
        """Generate friendly personality response"""
        responses = []
        
        if sentiment == "positive":
            responses = [
                f"That's wonderful! 😊 I love hearing positive news!",
                f"How exciting! 🎉 You sound really happy about that!",
                f"That's fantastic! ✨ It makes me happy to hear you're doing well!"
            ]
        elif sentiment == "negative":
            responses = [
                f"I'm sorry to hear that. 😟 Would you like to talk about it?",
                f"That sounds tough. 💙 I'm here if you need someone to listen.",
                f"I can understand why that would be difficult. 🤗 How are you feeling about it now?"
            ]
        else:
            responses = [
                f"Thanks for sharing that with me! 😊 What's your take on it?",
                f"Interesting! 🤔 I'd love to hear more about your thoughts on this.",
                f"That's really cool! ✨ Tell me what you think about it!"
            ]
        
        base_response = random.choice(responses)
        
        # Add topic-specific follow-up
        if topics:
            topic_responses = {
                "work": "How's your work-life balance these days?",
                "family": "Family is so important! How is everyone doing?",
                "travel": "I love hearing about travel! Where would you like to go next?",
                "food": "Food is one of my favorite topics! Do you enjoy cooking?",
                "technology": "Technology is fascinating! What's caught your interest lately?"
            }
            
            for topic in topics:
                if topic in topic_responses:
                    base_response += f" {topic_responses[topic]}"
                    break
        
        return base_response
    
    def _generate_professional_response(self, message: str, sentiment: str, topics: List[str]) -> str:
        """Generate professional personality response"""
        if sentiment == "positive":
            responses = [
                "That's excellent news. I'm pleased to hear about your positive experience.",
                "Thank you for sharing that update. It sounds like things are progressing well.",
                "I appreciate you keeping me informed of this positive development."
            ]
        elif sentiment == "negative":
            responses = [
                "I understand this presents some challenges. How would you like to address this?",
                "Thank you for bringing this to my attention. What would be most helpful right now?",
                "I see this is a concern. Let's discuss potential solutions."
            ]
        else:
            responses = [
                "Thank you for that information. Could you elaborate on your perspective?",
                "I appreciate you sharing that. What are your thoughts on the matter?",
                "Thank you for the update. How do you see this developing?"
            ]
        
        return random.choice(responses)
    
    def _generate_witty_response(self, message: str, sentiment: str, topics: List[str]) -> str:
        """Generate witty personality response"""
        witty_responses = [
            "Well, that's one way to keep things interesting! 😄 What's the plot twist?",
            "Ah, the plot thickens! 🎭 Do tell me more about this adventure!",
            "Now that's what I call a conversation starter! 🎪 What happens next?",
            "You know how to keep someone on their toes! 🕺 I'm all ears!",
            "That's quite the tale! 📚 I feel like I'm reading a good book!"
        ]
        
        if "work" in topics:
            witty_responses.extend([
                "Ah yes, the thrilling world of work! 💼 At least it pays the bills, right?",
                "Work - that thing we do between weekends! 😉 How's the adventure going?"
            ])
        elif "food" in topics:
            witty_responses.extend([
                "Food talk! 🍕 Now you're speaking my language! Well, if I could eat...",
                "Mmm, food discussions always make me wish I had taste buds! 🤖👨‍🍳"
            ])
        
        return random.choice(witty_responses)
    
    def _generate_sage_response(self, message: str, sentiment: str, topics: List[str]) -> str:
        """Generate sage personality response"""
        sage_responses = [
            "That's a profound observation. Life often teaches us through such experiences.",
            "There's wisdom in what you're sharing. What deeper meaning do you find in this?",
            "Interesting perspective. How has this shaped your understanding of things?",
            "Thank you for that reflection. What lessons do you think this holds?",
            "That resonates deeply. In what ways has this influenced your worldview?"
        ]
        
        if sentiment == "negative":
            sage_responses = [
                "Challenges often carry the seeds of growth within them. What might this be teaching you?",
                "Difficult times can be our greatest teachers. How do you see this shaping you?",
                "There's often hidden wisdom in our struggles. What insights are you gaining?"
            ]
        elif sentiment == "positive":
            sage_responses = [
                "Joy shared is joy doubled. What makes this moment particularly meaningful to you?",
                "Beautiful moments like these remind us of life's gifts. What are you most grateful for?",
                "Happiness often comes from unexpected places. What surprised you about this experience?"
            ]
        
        return random.choice(sage_responses)
    
    def clear_conversation(self) -> Tuple[List, str]:
        """Clear conversation and reset session"""
        self.conversation_history = []
        self.session_stats = {
            "messages_sent": 0,
            "session_start": datetime.datetime.now(),
            "topics_discussed": set()
        }
        status = "🔄 **Conversation cleared!**\n\nReady for a fresh start! How can I help you today?"
        return [], status
    
    def export_conversation(self) -> str:
        """Export conversation history"""
        if not self.conversation_history:
            return "📭 No conversation to export yet!\n\nStart chatting to build up some conversation history."
        
        export_data = {
            "session_info": {
                "start_time": self.session_stats["session_start"].isoformat(),
                "messages_sent": self.session_stats["messages_sent"],
                "topics_discussed": list(self.session_stats["topics_discussed"]),
                "personality_mode": self.personality_mode
            },
            "conversation": [
                msg for msg in self.conversation_history 
                if msg["type"] in ["user", "bot"]
            ],
            "user_profile": {
                "sentiment_pattern": self.user_profile["sentiment_history"],
                "topics_mentioned": list(self.session_stats["topics_discussed"])
            }
        }
        
        # Create readable summary
        summary = f"💬 **Conversation Export**\n\n"
        summary += f"**📊 Session Summary:**\n"
        summary += f"• Duration: {datetime.datetime.now() - self.session_stats['session_start']}\n"
        summary += f"• Messages exchanged: {self.session_stats['messages_sent']}\n"
        summary += f"• Personality mode: {self.personality_mode.title()}\n"
        summary += f"• Topics discussed: {', '.join(self.session_stats['topics_discussed']) if self.session_stats['topics_discussed'] else 'General conversation'}\n\n"
        
        # Sentiment analysis
        sentiments = [msg.get("sentiment", "neutral") for msg in self.conversation_history if msg.get("sentiment")]
        if sentiments:
            pos_count = sentiments.count("positive")
            neg_count = sentiments.count("negative")
            neu_count = sentiments.count("neutral")
            summary += f"**😊 Sentiment Analysis:**\n"
            summary += f"• Positive: {pos_count} ({pos_count/len(sentiments)*100:.1f}%)\n"
            summary += f"• Neutral: {neu_count} ({neu_count/len(sentiments)*100:.1f}%)\n"
            summary += f"• Negative: {neg_count} ({neg_count/len(sentiments)*100:.1f}%)\n\n"
        
        # Sample conversation
        user_messages = [msg for msg in self.conversation_history if msg["type"] == "user"]
        bot_messages = [msg for msg in self.conversation_history if msg["type"] == "bot"]
        
        if user_messages and bot_messages:
            summary += f"**💭 Conversation Sample:**\n"
            summary += f"You: {user_messages[0]['content'][:100]}...\n"
            summary += f"Bot: {bot_messages[0]['content'][:100]}...\n\n"
        
        summary += f"**📄 Full Data:**\n```json\n{json.dumps(export_data, indent=2)[:500]}...\n```"
        
        return summary
    
    def _generate_status_update(self) -> str:
        """Generate current session status"""
        if not self.conversation_history:
            return "👋 **Welcome!**\n\nNo conversation started yet.\nSay hello to begin chatting!"
        
        duration = datetime.datetime.now() - self.session_stats["session_start"]
        user_messages = [msg for msg in self.conversation_history if msg["type"] == "user"]
        
        status = f"💬 **Chat Session Status**\n\n"
        status += f"**⏱️ Session Info:**\n"
        status += f"• Duration: {duration}\n"
        status += f"• Messages: {len(user_messages)} from you, {self.session_stats['messages_sent']} total\n"
        status += f"• Personality: {self.personality_mode.title()}\n\n"
        
        if self.session_stats["topics_discussed"]:
            status += f"**💭 Topics We've Covered:**\n"
            for topic in sorted(self.session_stats["topics_discussed"]):
                status += f"• {topic.title()}\n"
            status += "\n"
        
        # Recent sentiment trend
        recent_sentiments = [
            msg.get("sentiment", "neutral") 
            for msg in self.conversation_history[-5:] 
            if msg.get("sentiment")
        ]
        
        if recent_sentiments:
            sentiment_emoji = {
                "positive": "😊", "negative": "😔", "neutral": "😐"
            }
            trend = " ".join([sentiment_emoji.get(s, "😐") for s in recent_sentiments])
            status += f"**📈 Recent Mood:** {trend}\n\n"
        
        status += f"**🎯 Conversation Quality:**\n"
        if len(user_messages) > 5:
            status += "• Great! We're having a nice long chat\n"
        elif len(user_messages) > 2:
            status += "• Good! Conversation is flowing well\n"
        else:
            status += "• Just getting started!\n"
        
        return status

# Create chatbot instance
chatbot = AdvancedChatBot()

# Enhanced Gradio interface
with gr.Blocks(title="💬 Chat Bot Pro", theme=gr.themes.Soft()) as interface:
    gr.Markdown("""
    # 💬 Chat Bot Pro Agent
    **Advanced conversational AI with personality, memory, and context awareness**
    
    Features: Multiple personalities, sentiment analysis, topic tracking, conversation export
    """)
    
    with gr.Row():
        with gr.Column(scale=3):
            chatbot_ui = gr.Chatbot(
                label="Conversation",
                height=400,
                show_label=True,
                container=True
            )
            
            with gr.Row():
                msg_input = gr.Textbox(
                    label="Your message",
                    placeholder="Type your message here... (Press Enter to send)",
                    lines=2,
                    scale=4
                )
                send_btn = gr.Button("Send 📤", variant="primary", scale=1)
        
        with gr.Column(scale=1):
            personality_selector = gr.Dropdown(
                choices=["friendly", "professional", "witty", "sage"],
                label="🎭 Bot Personality",
                value="friendly",
                interactive=True
            )
            
            personality_info = gr.Textbox(
                label="Personality Description",
                value="Warm, encouraging, and supportive",
                interactive=False,
                lines=2
            )
            
            status_display = gr.Textbox(
                label="📊 Session Status",
                lines=8,
                interactive=False
            )
            
            with gr.Row():
                export_btn = gr.Button("📥 Export Chat", variant="secondary")
                clear_btn = gr.Button("🗑️ Clear Chat", variant="stop")
    
    export_output = gr.Textbox(label="📄 Export Data", lines=10, visible=False)
    
    # Event handlers
    def handle_message(message, chat_history):
        if not message.strip():
            return chat_history, "", chatbot._generate_status_update()
        
        # Generate bot response
        bot_response = chatbot._generate_contextual_response(message)
        
        # Update chat history
        chat_history.append((message, bot_response))
        
        return chat_history, "", chatbot._generate_status_update()
    
    def update_personality_info(personality):
        info = chatbot.personalities.get(personality, {}).get("description", "")
        status_msg = chatbot.set_personality(personality)
        return info, status_msg
    
    def show_export():
        export_data = chatbot.export_conversation()
        return gr.update(visible=True, value=export_data), export_data
    
    def hide_export():
        return gr.update(visible=False), ""
    
    # Event handlers
    personality_selector.change(
        update_personality_info,
        inputs=[personality_selector],
        outputs=[personality_info, status_display]
    )
    
    msg_input.submit(
        handle_message,
        inputs=[msg_input, chatbot_ui],
        outputs=[chatbot_ui, msg_input, status_display]
    )
    
    send_btn.click(
        handle_message,
        inputs=[msg_input, chatbot_ui],
        outputs=[chatbot_ui, msg_input, status_display]
    )
    
    export_btn.click(
        show_export,
        outputs=[export_output, export_output]
    )
    
    clear_btn.click(
        chatbot.clear_conversation,
        outputs=[chatbot_ui, status_display]
    ).then(
        hide_export,
        outputs=[export_output, export_output]
    )
    
    # Initialize status
    interface.load(
        lambda: chatbot._generate_status_update(),
        outputs=[status_display]
    )

if __name__ == "__main__":
    interface.launch(server_port=int(os.environ.get('AGENT_PORT', 7860)))
