#!/bin/bash
# Deploy to Hackathon HF Space

echo "🏆 Deploying to Hackathon Space (Agents-MCP-Hackathon/gradio-mcp-playground)..."

# Create temporary directory for hackathon space
TEMP_DIR="hf-hackathon-deploy"
rm -rf $TEMP_DIR

# Clone the hackathon space
echo "📥 Cloning Hackathon Space..."
git clone https://huggingface.co/spaces/Agents-MCP-Hackathon/gradio-mcp-playground $TEMP_DIR

# Enter the directory
cd $TEMP_DIR

# Copy the fixed files
echo "📋 Copying updated files..."
cp ../app_hf_space.py app.py
cp ../requirements-space.txt requirements.txt

# Update README to point to hackathon space
cp ../README_hf_space.md README.md
# Update space URLs in README
sed -i 's|seanpoyner/gradio-mcp-playground|Agents-MCP-Hackathon/gradio-mcp-playground|g' README.md

# Check for changes
if ! git diff --quiet || ! git diff --staged --quiet; then
    echo "💾 Committing changes..."
    git add -A
    git commit -m "fix: Update app.py with gr.Group() fix and latest features

- Replace deprecated gr.Box() with gr.Group() for Gradio 4.31.0 compatibility
- Add Claude Desktop integration features
- Update documentation with video placeholder
- Ensure all demo features work correctly"
    
    echo "🚀 Pushing to Hackathon Space..."
    git push origin main
    
    echo "✅ Hackathon Space deployment complete!"
    echo "🔗 Check at: https://huggingface.co/spaces/Agents-MCP-Hackathon/gradio-mcp-playground"
else
    echo "ℹ️  No changes to deploy"
fi

cd ..