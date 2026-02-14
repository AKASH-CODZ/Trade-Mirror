#!/bin/bash

# TradeMirror Deployment Script
# Automates GitHub push and prepares for Streamlit Cloud deployment

echo "🚀 TradeMirror Deployment Process"
echo "================================="

# Check if we're in the right directory
if [ ! -f "prod/core/ai_coach.py" ]; then
    echo "❌ Error: Not in TradeMirror project root directory"
    exit 1
fi

echo "✅ Project structure verified"

# Check for Git repository
if [ ! -d ".git" ]; then
    echo "🔧 Initializing Git repository..."
    git init
    echo "✅ Git repository initialized"
fi

# Add all files
echo "📦 Adding files to Git..."
git add .

# Create commit
echo "📝 Creating commit..."
git commit -m "Day 4: Hybrid AI Deployment - Local Ollama + Cloud Groq"

# Check if remote exists
if ! git remote get-url origin >/dev/null 2>&1; then
    echo "🔗 Setting up GitHub remote..."
    echo "Please enter your GitHub username:"
    read github_username
    git remote add origin https://github.com/$github_username/TradeMirror.git
fi

# Push to GitHub
echo "📤 Pushing to GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo "✅ Successfully pushed to GitHub!"
    echo ""
    echo "🌐 Next Steps for Streamlit Cloud Deployment:"
    echo "1. Go to https://share.streamlit.io/"
    echo "2. Sign in with your GitHub account"
    echo "3. Click 'New App'"
    echo "4. Select your TradeMirror repository"
    echo "5. Set main file path to: prod/ui/app.py"
    echo "6. In Advanced Settings, add these secrets:"
    echo "   STREAMLIT_SERVER_STATE = \"cloud\""
    echo "   GROQ_API_KEY = \"your_groq_api_key_from_console.groq.com\""
    echo "7. Click 'Deploy'"
    echo ""
    echo "💡 Don't forget to get your free Groq API key from https://console.groq.com"
else
    echo "❌ Git push failed. Please check your GitHub credentials."
fi