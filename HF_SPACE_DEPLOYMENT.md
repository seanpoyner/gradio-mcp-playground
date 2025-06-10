# 🚀 Hugging Face Space Deployment Guide

Follow these steps to deploy the Gradio MCP Playground to your HF Space at `seanpoyner/gradio-mcp-playground`.

## 📋 Pre-Deployment Checklist

- [ ] HF Space exists at https://huggingface.co/spaces/seanpoyner/gradio-mcp-playground
- [ ] You have write access to the space
- [ ] Git is configured with HF credentials

## 🛠️ Deployment Steps

### 1. Clone Your HF Space

```bash
# Clone your existing HF Space
git clone https://huggingface.co/spaces/seanpoyner/gradio-mcp-playground
cd gradio-mcp-playground
```

### 2. Copy Required Files

Copy these files from this directory to your HF Space:

```bash
# Copy the demo app
cp /path/to/app_hf_space.py app.py

# Copy requirements
cp /path/to/requirements_hf_space.txt requirements.txt

# Copy the HF Space README
cp /path/to/README_hf_space.md README.md
```

### 3. Create .gitignore (if needed)

```bash
cat > .gitignore << 'EOF'
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.env
.venv
.DS_Store
*.log
*.db
.idea/
.vscode/
*.swp
*.swo
EOF
```

### 4. Commit and Push

```bash
# Add all files
git add .

# Commit with a descriptive message
git commit -m "🛝 Deploy Gradio MCP Playground for HF MCP Hackathon"

# Push to HF Space
git push origin main
```

### 5. Monitor Build

1. Go to https://huggingface.co/spaces/seanpoyner/gradio-mcp-playground
2. Click on "Logs" tab to monitor the build
3. Wait for the build to complete (usually 2-3 minutes)

## 🎯 Post-Deployment Testing

Test these key features:

1. **AI Assistant Tab**
   - [ ] Try all three modes (Adam, Liam, Arthur)
   - [ ] Test example prompts
   - [ ] Check tool execution display

2. **Server Builder Tab**
   - [ ] Create a calculator server
   - [ ] Test the generated code
   - [ ] Try different templates

3. **MCP Connections Tab**
   - [ ] View connected servers
   - [ ] Test tool execution
   - [ ] Check activity log

4. **Server Management Tab**
   - [ ] Browse demo servers
   - [ ] Test deploy button (simulated)

## 🐛 Troubleshooting

### Build Fails

If the build fails, check:

1. **Requirements**: Ensure all packages are available on HF Spaces
2. **Python Version**: HF Spaces uses Python 3.10
3. **Memory**: Free tier has 16GB RAM limit

### App Crashes

1. Check logs for errors
2. Reduce concurrent operations
3. Simplify demo data if needed

### Slow Performance

1. Enable queue: `demo.queue(max_size=20)`
2. Reduce animation/transitions
3. Optimize image loading

## 🎨 Customization

### Update Branding

In `app.py`, modify:
- Title: Line with "Gradio MCP Playground"
- Emoji: Change 🛝 to your preference
- Colors: Modify theme colors

### Add Your Info

Update these sections:
- GitHub link: Your repository
- Documentation link: Your docs
- Contact info: Your details

### Demo Content

Customize demo data in `setup_demo_data()`:
- Demo agents
- MCP servers
- Example prompts

## 📊 Analytics

Monitor your Space performance:

1. **Views**: Check Space analytics
2. **Usage**: Monitor compute usage
3. **Feedback**: Enable discussions

## 🏁 Final Steps

1. **Test Mobile**: Ensure mobile responsiveness
2. **Share Link**: Submit to hackathon
3. **Create Demo Video**: Record 2-minute demo
4. **Prepare Pitch**: Highlight key features

## 💡 Tips for Success

1. **Keep It Simple**: Focus on working features
2. **Clear CTAs**: Guide users on what to try
3. **Handle Errors**: Graceful error messages
4. **Loading States**: Show progress indicators
5. **Demo Data**: Make it impressive but realistic

## 📞 Support

If you encounter issues:

1. Check HF Spaces documentation
2. Review Gradio docs
3. Ask in HF Discord
4. Create GitHub issue

Good luck with your hackathon submission! 🏆