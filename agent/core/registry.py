"""Enhanced Registry Module

Extended server discovery and registry functionality with semantic search
and public server discovery capabilities.
"""

import asyncio
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime
import httpx


@dataclass 
class ServerMatch:
    """Represents a server match with confidence score"""
    server: Dict[str, Any]
    confidence: float
    match_reasons: List[str]


class EnhancedRegistry:
    """Enhanced server registry with semantic search and discovery"""
    
    def __init__(self):
        # Initialize with parent GMP registry if available
        try:
            import sys
            sys.path.append(str(Path(__file__).parent.parent.parent))
            from gradio_mcp_playground.registry import ServerRegistry
            self.gmp_registry = ServerRegistry()
        except ImportError:
            self.gmp_registry = None
        
        # Local enhanced registry
        self.enhanced_registry = {}
        self.public_sources = [
            "https://api.github.com/search/repositories?q=gradio+mcp+server",
            "https://huggingface.co/api/spaces?search=mcp",
        ]
        
        # Load enhanced registry data
        self._load_enhanced_registry()
    
    def _load_enhanced_registry(self) -> None:
        """Load enhanced registry with additional metadata"""
        
        # Get base registry from GMP
        if self.gmp_registry:
            base_registry = self.gmp_registry.get_all()
        else:
            base_registry = self._get_fallback_registry()
        
        # Enhance with additional metadata
        for server in base_registry:
            server_id = server.get("id", server.get("name", ""))
            if server_id:
                enhanced_server = self._enhance_server_info(server)
                self.enhanced_registry[server_id] = enhanced_server
    
    def _get_fallback_registry(self) -> List[Dict[str, Any]]:
        """Fallback registry when GMP registry is not available"""
        return [
            {
                "id": "basic-calculator",
                "name": "Basic Calculator",
                "description": "Simple calculator for basic arithmetic operations",
                "category": "tools",
                "tags": ["calculator", "math", "arithmetic"],
                "template": "calculator"
            },
            {
                "id": "text-processor",
                "name": "Text Processor",
                "description": "Text processing and manipulation tools",
                "category": "text",
                "tags": ["text", "processing", "string"],
                "template": "basic"
            },
            {
                "id": "data-analyzer",
                "name": "Data Analyzer",
                "description": "CSV and data analysis tools",
                "category": "data",
                "tags": ["data", "csv", "analysis", "pandas"],
                "template": "data-analyzer"
            },
            {
                "id": "image-processor",
                "name": "Image Processor",
                "description": "Image processing and manipulation",
                "category": "image",
                "tags": ["image", "processing", "pil", "opencv"],
                "template": "image-processor"
            }
        ]
    
    def _enhance_server_info(self, server: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance server information with additional metadata"""
        
        enhanced = server.copy()
        
        # Add semantic keywords
        enhanced["semantic_keywords"] = self._extract_semantic_keywords(server)
        
        # Add complexity score
        enhanced["complexity_score"] = self._calculate_complexity_score(server)
        
        # Add use cases
        enhanced["use_cases"] = self._generate_use_cases(server)
        
        # Add required skills
        enhanced["required_skills"] = self._extract_required_skills(server)
        
        # Add similar servers
        enhanced["similar_servers"] = self._find_similar_servers(server)
        
        return enhanced
    
    def _extract_semantic_keywords(self, server: Dict[str, Any]) -> List[str]:
        """Extract semantic keywords for better matching"""
        
        keywords = set()
        
        # From name and description
        text = f"{server.get('name', '')} {server.get('description', '')}".lower()
        
        # Extract domain-specific terms
        domain_patterns = {
            "mathematics": r"math|calculate|arithmetic|algebra|geometry|statistics",
            "data_processing": r"data|csv|excel|pandas|analysis|visualization",
            "text_processing": r"text|string|nlp|language|sentiment|translation",
            "image_processing": r"image|photo|picture|visual|opencv|pil",
            "web_development": r"web|http|api|rest|scraping|crawling",
            "machine_learning": r"ml|ai|model|prediction|classification|regression",
            "file_processing": r"file|document|convert|transform|parse",
            "automation": r"automate|workflow|pipeline|batch|schedule"
        }
        
        for domain, pattern in domain_patterns.items():
            if re.search(pattern, text):
                keywords.add(domain)
        
        # Add existing tags
        keywords.update(server.get("tags", []))
        
        # Add category
        if "category" in server:
            keywords.add(server["category"])
        
        return list(keywords)
    
    def _calculate_complexity_score(self, server: Dict[str, Any]) -> float:
        """Calculate complexity score (0.0 to 1.0)"""
        
        score = 0.0
        
        # Base complexity from category
        category_scores = {
            "starter": 0.1,
            "tools": 0.3,
            "data": 0.5,
            "ai": 0.7,
            "advanced": 0.9,
            "integration": 0.6,
            "web": 0.4
        }
        
        category = server.get("category", "tools")
        score = category_scores.get(category, 0.3)
        
        # Adjust based on tags
        complex_tags = ["ai", "ml", "advanced", "multi-tool", "pipeline"]
        simple_tags = ["basic", "simple", "starter", "calculator"]
        
        tags = server.get("tags", [])
        for tag in tags:
            if tag in complex_tags:
                score += 0.1
            elif tag in simple_tags:
                score -= 0.1
        
        # Ensure score is between 0.0 and 1.0
        return max(0.0, min(1.0, score))
    
    def _generate_use_cases(self, server: Dict[str, Any]) -> List[str]:
        """Generate potential use cases for the server"""
        
        use_cases = []
        category = server.get("category", "")
        tags = server.get("tags", [])
        
        if category == "tools" or "calculator" in tags:
            use_cases.extend([
                "Educational math helper",
                "Financial calculations",
                "Engineering computations",
                "Quick calculations in workflows"
            ])
        
        if category == "data" or "data" in tags:
            use_cases.extend([
                "Business data analysis",
                "Research data processing",
                "Report generation",
                "Data visualization dashboards"
            ])
        
        if category == "text" or "text" in tags:
            use_cases.extend([
                "Content management",
                "Document processing",
                "Language analysis",
                "Text automation"
            ])
        
        if category == "image" or "image" in tags:
            use_cases.extend([
                "Photo editing workflows",
                "Image batch processing",
                "Visual content creation",
                "Computer vision applications"
            ])
        
        if category == "ai" or "ai" in tags:
            use_cases.extend([
                "Intelligent automation",
                "Content generation",
                "Predictive analysis",
                "Smart recommendations"
            ])
        
        return use_cases[:4]  # Return top 4 use cases
    
    def _extract_required_skills(self, server: Dict[str, Any]) -> List[str]:
        """Extract required skills to use the server"""
        
        skills = []
        category = server.get("category", "")
        tags = server.get("tags", [])
        complexity = self._calculate_complexity_score(server)
        
        # Basic skills
        if complexity < 0.3:
            skills.append("Basic computer skills")
        else:
            skills.append("Technical familiarity")
        
        # Domain-specific skills
        if category == "data" or "data" in tags:
            skills.extend(["Data analysis basics", "Spreadsheet knowledge"])
        
        if category == "ai" or "ai" in tags:
            skills.extend(["AI/ML concepts", "Model understanding"])
        
        if "api" in tags or "integration" in tags:
            skills.extend(["API knowledge", "System integration"])
        
        if complexity > 0.7:
            skills.append("Advanced configuration")
        
        return skills[:3]  # Return top 3 skills
    
    def _find_similar_servers(self, server: Dict[str, Any]) -> List[str]:
        """Find similar servers in the registry"""
        
        similar = []
        current_id = server.get("id", "")
        current_category = server.get("category", "")
        current_tags = set(server.get("tags", []))
        
        for other_id, other_server in self.enhanced_registry.items():
            if other_id == current_id:
                continue
            
            similarity_score = 0.0
            
            # Category match
            if other_server.get("category") == current_category:
                similarity_score += 0.5
            
            # Tag overlap
            other_tags = set(other_server.get("tags", []))
            tag_overlap = len(current_tags & other_tags) / max(len(current_tags | other_tags), 1)
            similarity_score += tag_overlap * 0.5
            
            if similarity_score > 0.3:
                similar.append(other_id)
        
        return similar[:3]  # Return top 3 similar servers
    
    async def find_matching_servers(self, requirements: Dict[str, Any]) -> List[ServerMatch]:
        """Find servers matching requirements with confidence scores"""
        
        matches = []
        
        # Extract search criteria from requirements
        search_terms = self._extract_search_terms(requirements)
        functionality = requirements.get("functionality", [])
        ui_prefs = requirements.get("ui_preferences", {})
        
        for server_id, server in self.enhanced_registry.items():
            match_score, reasons = self._calculate_match_score(
                server, search_terms, functionality, ui_prefs
            )
            
            if match_score > 0.2:  # Minimum threshold
                matches.append(ServerMatch(
                    server=server,
                    confidence=match_score,
                    match_reasons=reasons
                ))
        
        # Sort by confidence
        matches.sort(key=lambda x: x.confidence, reverse=True)
        
        return matches
    
    def _extract_search_terms(self, requirements: Dict[str, Any]) -> List[str]:
        """Extract search terms from requirements"""
        
        terms = []
        
        # From functionality
        functionality = requirements.get("functionality", [])
        terms.extend(functionality)
        
        # From UI preferences
        ui_prefs = requirements.get("ui_preferences", {})
        if ui_prefs.get("complexity") == "simple":
            terms.extend(["basic", "simple", "starter"])
        elif ui_prefs.get("complexity") == "advanced":
            terms.extend(["advanced", "complex", "multi-tool"])
        
        return terms
    
    def _calculate_match_score(
        self, 
        server: Dict[str, Any], 
        search_terms: List[str],
        functionality: List[str],
        ui_prefs: Dict[str, Any]
    ) -> tuple[float, List[str]]:
        """Calculate match score for a server"""
        
        score = 0.0
        reasons = []
        
        # Semantic keyword matching
        server_keywords = server.get("semantic_keywords", [])
        keyword_matches = set(search_terms) & set(server_keywords)
        if keyword_matches:
            score += 0.4 * (len(keyword_matches) / max(len(search_terms), 1))
            reasons.append(f"Matches keywords: {', '.join(keyword_matches)}")
        
        # Functionality matching
        if functionality:
            func_score = 0.0
            for func in functionality:
                if func in server.get("description", "").lower():
                    func_score += 0.2
                    reasons.append(f"Supports {func}")
                if func in server_keywords:
                    func_score += 0.3
            score += min(func_score, 0.4)
        
        # UI complexity matching
        complexity_pref = ui_prefs.get("complexity", "medium")
        server_complexity = server.get("complexity_score", 0.5)
        
        if complexity_pref == "simple" and server_complexity < 0.4:
            score += 0.2
            reasons.append("Matches simple complexity preference")
        elif complexity_pref == "advanced" and server_complexity > 0.6:
            score += 0.2
            reasons.append("Matches advanced complexity preference")
        elif complexity_pref == "medium" and 0.3 <= server_complexity <= 0.7:
            score += 0.1
            reasons.append("Matches medium complexity preference")
        
        # Category bonus
        if search_terms:
            category = server.get("category", "")
            if category in search_terms:
                score += 0.1
                reasons.append(f"Category match: {category}")
        
        return score, reasons
    
    async def search_servers(self, query: str) -> List[Dict[str, Any]]:
        """Search for servers using text query"""
        
        query_lower = query.lower()
        results = []
        
        for server_id, server in self.enhanced_registry.items():
            score = 0.0
            
            # Search in name
            if query_lower in server.get("name", "").lower():
                score += 0.5
            
            # Search in description
            if query_lower in server.get("description", "").lower():
                score += 0.3
            
            # Search in tags
            tags = server.get("tags", [])
            if any(query_lower in tag.lower() for tag in tags):
                score += 0.4
            
            # Search in semantic keywords
            keywords = server.get("semantic_keywords", [])
            if any(query_lower in keyword.lower() for keyword in keywords):
                score += 0.3
            
            # Search in use cases
            use_cases = server.get("use_cases", [])
            if any(query_lower in use_case.lower() for use_case in use_cases):
                score += 0.2
            
            if score > 0.1:
                server_with_score = server.copy()
                server_with_score["search_score"] = score
                results.append(server_with_score)
        
        # Sort by score
        results.sort(key=lambda x: x["search_score"], reverse=True)
        
        return results
    
    async def discover_public_servers(self) -> List[Dict[str, Any]]:
        """Discover servers from public sources"""
        
        discovered = []
        
        for source_url in self.public_sources:
            try:
                servers = await self._fetch_from_source(source_url)
                discovered.extend(servers)
            except Exception as e:
                # Log error but continue with other sources
                print(f"Error fetching from {source_url}: {e}")
        
        return discovered
    
    async def _fetch_from_source(self, source_url: str) -> List[Dict[str, Any]]:
        """Fetch servers from a public source"""
        
        servers = []
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(source_url, timeout=10.0)
                data = response.json()
                
                if "github.com" in source_url:
                    servers.extend(self._parse_github_results(data))
                elif "huggingface.co" in source_url:
                    servers.extend(self._parse_huggingface_results(data))
        
        except Exception as e:
            print(f"Failed to fetch from {source_url}: {e}")
        
        return servers
    
    def _parse_github_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse GitHub search results"""
        
        servers = []
        items = data.get("items", [])
        
        for item in items[:10]:  # Limit to top 10 results
            server = {
                "id": f"github-{item['id']}",
                "name": item["name"],
                "description": item.get("description", ""),
                "category": "public",
                "tags": ["github", "community"],
                "url": item["html_url"],
                "source": "github",
                "stars": item.get("stargazers_count", 0),
                "updated": item.get("updated_at", "")
            }
            servers.append(server)
        
        return servers
    
    def _parse_huggingface_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Hugging Face search results"""
        
        servers = []
        
        # Parse HuggingFace API response format
        if isinstance(data, list):
            for item in data[:10]:
                server = {
                    "id": f"hf-{item.get('id', '')}",
                    "name": item.get("name", ""),
                    "description": item.get("description", ""),
                    "category": "public",
                    "tags": ["huggingface", "community"],
                    "url": f"https://huggingface.co/spaces/{item.get('id', '')}",
                    "source": "huggingface",
                    "likes": item.get("likes", 0)
                }
                servers.append(server)
        
        return servers
    
    def get_server_by_id(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get server by ID"""
        return self.enhanced_registry.get(server_id)
    
    def get_servers_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all servers in a category"""
        return [
            server for server in self.enhanced_registry.values()
            if server.get("category") == category
        ]
    
    def get_all_categories(self) -> List[str]:
        """Get all available categories"""
        categories = set()
        for server in self.enhanced_registry.values():
            if "category" in server:
                categories.add(server["category"])
        return sorted(list(categories))
    
    def get_server_recommendations(self, current_server: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get recommendations based on current server"""
        
        similar_ids = current_server.get("similar_servers", [])
        recommendations = []
        
        for server_id in similar_ids:
            server = self.get_server_by_id(server_id)
            if server:
                recommendations.append(server)
        
        return recommendations
    
    def add_custom_server(self, server: Dict[str, Any]) -> None:
        """Add a custom server to the registry"""
        
        server_id = server.get("id", server.get("name", ""))
        if server_id:
            enhanced_server = self._enhance_server_info(server)
            self.enhanced_registry[server_id] = enhanced_server
    
    def remove_server(self, server_id: str) -> bool:
        """Remove a server from the registry"""
        
        if server_id in self.enhanced_registry:
            del self.enhanced_registry[server_id]
            return True
        return False