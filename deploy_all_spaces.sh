#!/bin/bash
# Deploy to all HF Spaces

echo "🚀 Deploying Gradio MCP Playground to all HF Spaces..."
echo "=================================================="

# Deploy to hackathon space
echo -e "\n1️⃣ Deploying to Hackathon Space..."
./deploy_hackathon_space.sh

echo -e "\n=================================================="

# Deploy to personal space  
echo -e "\n2️⃣ Deploying to Personal Space..."
./deploy_personal_space.sh

echo -e "\n=================================================="
echo "✅ All deployments complete!"
echo ""
echo "📍 Spaces:"
echo "   - Hackathon: https://huggingface.co/spaces/Agents-MCP-Hackathon/gradio-mcp-playground"
echo "   - Personal: https://huggingface.co/spaces/seanpoyner/gradio-mcp-playground"
echo ""
echo "📊 Check logs:"
echo "   - Hackathon logs: https://huggingface.co/spaces/Agents-MCP-Hackathon/gradio-mcp-playground/logs"
echo "   - Personal logs: https://huggingface.co/spaces/seanpoyner/gradio-mcp-playground/logs"