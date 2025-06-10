"""
Conversation Manager for handling context optimization and image data
"""
import json
import re
from typing import Dict, List, Any, Optional, Tuple
import base64
import hashlib


class ConversationManager:
    """Manages conversation context and optimizes for token limits"""
    
    def __init__(self, max_context_length: int = 30000):
        self.max_context_length = max_context_length
        self.image_storage: Dict[str, Dict[str, Any]] = {}
        self.conversation_history: List[Dict[str, Any]] = []
        
    def store_image(self, image_data: str, mime_type: str = "image/png") -> str:
        """Store image data and return a reference ID"""
        # Generate a unique ID for the image
        image_hash = hashlib.md5(image_data.encode()).hexdigest()[:8]
        image_id = f"img_{image_hash}"
        
        self.image_storage[image_id] = {
            "data": image_data,
            "mime_type": mime_type,
            "timestamp": None  # Could add timestamp if needed
        }
        
        return image_id
    
    def process_tool_observation(self, observation: str) -> str:
        """Process tool observations to replace image data with references"""
        # Pattern to match image data in observations
        image_pattern = r"'data': '([A-Za-z0-9+/=]{100,})'.*?'mimeType': '([^']+)'"
        
        def replace_image(match):
            image_data = match.group(1)
            mime_type = match.group(2)
            image_id = self.store_image(image_data, mime_type)
            return f"'image_ref': '{image_id}', 'mimeType': '{mime_type}'"
        
        # Replace image data with references
        processed = re.sub(image_pattern, replace_image, observation)
        
        # Also handle case where image data might be in different format
        if len(processed) > 1000 and "iVBORw0KGgo" in processed:
            # Likely contains base64 image data
            # Extract and replace with reference
            start_idx = processed.find("iVBORw0KGgo")
            if start_idx != -1:
                # Find the end of base64 data
                end_idx = start_idx
                while end_idx < len(processed) and processed[end_idx] in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=":
                    end_idx += 1
                
                if end_idx - start_idx > 100:  # Significant image data
                    image_data = processed[start_idx:end_idx]
                    image_id = self.store_image(image_data)
                    processed = processed[:start_idx] + f"[Image stored as {image_id}]" + processed[end_idx:]
        
        # Truncate very long observations to prevent UI issues
        if len(processed) > 5000:
            processed = processed[:5000] + "\n... (observation truncated)"
        
        return processed
    
    def get_image(self, image_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve stored image data"""
        return self.image_storage.get(image_id)
    
    def compact_conversation(self, messages: List[Dict[str, Any]], target_length: int = 20000) -> List[Dict[str, Any]]:
        """Compact conversation history to fit within token limits"""
        # Simple strategy: keep system message, first few exchanges, and recent messages
        if not messages:
            return messages
            
        # Rough token estimation (4 chars = 1 token)
        def estimate_tokens(text: str) -> int:
            return len(text) // 4
        
        total_tokens = sum(estimate_tokens(str(msg)) for msg in messages)
        
        if total_tokens < target_length:
            return messages
        
        # Keep system message if present
        system_msgs = [msg for msg in messages if msg.get("role") == "system"]
        other_msgs = [msg for msg in messages if msg.get("role") != "system"]
        
        if len(other_msgs) <= 6:  # Too few to compact
            return messages
        
        # Keep first 2 and last 4 message pairs
        compacted = system_msgs.copy()
        
        # Add first exchange
        if len(other_msgs) >= 2:
            compacted.extend(other_msgs[:2])
        
        # Add summary message
        num_omitted = len(other_msgs) - 6
        if num_omitted > 0:
            compacted.append({
                "role": "assistant",
                "content": f"[{num_omitted} messages omitted for brevity. Recent context continues below...]"
            })
        
        # Add recent messages
        compacted.extend(other_msgs[-4:])
        
        return compacted
    
    def summarize_with_slm(self, messages: List[Dict[str, Any]], hf_token: str) -> Optional[str]:
        """Use a small language model to summarize conversation history"""
        # This would call a smaller model like Phi-2 or similar
        # For now, return None to use simple compaction
        return None