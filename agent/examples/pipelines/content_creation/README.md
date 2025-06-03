# Content Creation Pipeline Example

This example demonstrates a complete content creation pipeline that takes a topic, researches it, writes an article, and generates accompanying images.

## Pipeline Overview

```
Topic Input → Research → Writing → Image Generation → Content Assembly → Final Output
```

### Components

1. **Research Module**: Web scraping and information gathering
2. **Writing Module**: AI-powered article generation
3. **Image Module**: AI image generation based on content
4. **Assembly Module**: Combine text and images into final format

## Pipeline Configuration

### Sequential Flow
```json
{
  "name": "content-creation-pipeline",
  "description": "Complete content creation from topic to finished article",
  "type": "sequential",
  "servers": [
    {
      "id": "researcher",
      "name": "Web Research Server",
      "type": "web-scraper",
      "config": {
        "max_sources": 5,
        "timeout": 30,
        "summarize": true
      }
    },
    {
      "id": "writer", 
      "name": "Article Writer",
      "type": "llm-tools",
      "config": {
        "model": "gpt-3.5-turbo",
        "max_words": 1000,
        "tone": "informative"
      }
    },
    {
      "id": "image_generator",
      "name": "Image Generator",
      "type": "image-generator", 
      "config": {
        "model": "stable-diffusion",
        "count": 3,
        "style": "photographic"
      }
    },
    {
      "id": "assembler",
      "name": "Content Assembler",
      "type": "document-processor",
      "config": {
        "format": "markdown",
        "include_metadata": true
      }
    }
  ],
  "connections": [
    {
      "source": "researcher",
      "target": "writer",
      "data_mapping": {
        "research_summary": "context"
      }
    },
    {
      "source": "writer",
      "target": "image_generator", 
      "data_mapping": {
        "article_content": "image_prompts"
      }
    },
    {
      "source": "writer",
      "target": "assembler",
      "data_mapping": {
        "article_text": "content"
      }
    },
    {
      "source": "image_generator",
      "target": "assembler",
      "data_mapping": {
        "generated_images": "images"
      }
    }
  ]
}
```

## Example Usage

### Input
```
Topic: "The Future of Renewable Energy"
```

### Processing Steps

#### 1. Research Phase
- Searches for recent articles about renewable energy
- Extracts key information and statistics
- Summarizes findings into research brief

**Output:**
```
Research Summary:
- Solar and wind costs have dropped 70% since 2010
- Global renewable capacity increased 15% in 2023
- Battery storage technology is key enabler
- Policy support varies by region
- Key challenges: grid integration, storage costs
```

#### 2. Writing Phase
- Takes research summary as context
- Generates comprehensive article
- Maintains consistent tone and structure

**Output:**
```markdown
# The Future of Renewable Energy: A Bright Horizon Ahead

The renewable energy sector is experiencing unprecedented growth, 
driven by technological advances and policy support...

## Key Trends Shaping the Industry

### 1. Dramatic Cost Reductions
Solar and wind energy costs have plummeted by 70% since 2010...

### 2. Energy Storage Revolution
Battery technology improvements are solving intermittency...

### 3. Policy and Market Drivers
Government incentives and corporate commitments...

## Conclusion
The future of renewable energy looks brighter than ever...
```

#### 3. Image Generation Phase
- Analyzes article content for visual concepts
- Generates relevant images for key sections
- Creates consistent visual style

**Generated Images:**
1. Solar farm landscape (for cost reduction section)
2. Battery storage facility (for storage section)  
3. Wind turbines at sunset (for conclusion)

#### 4. Assembly Phase
- Combines article text with generated images
- Adds metadata and formatting
- Creates final deliverable

**Final Output:**
```markdown
---
title: "The Future of Renewable Energy: A Bright Horizon Ahead"
generated_at: "2024-01-20T15:30:00Z"
word_count: 987
images: 3
research_sources: 5
---

# The Future of Renewable Energy: A Bright Horizon Ahead

![Solar Farm](./images/solar_farm_landscape.jpg)
*Modern solar installations demonstrate the scale of renewable growth*

The renewable energy sector is experiencing unprecedented growth...

## Key Trends Shaping the Industry

### 1. Dramatic Cost Reductions

Solar and wind energy costs have plummeted by 70% since 2010...

![Battery Storage](./images/battery_storage_facility.jpg)
*Advanced battery systems are enabling reliable renewable energy*

### 2. Energy Storage Revolution

Battery technology improvements are solving intermittency...

## Conclusion

![Wind Turbines](./images/wind_turbines_sunset.jpg)
*The future of renewable energy looks brighter than ever*

The convergence of technological advancement, policy support, and market forces...

---
*Generated using GMP Agent Content Creation Pipeline*
```

## Building This Pipeline

### Conversation with Agent

```
User: I want to build a content creation pipeline that takes a topic, researches it, writes an article, and generates images

Agent: That's a sophisticated content pipeline! I'll break this down into components:

1. **Research Module**: Web scraping + summarization
2. **Writing Module**: LLM-powered article generation  
3. **Image Module**: AI image generation based on content
4. **Assembly Module**: Combine everything into final output

I found these relevant servers in the registry:
- web-scraper (for research)
- llm-tools (for writing)
- image-generator (for visuals)

Would you like me to create a unified pipeline or separate servers that work together?

User: Create a unified pipeline

Agent: Building your content creation pipeline...

✅ Created research server with web scraping capabilities
✅ Set up LLM-powered writing server  
✅ Configured image generation with Stable Diffusion
✅ Built content assembly and formatting system
✅ Connected all components with data flow mapping
✅ Added error handling and progress tracking

Your content creation pipeline is ready!

**Features:**
- Research any topic from web sources
- Generate comprehensive articles
- Create relevant images automatically
- Assemble into professional format
- Support for multiple output formats

**Usage:**
1. Enter a topic
2. Pipeline automatically researches and writes
3. Generates accompanying images
4. Delivers complete article package

Want to test it with a topic?
```

## Configuration Options

### Research Settings
- **Max Sources**: Number of sources to research
- **Search Depth**: How detailed the research should be
- **Summarization**: Level of summary vs. raw data
- **Source Types**: Academic, news, blogs, etc.

### Writing Settings
- **Article Length**: Word count target
- **Writing Style**: Academic, casual, technical, etc.
- **Structure**: Outline template to follow
- **Citations**: Include source references

### Image Settings
- **Image Count**: Number of images to generate
- **Art Style**: Photographic, illustration, artistic
- **Resolution**: Output image dimensions
- **Themes**: Visual themes to emphasize

### Assembly Settings
- **Output Format**: Markdown, HTML, PDF, Word
- **Template**: Layout and styling template
- **Metadata**: Include generation details
- **Export Options**: File formats and delivery

## Customization Examples

### Academic Research Paper
```json
{
  "research": {
    "source_types": ["academic", "peer_reviewed"],
    "citation_style": "APA"
  },
  "writing": {
    "style": "academic",
    "length": 3000,
    "include_references": true
  },
  "images": {
    "style": "technical_diagrams",
    "count": 5
  }
}
```

### Blog Post
```json
{
  "research": {
    "source_types": ["news", "blogs", "social"],
    "recency": "last_30_days"
  },
  "writing": {
    "style": "conversational", 
    "length": 800,
    "include_examples": true
  },
  "images": {
    "style": "lifestyle",
    "count": 3
  }
}
```

### Technical Documentation
```json
{
  "research": {
    "source_types": ["documentation", "tutorials"],
    "depth": "comprehensive"
  },
  "writing": {
    "style": "technical",
    "include_code_examples": true,
    "structure": "step_by_step"
  },
  "images": {
    "style": "diagrams",
    "include_screenshots": true
  }
}
```

## Performance Metrics

- **Research Time**: 30-60 seconds
- **Writing Time**: 45-90 seconds  
- **Image Generation**: 60-120 seconds
- **Assembly Time**: 10-15 seconds
- **Total Pipeline**: 2-4 minutes

## Error Handling

The pipeline includes robust error handling:

- **Research Failures**: Fallback to cached content or alternative sources
- **Writing Issues**: Retry with adjusted parameters
- **Image Generation Problems**: Use stock images or skip images
- **Assembly Errors**: Generate basic format as backup

## Monitoring & Logging

- Real-time progress updates
- Component performance metrics
- Error tracking and reporting
- Quality assessment scores
- User feedback integration

This pipeline demonstrates the power of connecting multiple AI services into a cohesive workflow that can produce professional content automatically.