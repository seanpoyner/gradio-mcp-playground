#!/bin/bash
# Deploy to HF Space Script

echo "🛝 Deploying Gradio MCP Playground to HF Space..."

# Check if we're in a git repo for HF Space
if [ ! -d ".git" ] || ! git remote -v | grep -q "huggingface.co"; then
    echo "📦 Setting up HF Space repository..."
    
    # Clone the space if it doesn't exist
    if [ ! -d "hf-space-gradio-mcp" ]; then
        echo "📥 Cloning HF Space..."
        git clone https://huggingface.co/spaces/seanpoyner/gradio-mcp-playground hf-space-gradio-mcp
    fi
    
    cd hf-space-gradio-mcp
fi

# Copy the HF Space files
echo "📋 Copying HF Space files..."
cp ../app_hf_space.py app.py
cp ../requirements_hf_space.txt requirements.txt
cp ../README_hf_space.md README.md

# Check current status
echo "📊 Current status:"
git status

# Add and commit changes
if ! git diff --quiet || ! git diff --staged --quiet; then
    echo "💾 Committing changes..."
    git add -A
    git commit -m "Update HF Space deployment"
fi

# Push to HF Space
echo "🚀 Pushing to Hugging Face Space..."
git push origin main

echo "✅ Deployment complete!"
echo "🔗 Check your space at: https://huggingface.co/spaces/seanpoyner/gradio-mcp-playground"
echo "📋 Monitor logs at: https://huggingface.co/spaces/seanpoyner/gradio-mcp-playground/logs"