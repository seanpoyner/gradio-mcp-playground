# 🏗️ Gradio MCP Playground - Agent Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     🛝 Gradio MCP Playground                             │
│                                                                         │
│  ┌─────────────────────────┐    ┌──────────────────────────────────┐   │
│  │   Unified Dashboard      │    │        Agent Platform            │   │
│  │  (unified_web_ui.py)     │◄──►│        (agent/app.py)            │   │
│  └─────────────────────────┘    └──────────────────────────────────┘   │
│            │                                    │                        │
│            ▼                                    ▼                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Core Components                               │   │
│  ├─────────────────┬─────────────────┬─────────────────────────────┤   │
│  │ Config Manager  │ Server Manager  │  MCP Connection Manager     │   │
│  │                 │                 │                             │   │
│  │ • YAML configs  │ • Start/Stop    │  • Filesystem access       │   │
│  │ • Prompts       │ • Monitor       │  • GitHub integration      │   │
│  │ • Settings      │ • Deploy        │  • Brave Search            │   │
│  └─────────────────┴─────────────────┴─────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Agent System Components

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Agent Platform                                  │
│                                                                         │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────────┐    │
│  │   Chat Interface │  │ Pipeline Builder  │  │  Control Panel    │    │
│  │                  │  │                   │  │                   │    │
│  │ • 3 AI Modes     │  │ • Visual Design   │  │ • Live Dashboard  │    │
│  │ • Context Aware  │  │ • Drag & Drop     │  │ • Agent Deploy    │    │
│  │ • Tool Access    │  │ • Code Generation │  │ • Health Monitor  │    │
│  └────────┬─────────┘  └─────────┬─────────┘  └────────┬────────┘    │
│           │                       │                       │             │
│           └───────────────────────┴───────────────────────┘             │
│                                   │                                     │
│                                   ▼                                     │
│         ┌─────────────────────────────────────────────────┐            │
│         │              Agent Core (GMPAgent)              │            │
│         │                                                 │            │
│         │  • Intent Recognition  • Task Planning          │            │
│         │  • Context Management  • Code Generation        │            │
│         │  • Knowledge Base      • Error Handling         │            │
│         └─────────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Architecture

```
User Input
    │
    ▼
┌───────────────────┐
│  AI Assistant Tab │
│   (3 Modes)       │
└─────────┬─────────┘
          │
    ┌─────┴─────┬──────────┬────────────┐
    ▼           ▼          ▼            ▼
┌────────┐ ┌─────────┐ ┌──────────┐ ┌─────────┐
│ General│ │   MCP   │ │  Agent   │ │ Direct  │
│  Mode  │ │  Mode   │ │ Builder  │ │ Access  │
└────┬───┘ └────┬────┘ └────┬─────┘ └────┬────┘
     │          │           │             │
     └──────────┴───────────┴─────────────┘
                           │
                           ▼
                 ┌─────────────────┐
                 │ Agent Execution  │
                 │    Framework     │
                 └────────┬────────┘
                          │
         ┌────────────────┴────────────────┐
         ▼                                 ▼
┌─────────────────┐              ┌─────────────────┐
│ Pre-built Agents│              │  Custom Agents  │
├─────────────────┤              ├─────────────────┤
│ • Twitter Blog  │              │ • User Created  │
│ • Web Scraper   │              │ • From Templates│
│ • Data Processor│              │ • AI Generated  │
└─────────────────┘              └─────────────────┘
```

## Agent Lifecycle

```
1. Creation
   ┌─────────────┐
   │   Template  │ ──► Code Generation ──► Validation
   └─────────────┘

2. Deployment
   ┌─────────────┐
   │   Deploy    │ ──► Process Start ──► Port Assignment ──► Health Check
   └─────────────┘

3. Monitoring
   ┌─────────────┐
   │   Running   │ ──► CPU/Memory ──► Status Updates ──► Logs
   └─────────────┘

4. Management
   ┌─────────────┐
   │   Actions   │ ──► Stop/Restart ──► Config Update ──► Export
   └─────────────┘
```

## Pipeline Example

```
Content Creation Pipeline:

┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ Web Scraper │────►│ Data Process │────►│   Twitter   │
│   Agent     │     │    Agent     │     │    Agent    │
└─────────────┘     └──────────────┘     └─────────────┘
      │                    │                     │
      ▼                    ▼                     ▼
  [Raw Data]         [Processed Data]      [Twitter Posts]
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Security Layer                         │
├─────────────────────────────────────────────────────────┤
│  • Input Validation    • Code Sandboxing                │
│  • API Key Encryption  • Rate Limiting                  │
│  • Access Control      • Audit Logging                  │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│               Secure Storage (AES-256)                  │
├─────────────────────────────────────────────────────────┤
│  • Encrypted Credentials  • Machine-specific Keys       │
│  • Token Rotation         • Secure Deletion             │
└─────────────────────────────────────────────────────────┘
```

## Technology Stack

```
Frontend Layer:
├── Gradio 4.31+        # UI Framework
├── HTML5 Canvas        # Pipeline Visualization
├── WebSockets          # Real-time Updates
└── Custom CSS/JS       # Enhanced UI

Backend Layer:
├── Python 3.8+         # Core Runtime
├── asyncio             # Async Operations
├── psutil              # System Monitoring
└── subprocess          # Agent Execution

Protocol Layer:
├── MCP (stdio)         # Primary Protocol
├── HTTP/REST           # API Endpoints
├── WebSocket           # Real-time Communication
└── JSON-RPC            # RPC Protocol

Storage Layer:
├── JSON Files          # Configuration
├── SQLite              # Metadata Storage
├── File System         # Agent Code
└── Encrypted Store     # Credentials
```

## Deployment Options

```
Local Development:
┌─────────────┐
│   Developer │──► python agent/app.py --dev
└─────────────┘

Production - Single Server:
┌─────────────┐
│    Docker   │──► docker run -p 8080:8080 gmp-agent
└─────────────┘

Production - Scalable:
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Load Balancer│────►│  Agent Node │────►│   Database  │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
              [Agent Node]   [Agent Node]

Cloud Platforms:
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ HF Spaces   │  │   Railway   │  │  Kubernetes │
└─────────────┘  └─────────────┘  └─────────────┘
```

---

This architecture diagram illustrates how the Gradio MCP Playground's agent system provides a comprehensive, scalable, and secure platform for building and deploying AI agents without expensive API subscriptions.