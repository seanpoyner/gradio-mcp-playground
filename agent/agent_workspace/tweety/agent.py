#!/usr/bin/env python3
"""Generated agent: tweety"""

import sys
import os
import logging

# Setup logging for the agent
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tweety")

try:
    logger.info("Starting agent: tweety")
    
    # User's agent code
    """
    🐦 Twitter Blog Agent

    AGENT_INFO = {
        "name": "🐦 Twitter Blog Agent",
        "description": "Automated Twitter thread generation and posting from blog posts with directory monitoring",
        "category": "Automation",
        "difficulty": "Advanced",
        "features": [
            "Blog directory monitoring for new markdown posts",
            "AI-powered Twitter thread generation using Google Gemini",
            "Automated Twitter posting with proper reply chains",
            "File tracking to process only new posts",
            "Configuration through Gradio interface",
            "Rate limiting and error handling for Twitter API"
        ],
        "version": "1.0.0",
        "author": "Agent System"
    }
    """

    import os
    import time
    import json
    import yaml
    import re
    import threading
    import asyncio
    from datetime import datetime, timezone
    from typing import List, Optional, Dict, Any, Callable
    from pathlib import Path
    import gradio as gr
    import tweepy
    import google.generativeai as genai
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    import hashlib
    import random
    import requests
    from bs4 import BeautifulSoup
    from urllib.parse import urlparse

    # Import secure storage from gradio_mcp_playground
    try:
        import sys
        sys.path.append(str(Path(__file__).parent.parent))
        from gradio_mcp_playground.config_manager import ConfigManager
        HAS_SECURE_STORAGE = True
    except ImportError:
        HAS_SECURE_STORAGE = False
        ConfigManager = None


    class WebContentFetcher:
        """Fetches content from web URLs for processing."""
    
        def __init__(self):
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
    
        def fetch_blog_content(self, url: str) -> Dict[str, str]:
            """Fetch blog content from URL."""
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
            
                soup = BeautifulSoup(response.content, 'html.parser')
            
                # Extract title
                title = ""
                title_tag = soup.find('title')
                if title_tag:
                    title = title_tag.get_text().strip()
            
                # Try to extract main content using common selectors
                content_selectors = [
                    'article',
                    '.post-content',
                    '.entry-content', 
                    '.content',
                    '.post-body',
                    'main',
                    '.article-content',
                    '[role="main"]'
                ]
            
                content = ""
                for selector in content_selectors:
                    content_elem = soup.select_one(selector)
                    if content_elem:
                        # Remove script and style elements
                        for script in content_elem(["script", "style"]):
                            script.decompose()
                        content = content_elem.get_text()
                        break
            
                # If no specific content found, use body
                if not content:
                    body = soup.find('body')
                    if body:
                        for script in body(["script", "style", "nav", "footer", "header"]):
                            script.decompose()
                        content = body.get_text()
            
                # Clean up content
                content = re.sub(r'\s+', ' ', content).strip()
            
                return {
                    "title": title,
                    "content": content[:4000],  # Limit content length
                    "url": url
                }
            
            except Exception as e:
                return {
                    "title": "Error fetching content",
                    "content": f"Could not fetch content from {url}: {str(e)}",
                    "url": url
                }


    class BlogPost:
        """Represents a blog post with metadata and content."""
    
        def __init__(self, filepath: str):
            self.filepath = filepath
            self.content = ""
            self.metadata = {}
            self.created_time = os.path.getctime(filepath)
            self.parse_file()
    
        def parse_file(self):
            """Parse markdown file with YAML front matter."""
            try:
                with open(self.filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                    # Split front matter and content
                    parts = content.split('---', 2)
                
                    if len(parts) >= 3:
                        try:
                            self.metadata = yaml.safe_load(parts[1]) or {}
                            if not isinstance(self.metadata, dict):
                                self.metadata = {}
                        except yaml.YAMLError:
                            self.metadata = {}
                        self.content = parts[2].strip()
                    else:
                        self.content = content.strip()
                    
            except Exception as e:
                print(f"Error reading file {self.filepath}: {e}")
                self.content = ""
                self.metadata = {}


    class ContentProcessor:
        """Processes different types of content (files, URLs, text) into BlogPost-like objects."""
    
        def __init__(self):
            self.web_fetcher = WebContentFetcher()
    
        def process_file(self, file_path: str) -> BlogPost:
            """Process a file upload."""
            return BlogPost(file_path)
    
        def process_text_content(self, content: str, title: str = "") -> BlogPost:
            """Process raw text content."""
            # Create a temporary BlogPost-like object
            class TextPost:
                def __init__(self, content, title):
                    self.content = content
                    self.metadata = {"title": title} if title else {}
                    self.filepath = "manual_input"
                    self.created_time = time.time()
        
            return TextPost(content, title)
    
        def process_url(self, url: str) -> BlogPost:
            """Process a blog URL."""
            fetched_content = self.web_fetcher.fetch_blog_content(url)
            return self.process_text_content(
                fetched_content["content"], 
                fetched_content["title"]
            )



    class TweetGenerator:
        """Generates Twitter threads from blog posts using Google Gemini AI."""
    
        def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash-lite"):
            self.api_key = api_key
            self.model_name = model_name
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
    
        def clean_tweet(self, tweet: str) -> str:
            """Clean tweet text and ensure it's under character limit."""
            # Remove tweet numbering and labels
            tweet = re.sub(r'^(Tweet \d+:|Step \d+:|#\d+:|\[\w+\])', '', tweet)
        
            # Remove markdown formatting
            tweet = re.sub(r'\*\*(.*?)\*\*', r'\1', tweet)
            tweet = re.sub(r'\*(.*?)\*', r'\1', tweet)
        
            # Clean up any double spaces or newlines
            tweet = re.sub(r'\s+', ' ', tweet).strip()
        
            # Ensure tweet is under limit
            if len(tweet) > 280:
                cutoff = tweet[:277].rfind(' ')
                if cutoff == -1:
                    cutoff = 277
                tweet = tweet[:cutoff] + "..."
        
            return tweet
    
        def generate_tweets(self, blog_post: BlogPost) -> List[str]:
            """Generate a Twitter thread from a blog post."""
            metadata = blog_post.metadata or {}
            title = metadata.get('title', '') if isinstance(metadata, dict) else ''
        
            prompt = f"""
            Generate an engaging Twitter thread about this blog post.
            Format as [MAIN] for first tweet and [REPLY] for subsequent tweets.

            Guidelines:
            - First tweet should hook readers with the main value proposition
            - Each subsequent tweet should dive deep into specific aspects
            - Use full 280 characters when needed for detailed explanations
            - Make it conversational yet informative
            - Include emojis and hashtags naturally
            - Add specific examples and key points
            - Main tweet should include 2-3 relevant hashtags
            - Break complex ideas into digestible chunks
            - End with a compelling call to action
            - Generate 5-8 tweets total for a comprehensive thread

            DO NOT include labels like "Tweet 1:" or "Step 1:"
            Each tweet should read naturally as part of a thread.

            Blog title: {title}
            Blog content:
            {blog_post.content[:4000]}  # Limit content to avoid token limits
            """

            try:
                response = self.model.generate_content(prompt)
                tweets = []
            
                for line in response.text.split('\n'):
                    line = line.strip()
                    if line.startswith('[MAIN]') or line.startswith('[REPLY]'):
                        clean_text = self.clean_tweet(
                            line.replace('[MAIN]', '').replace('[REPLY]', '').strip()
                        )
                        if clean_text and len(clean_text) > 10:  # Ensure meaningful content
                            tweets.append(clean_text)
            
                if not tweets:
                    raise ValueError("No valid tweets generated")
                
                return tweets
            
            except Exception as e:
                print(f"Error generating tweets: {e}")
                # Return a basic tweet as fallback
                fallback_title = title or "New Blog Post"
                return [f"📝 New blog post: {fallback_title}\n\n#tech #coding #programming"]
    
        def generate_tweets_with_prompt(self, blog_post: BlogPost, custom_prompt: str) -> List[str]:
            """Generate a Twitter thread from a blog post using a custom prompt."""
            metadata = blog_post.metadata or {}
            title = metadata.get('title', '') if isinstance(metadata, dict) else ''
        
            # Combine custom prompt with blog content
            full_prompt = f"""
            {custom_prompt}

            Blog title: {title}
            Blog content:
            {blog_post.content[:4000]}  # Limit content to avoid token limits
        
            Format your response as:
            [MAIN] for the first tweet
            [REPLY] for subsequent tweets
        
            Each tweet should be under 280 characters.
            DO NOT include labels like "Tweet 1:" or "Step 1:"
            """

            try:
                response = self.model.generate_content(full_prompt)
                tweets = []
            
                for line in response.text.split('\n'):
                    line = line.strip()
                    if line.startswith('[MAIN]') or line.startswith('[REPLY]'):
                        clean_text = self.clean_tweet(
                            line.replace('[MAIN]', '').replace('[REPLY]', '').strip()
                        )
                        if clean_text and len(clean_text) > 10:  # Ensure meaningful content
                            tweets.append(clean_text)
            
                if not tweets:
                    raise ValueError("No valid tweets generated")
                
                return tweets
            
            except Exception as e:
                print(f"Error generating tweets with custom prompt: {e}")
                # Return a basic tweet as fallback
                fallback_title = title or "New Content"
                return [f"📝 {fallback_title}"]


    class TwitterPoster:
        """Handles posting tweets and managing Twitter API interactions."""
    
        def __init__(self, api_key: str, api_secret: str, access_token: str, access_token_secret: str):
            self.api_key = api_key
            self.api_secret = api_secret
            self.access_token = access_token
            self.access_token_secret = access_token_secret
        
            if not all([api_key, api_secret, access_token, access_token_secret]):
                raise ValueError("Missing Twitter API credentials")

            auth = tweepy.OAuthHandler(api_key, api_secret)
            auth.set_access_token(access_token, access_token_secret)
        
            self.client = tweepy.Client(
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_token_secret
            )

            # Add v1 API for rate limit checking
            self.api = tweepy.API(auth)
        
            # Verify credentials
            try:
                self.client.get_me()
                print("Successfully authenticated with Twitter API")
            except tweepy.Forbidden:
                print("ERROR: Twitter API authentication failed due to permissions issue.")
                raise
            except Exception as e:
                print(f"Twitter API authentication failed: {str(e)}")
                raise

            # Get user info
            try:
                self.user_info = self.client.get_me().data
                self.username = self.user_info.username
                print(f"Authenticated as @{self.username}")
            except Exception as e:
                print(f"Error getting user info: {str(e)}")
                raise

        def check_rate_limits(self) -> bool:
            """Check current rate limits and wait if needed."""
            try:
                limits = self.api.rate_limit_status()
                tweets_remaining = limits['resources']['tweets']['/tweets']['remaining']
                reset_time = limits['resources']['tweets']['/tweets']['reset']
            
                if tweets_remaining == 0:
                    reset_datetime = datetime.fromtimestamp(reset_time, timezone.utc)
                    now = datetime.now(timezone.utc)
                    wait_seconds = (reset_datetime - now).total_seconds() + 10  # Add buffer
                
                    print(f"Rate limit reached. Waiting {wait_seconds:.0f} seconds until {reset_datetime} UTC")
                    time.sleep(wait_seconds)
                    return False
            
                print(f"Rate limits: {tweets_remaining} tweets remaining")
                return True
            
            except Exception as e:
                print(f"Error checking rate limits: {e}")
                return True  # Continue if we can't check

        def post_with_retry(self, tweet_func: Callable, max_retries: int = 5, initial_delay: int = 15):
            """Post with exponential backoff retry logic and jitter."""
            delay = initial_delay
            for attempt in range(max_retries):
                try:
                    return tweet_func()
                except tweepy.TooManyRequests:
                    if attempt == max_retries - 1:
                        raise
                    # Add jitter to avoid thundering herd
                    jitter = random.uniform(0, 5)
                    wait_time = delay + jitter
                    print(f"Rate limit hit, waiting {wait_time:.1f} seconds (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(wait_time)
                    delay *= 2  # Exponential backoff
                except Exception as e:
                    print(f"Error: {str(e)}")
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(delay)

        def post_tweets(self, tweets: List[str]) -> bool:
            """Post a Twitter thread with proper reply chains."""
            if not tweets:
                return False
            
            # Check rate limits before starting
            if not self.check_rate_limits():
                print("Rate limits exhausted, try again later")
                return False
            
            try:
                # Add initial delay before starting
                time.sleep(5)
            
                # Post the main tweet first
                main_response = self.post_with_retry(
                    lambda: self.client.create_tweet(text=tweets[0])
                )
                main_tweet_id = main_response.data['id']
                print(f"Main tweet posted: {tweets[0][:50]}...")
            
                # Post replies with rate limit checking between each
                for i, tweet in enumerate(tweets[1:], 1):
                    # Check rate limits before each reply
                    if not self.check_rate_limits():
                        print(f"Stopping after {i} replies due to rate limits")
                        break
                
                    try:
                        base_delay = min(15 + (i * 5), 30)  # Increased delays
                        jitter = random.uniform(0, 5)
                        time.sleep(base_delay + jitter)
                    
                        response = self.post_with_retry(
                            lambda: self.client.create_tweet(
                                text=tweet,
                                in_reply_to_tweet_id=main_tweet_id
                            )
                        )
                        main_tweet_id = response.data['id']  # Update for next reply
                        print(f"Reply {i} posted: {tweet[:50]}...")
                    
                    except Exception as e:
                        print(f"Error posting reply {i}: {str(e)}")
                        time.sleep(60)  # Longer wait after errors
            
                return True
                    
            except Exception as e:
                print(f"Error in tweet thread: {str(e)}")
                return False


    class BlogMonitor(FileSystemEventHandler):
        """Monitors blog directory for new markdown files."""
    
        def __init__(self, callback: Callable[[BlogPost], None], state_file: str):
            self.callback = callback
            self.state_file = state_file
            self.processed_files = self.load_state()

        def load_state(self) -> Dict[str, float]:
            """Load processed files state from JSON file."""
            try:
                if os.path.exists(self.state_file):
                    with open(self.state_file, 'r') as f:
                        return json.load(f)
            except Exception as e:
                print(f"Error loading state file: {e}")
            return {}

        def save_state(self):
            """Save processed files state to JSON file."""
            try:
                os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
                with open(self.state_file, 'w') as f:
                    json.dump(self.processed_files, f, indent=2)
            except Exception as e:
                print(f"Error saving state file: {e}")

        def on_created(self, event):
            """Handle new file creation events."""
            if event.is_directory or not event.src_path.endswith('.md'):
                return
        
            # Wait a brief moment to ensure file is fully written
            time.sleep(2)
        
            filepath = event.src_path
            file_hash = self.get_file_hash(filepath)
        
            # Check if we've already processed this file
            if filepath in self.processed_files:
                return
        
            print(f"New blog post detected: {os.path.basename(filepath)}")
        
            try:
                post = BlogPost(filepath)
                self.processed_files[filepath] = time.time()
                self.save_state()
                self.callback(post)
            except Exception as e:
                print(f"Error processing new file {filepath}: {e}")

        def get_file_hash(self, filepath: str) -> str:
            """Get file hash for duplicate detection."""
            try:
                with open(filepath, 'rb') as f:
                    return hashlib.md5(f.read()).hexdigest()
            except Exception:
                return ""

        def process_existing_files(self, directory: str):
            """Process any existing files that haven't been processed yet."""
            try:
                for filename in os.listdir(directory):
                    if filename.endswith('.md'):
                        filepath = os.path.join(directory, filename)
                    
                        # Only process if not already processed
                        if filepath not in self.processed_files:
                            print(f"Processing existing file: {filename}")
                            try:
                                post = BlogPost(filepath)
                                self.processed_files[filepath] = time.time()
                                self.callback(post)
                            except Exception as e:
                                print(f"Error processing existing file {filepath}: {e}")
            
                self.save_state()
            
            except Exception as e:
                print(f"Error processing existing files: {e}")


    class TwitterBlogAgent:
        """Main Twitter Blog Automation Agent."""
    
        def __init__(self):
            self.observer = None
            self.is_running = False
            self.config = {}
            self.tweet_generator = None
            self.twitter_poster = None
            self.content_processor = ContentProcessor()
            self.state_file = "temp_agents/twitter_agent_state.json"
            self.processing_history = []
        
            # Initialize secure config manager
            self.config_manager = ConfigManager() if HAS_SECURE_STORAGE else None
        
            # Available Gemini models
            self.available_models = [
                "gemini-2.0-flash-lite",
                "gemini-2.0-flash",
                "gemini-2.5-flash-preview-tts", 
                "gemini-2.5-flash-preview-05-20"
            ]
        
            # Auto-load saved configuration on startup
            self.auto_load_config()
    
        def auto_load_config(self) -> None:
            """Automatically load saved configuration on startup if available."""
            if not self.config_manager or not self.config_manager.has_secure_storage():
                self.startup_message = "⚪ No secure storage available for auto-loading configuration"
                return
        
            try:
                config, _ = self.load_config_securely()
                if config and config.get('gemini_api_key'):
                    # Only auto-load if we have at least the essential API key
                    result = self.update_config(config)
                    if "successfully" in result.lower():
                        self.startup_message = "✅ Configuration auto-loaded from secure storage"
                    else:
                        self.startup_message = f"⚠️ Auto-load failed: {result}"
                else:
                    self.startup_message = "⚪ No saved configuration found to auto-load"
            except Exception as e:
                self.startup_message = f"❌ Auto-load error: {str(e)}"
    
        def get_startup_status(self) -> str:
            """Get startup status message."""
            return getattr(self, 'startup_message', '⚪ Ready for configuration')
    
        def update_config(self, config: Dict[str, Any]) -> str:
            """Update agent configuration."""
            try:
                self.config = config
            
                # Validate required fields (blog directory is now optional)
                required_fields = [
                    'twitter_api_key', 'twitter_api_secret', 
                    'twitter_access_token', 'twitter_access_token_secret',
                    'gemini_api_key'
                ]
            
                missing = [field for field in required_fields if not config.get(field)]
                if missing:
                    return f"Missing required fields: {', '.join(missing)}"
            
                # Validate blog directory only if provided
                if config.get('blog_directory') and not os.path.exists(config['blog_directory']):
                    return f"Blog directory does not exist: {config['blog_directory']}"
            
                # Get model name, default to gemini-2.0-flash-lite
                model_name = config.get('gemini_model', 'gemini-2.0-flash-lite')
            
                # Initialize components
                self.tweet_generator = TweetGenerator(config['gemini_api_key'], model_name)
                self.twitter_poster = TwitterPoster(
                    config['twitter_api_key'],
                    config['twitter_api_secret'],
                    config['twitter_access_token'],
                    config['twitter_access_token_secret']
                )
            
                return "Configuration updated successfully!"
            
            except Exception as e:
                return f"Configuration error: {str(e)}"
    
        def process_manual_content(self, content_type: str, content_input: str, custom_prompt: str = "") -> str:
            """Process manually provided content (file, URL, or text)."""
            try:
                if not self.tweet_generator or not self.twitter_poster:
                    return "❌ Agent not properly configured. Please set up API keys first."
            
                # Process based on content type
                if content_type == "file_upload" and content_input:
                    post = self.content_processor.process_file(content_input)
                elif content_type == "url" and content_input:
                    if not self._is_valid_url(content_input):
                        return "❌ Please provide a valid URL"
                    post = self.content_processor.process_url(content_input)
                elif content_type == "text" and content_input:
                    post = self.content_processor.process_text_content(content_input, "Manual Input")
                else:
                    return "❌ Please provide valid content to process"
            
                # Generate tweets with custom prompt if provided
                if custom_prompt:
                    tweets = self.tweet_generator.generate_tweets_with_prompt(post, custom_prompt)
                else:
                    tweets = self.tweet_generator.generate_tweets(post)
            
                # Store in history for review
                processing_entry = {
                    "timestamp": datetime.now().isoformat(),
                    "content_type": content_type,
                    "source": content_input[:100] + "..." if len(content_input) > 100 else content_input,
                    "custom_prompt": custom_prompt,
                    "tweets_generated": len(tweets),
                    "tweets": tweets
                }
                self.processing_history.append(processing_entry)
            
                # Format response
                response = f"✅ Generated {len(tweets)} tweets from {content_type}\n\n"
                response += "**Generated Tweets:**\n\n"
                for i, tweet in enumerate(tweets, 1):
                    response += f"**Tweet {i}:**\n{tweet}\n\n"
            
                response += "\nUse 'Post Generated Tweets' to publish these tweets."
            
                return response
            
            except Exception as e:
                return f"❌ Error processing content: {str(e)}"
    
        def post_last_generated_tweets(self) -> str:
            """Post the most recently generated tweets."""
            try:
                if not self.processing_history:
                    return "❌ No tweets generated yet. Please generate tweets first."
            
                if not self.twitter_poster:
                    return "❌ Twitter API not configured"
            
                last_entry = self.processing_history[-1]
                tweets = last_entry["tweets"]
            
                success = self.twitter_poster.post_tweets(tweets)
            
                if success:
                    return f"✅ Successfully posted Twitter thread with {len(tweets)} tweets!"
                else:
                    return "❌ Failed to post Twitter thread. Check logs for details."
                
            except Exception as e:
                return f"❌ Error posting tweets: {str(e)}"
    
        def save_config_securely(self, config: Dict[str, Any]) -> str:
            """Save configuration securely using encryption."""
            if not self.config_manager or not self.config_manager.has_secure_storage():
                return "❌ Secure storage not available"
        
            try:
                # Save each API key separately
                if config.get('twitter_api_key'):
                    self.config_manager.save_secure_token('twitter_api_key', config['twitter_api_key'])
                if config.get('twitter_api_secret'):
                    self.config_manager.save_secure_token('twitter_api_secret', config['twitter_api_secret'])
                if config.get('twitter_access_token'):
                    self.config_manager.save_secure_token('twitter_access_token', config['twitter_access_token'])
                if config.get('twitter_access_token_secret'):
                    self.config_manager.save_secure_token('twitter_access_token_secret', config['twitter_access_token_secret'])
                if config.get('gemini_api_key'):
                    self.config_manager.save_secure_token('gemini_api_key', config['gemini_api_key'])
            
                # Save non-sensitive config to regular config
                non_sensitive_config = {
                    'blog_directory': config.get('blog_directory', ''),
                    'gemini_model': config.get('gemini_model', 'gemini-2.0-flash-lite')
                }
                self.config_manager.set('twitter_blog_agent', non_sensitive_config)
            
                return "✅ Configuration saved securely"
            
            except Exception as e:
                return f"❌ Error saving config: {str(e)}"
    
        def load_config_securely(self) -> Dict[str, str]:
            """Load configuration securely from encrypted storage."""
            if not self.config_manager or not self.config_manager.has_secure_storage():
                return {}, "Secure storage not available"
        
            try:
                config = {}
                status_parts = []
            
                # Load API keys
                keys_to_load = [
                    'twitter_api_key', 'twitter_api_secret', 
                    'twitter_access_token', 'twitter_access_token_secret', 
                    'gemini_api_key'
                ]
            
                for key in keys_to_load:
                    value = self.config_manager.load_secure_token(key)
                    if value:
                        config[key] = value
                        status_parts.append(f"{key}: ✓")
                    else:
                        config[key] = ""
                        status_parts.append(f"{key}: ✗")
            
                # Load non-sensitive config
                non_sensitive_config = self.config_manager.get('twitter_blog_agent', {})
                config.update(non_sensitive_config)
            
                status = "✅ Configuration loaded:\n" + "\n".join(status_parts)
            
                return config, status
            
            except Exception as e:
                return {}, f"❌ Error loading config: {str(e)}"
    
        def clear_saved_config(self) -> str:
            """Clear all saved configuration from secure storage."""
            if not self.config_manager or not self.config_manager.has_secure_storage():
                return "❌ Secure storage not available"
        
            try:
                # Clear API keys
                keys_to_clear = [
                    'twitter_api_key', 'twitter_api_secret', 
                    'twitter_access_token', 'twitter_access_token_secret', 
                    'gemini_api_key'
                ]
            
                for key in keys_to_clear:
                    self.config_manager.delete_secure_token(key)
            
                # Clear non-sensitive config
                self.config_manager.set('twitter_blog_agent', {})
            
                return "🗑️ Configuration cleared from secure storage"
            
            except Exception as e:
                return f"❌ Error clearing config: {str(e)}"
    
        def get_processing_history(self) -> str:
            """Get formatted processing history."""
            if not self.processing_history:
                return "No processing history available."
        
            history_text = "**Recent Processing History:**\n\n"
        
            for i, entry in enumerate(reversed(self.processing_history[-5:]), 1):
                history_text += f"**{i}. {entry['timestamp']}**\n"
                history_text += f"• Type: {entry['content_type']}\n"
                history_text += f"• Source: {entry['source']}\n"
                if entry['custom_prompt']:
                    history_text += f"• Custom Prompt: {entry['custom_prompt'][:100]}...\n"
                history_text += f"• Tweets Generated: {entry['tweets_generated']}\n\n"
        
            return history_text
    
        def _is_valid_url(self, url: str) -> bool:
            """Check if URL is valid."""
            try:
                result = urlparse(url)
                return all([result.scheme, result.netloc])
            except:
                return False
    
        def process_blog_post(self, post: BlogPost):
            """Process a single blog post (for directory monitoring)."""
            try:
                print(f"Processing: {os.path.basename(post.filepath)}")
            
                if not self.tweet_generator or not self.twitter_poster:
                    print("Agent not properly configured")
                    return
            
                # Generate tweets
                tweets = self.tweet_generator.generate_tweets(post)
                print(f"Generated {len(tweets)} tweets")
            
                # Post tweets
                success = self.twitter_poster.post_tweets(tweets)
            
                if success:
                    print(f"Successfully posted Twitter thread for {os.path.basename(post.filepath)}")
                else:
                    print(f"Failed to post Twitter thread for {os.path.basename(post.filepath)}")
                
            except Exception as e:
                print(f"Error processing blog post {post.filepath}: {e}")
    
        def start_monitoring(self) -> str:
            """Start monitoring the blog directory."""
            try:
                if self.is_running:
                    return "Agent is already running"
            
                if not self.config.get('blog_directory'):
                    return "Blog directory not configured. Directory monitoring is optional - you can still use manual content processing."
            
                if not all([self.tweet_generator, self.twitter_poster]):
                    return "Agent not properly configured"
            
                # Create monitor
                monitor = BlogMonitor(self.process_blog_post, self.state_file)
            
                # Process existing files first
                monitor.process_existing_files(self.config['blog_directory'])
            
                # Start monitoring
                self.observer = Observer()
                self.observer.schedule(monitor, self.config['blog_directory'], recursive=False)
                self.observer.start()
            
                self.is_running = True
                return f"Started monitoring: {self.config['blog_directory']}"
            
            except Exception as e:
                return f"Error starting monitor: {str(e)}"
    
        def stop_monitoring(self) -> str:
            """Stop monitoring the blog directory."""
            try:
                if not self.is_running:
                    return "Agent is not running"
            
                if self.observer:
                    self.observer.stop()
                    self.observer.join()
                    self.observer = None
            
                self.is_running = False
                return "Stopped monitoring"
            
            except Exception as e:
                return f"Error stopping monitor: {str(e)}"
    
        def get_status(self) -> Dict[str, Any]:
            """Get current agent status."""
            return {
                "is_running": self.is_running,
                "blog_directory": self.config.get('blog_directory', 'Not configured (optional)'),
                "twitter_configured": bool(self.twitter_poster),
                "gemini_configured": bool(self.tweet_generator),
                "manual_processing_available": bool(self.tweet_generator and self.twitter_poster),
                "recent_manual_processes": len(self.processing_history)
            }


    # Global agent instance
    twitter_agent = TwitterBlogAgent()


    # Create twitter agent instance
    twitter_agent = TwitterBlogAgent()

    # Enhanced Gradio interface
    with gr.Blocks(title="🐦 Twitter Blog Agent", theme=gr.themes.Soft()) as interface:
        gr.Markdown("""
        # 🐦 Twitter Blog Agent
        **Automated Twitter thread generation and posting from blog posts**
    
        Features: Directory monitoring, AI-powered thread generation, automated posting with reply chains
        """)
    
        with gr.Tab("Configuration"):
            gr.Markdown("## API Keys Configuration")
        
            with gr.Row():
                with gr.Column():
                    twitter_api_key = gr.Textbox(
                        label="Twitter API Key (Consumer Key)",
                        type="password",
                        placeholder="Enter your Twitter API Key"
                    )
                    twitter_api_secret = gr.Textbox(
                        label="Twitter API Secret (Consumer Secret)",
                        type="password",
                        placeholder="Enter your Twitter API Secret"
                    )
            
                with gr.Column():
                    twitter_access_token = gr.Textbox(
                        label="Twitter Access Token",
                        type="password",
                        placeholder="Enter your Twitter Access Token"
                    )
                    twitter_access_token_secret = gr.Textbox(
                        label="Twitter Access Token Secret",
                        type="password",
                        placeholder="Enter your Twitter Access Token Secret"
                    )
        
            gemini_api_key = gr.Textbox(
                label="Gemini API Key",
                type="password",
                placeholder="Enter your Google Gemini API Key"
            )
        
            gemini_model = gr.Dropdown(
                label="Gemini Model",
                choices=twitter_agent.available_models,
                value="gemini-2.0-flash-lite",
                info="Select the Gemini model to use for tweet generation"
            )
        
            blog_directory = gr.Textbox(
                label="Blog Directory Path",
                placeholder="Enter the path to your blog posts directory (e.g., /path/to/blog/posts)"
            )
        
            config_status = gr.Textbox(
                label="Configuration Status", 
                interactive=False,
                value=twitter_agent.get_startup_status()
            )
        
            # Secure storage section
            gr.Markdown("### 🔒 Secure Configuration Storage")
            if HAS_SECURE_STORAGE and twitter_agent.config_manager and twitter_agent.config_manager.has_secure_storage():
                gr.Markdown("✅ Secure storage available - API keys will be encrypted and stored safely")
            
                with gr.Row():
                    save_config_btn = gr.Button("💾 Save Configuration Securely", variant="primary")
                    load_config_btn = gr.Button("📂 Load Saved Configuration", variant="secondary")
                    clear_config_btn = gr.Button("🗑️ Clear Saved Configuration", variant="stop")
            
                secure_storage_status = gr.Textbox(label="Secure Storage Status", interactive=False)
            else:
                gr.Markdown("⚠️ Secure storage not available - install cryptography package for encrypted config storage")
                save_config_btn = gr.Button("Save Configuration", variant="primary")
                secure_storage_status = gr.Textbox(value="Secure storage not available", label="Storage Status", interactive=False)
        
            def update_config(twitter_key, twitter_secret, access_token, access_secret, gemini_key, model_name, blog_dir):
                config = {
                    'twitter_api_key': twitter_key,
                    'twitter_api_secret': twitter_secret,
                    'twitter_access_token': access_token,
                    'twitter_access_token_secret': access_secret,
                    'gemini_api_key': gemini_key,
                    'gemini_model': model_name,
                    'blog_directory': blog_dir
                }
                return twitter_agent.update_config(config)
        
            def save_config_securely(twitter_key, twitter_secret, access_token, access_secret, gemini_key, model_name, blog_dir):
                config = {
                    'twitter_api_key': twitter_key,
                    'twitter_api_secret': twitter_secret,
                    'twitter_access_token': access_token,
                    'twitter_access_token_secret': access_secret,
                    'gemini_api_key': gemini_key,
                    'gemini_model': model_name,
                    'blog_directory': blog_dir
                }
                # First update the current config
                update_result = twitter_agent.update_config(config)
                # Then save securely
                save_result = twitter_agent.save_config_securely(config)
                return f"{update_result}\n{save_result}"
        
            def load_config_securely():
                config, status = twitter_agent.load_config_securely()
                if config:
                    return (
                        config.get('twitter_api_key', ''),
                        config.get('twitter_api_secret', ''),
                        config.get('twitter_access_token', ''),
                        config.get('twitter_access_token_secret', ''),
                        config.get('gemini_api_key', ''),
                        config.get('gemini_model', 'gemini-2.0-flash-lite'),
                        config.get('blog_directory', ''),
                        status
                    )
                else:
                    return "", "", "", "", "", "gemini-2.0-flash-lite", "", status
        
            def clear_saved_config():
                result = twitter_agent.clear_saved_config()
                return "", "", "", "", "", "gemini-2.0-flash-lite", "", result
        
            # Connect button events
            if HAS_SECURE_STORAGE and twitter_agent.config_manager and twitter_agent.config_manager.has_secure_storage():
                # Secure storage available
                save_config_btn.click(
                    fn=save_config_securely,
                    inputs=[twitter_api_key, twitter_api_secret, twitter_access_token, 
                           twitter_access_token_secret, gemini_api_key, gemini_model, blog_directory],
                    outputs=secure_storage_status
                )
            
                load_config_btn.click(
                    fn=load_config_securely,
                    outputs=[twitter_api_key, twitter_api_secret, twitter_access_token,
                            twitter_access_token_secret, gemini_api_key, gemini_model, 
                            blog_directory, secure_storage_status]
                )
            
                clear_config_btn.click(
                    fn=clear_saved_config,
                    outputs=[twitter_api_key, twitter_api_secret, twitter_access_token,
                            twitter_access_token_secret, gemini_api_key, gemini_model,
                            blog_directory, secure_storage_status]
                )
            else:
                # Regular save without secure storage
                save_config_btn.click(
                    fn=update_config,
                    inputs=[twitter_api_key, twitter_api_secret, twitter_access_token, 
                           twitter_access_token_secret, gemini_api_key, gemini_model, blog_directory],
                    outputs=config_status
                )
    
        with gr.Tab("Control Panel"):
            gr.Markdown("## Agent Control")
        
            with gr.Row():
                start_btn = gr.Button("🚀 Start Monitoring", variant="primary")
                stop_btn = gr.Button("🛑 Stop Monitoring", variant="secondary")
        
            status_output = gr.Textbox(label="Agent Status", interactive=False, lines=5)
        
            def get_status():
                status = twitter_agent.get_status()
                return (
                    f"Running: {status['is_running']}\n"
                    f"Directory: {status['blog_directory']}\n"
                    f"Twitter API: {'✓' if status['twitter_configured'] else '✗'}\n"
                    f"Gemini API: {'✓' if status['gemini_configured'] else '✗'}"
                )
        
            start_btn.click(fn=twitter_agent.start_monitoring, outputs=status_output)
            stop_btn.click(fn=twitter_agent.stop_monitoring, outputs=status_output)
        
            # Refresh status button
            refresh_btn = gr.Button("🔄 Refresh Status")
            refresh_btn.click(fn=get_status, outputs=status_output)
    
        with gr.Tab("Manual Processing"):
            gr.Markdown("## Manual Content Processing")
            gr.Markdown("Process individual files, URLs, or text content to generate Twitter threads")
        
            # Simplified interface without conditional visibility
            text_input = gr.Textbox(
                label="Text Content",
                placeholder="Enter or paste your content here...",
                lines=8
            )
        
            custom_prompt = gr.Textbox(
                label="Custom Prompt (Optional)",
                placeholder="Add specific instructions for AI generation",
                lines=3
            )
        
            processing_output = gr.Textbox(
                label="Generated Tweets",
                lines=15,
                interactive=False,
                placeholder="Generated tweets will appear here..."
            )
        
            with gr.Row():
                generate_btn = gr.Button("🤖 Generate Tweets", variant="primary")
                post_btn = gr.Button("🐦 Post Generated Tweets", variant="secondary")
        
            processing_status = gr.Textbox(
                label="Status",
                interactive=False,
                lines=2
            )
        
            # Simple processing function
            def process_text_content(text_content, custom_prompt):
                if not text_content.strip():
                    return "❌ Please provide content to process", ""
            
                result = twitter_agent.process_manual_content("text", text_content, custom_prompt)
                return result, "✅ Content processed successfully"
        
            def post_tweets():
                result = twitter_agent.post_last_generated_tweets()
                return result
        
            # Connect buttons to functions
            generate_btn.click(
                fn=process_text_content,
                inputs=[text_input, custom_prompt],
                outputs=[processing_output, processing_status]
            )
        
            post_btn.click(
                fn=post_tweets,
                outputs=processing_status
            )
    
        with gr.Tab("Activity Logs"):
            gr.Markdown("## Recent Activity")
            logs_output = gr.Textbox(
                label="Activity Logs",
                lines=20,
                interactive=False,
                placeholder="Activity logs will appear here..."
            )


    if __name__ == "__main__":
        interface.launch(
            server_port=int(os.environ.get('AGENT_PORT', 7860)),
            share=False,
            inbrowser=False
        )

    
    logger.info("Agent tweety started successfully")
    
except Exception as e:
    logger.error(f"Agent tweety failed to start: {e}")
    sys.exit(1)
