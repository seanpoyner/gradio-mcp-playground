#!/bin/bash
# Deploy to Personal HF Space

echo "🛝 Deploying to Personal Space (seanpoyner/gradio-mcp-playground)..."

# Create temporary directory for personal space
TEMP_DIR="hf-personal-deploy"
rm -rf $TEMP_DIR

# Clone the personal space
echo "📥 Cloning Personal Space..."
git clone https://huggingface.co/spaces/seanpoyner/gradio-mcp-playground $TEMP_DIR

# Enter the directory
cd $TEMP_DIR

# Copy the fixed files
echo "📋 Copying updated files..."
cp ../app_hf_space.py app.py
cp ../requirements-space.txt requirements.txt
cp ../README_hf_space.md README.md

# Check for changes
if ! git diff --quiet || ! git diff --staged --quiet; then
    echo "💾 Committing changes..."
    git add -A
    git commit -m "fix: Update app.py with gr.Group() fix and latest features

- Replace deprecated gr.Box() with gr.Group() for Gradio 4.31.0 compatibility
- Add Claude Desktop integration features
- Update documentation
- Ensure all demo features work correctly"
    
    echo "🚀 Pushing to Personal Space..."
    git push origin main
    
    echo "✅ Personal Space deployment complete!"
    echo "🔗 Check at: https://huggingface.co/spaces/seanpoyner/gradio-mcp-playground"
else
    echo "ℹ️  No changes to deploy"
fi

cd ..