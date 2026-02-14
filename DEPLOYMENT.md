# 🚀 TradeMirror Deployment Guide

## 🎯 Hybrid AI Architecture

TradeMirror now supports **hybrid deployment**:
- **Local**: Uses your RTX 5070 with Ollama for maximum performance
- **Cloud**: Uses Groq API for universal accessibility

## 📋 Prerequisites

### Local Development
- Python 3.9+
- Ollama installed and running (`ollama serve`)
- RTX 5070 GPU (recommended)

### Cloud Deployment
- GitHub account
- Free Groq API key from [console.groq.com](https://console.groq.com)
- Streamlit Cloud account (free)

## 🔧 Local Setup

1. **Install Dependencies**:
```bash
cd TradeMirror
pip install -r prod/requirements.txt
```

2. **Start Ollama**:
```bash
ollama serve
```

3. **Run Application**:
```bash
streamlit run prod/ui/app.py
```

## ☁️ Cloud Deployment

### Step 1: Get Groq API Key
1. Visit [console.groq.com](https://console.groq.com)
2. Sign up for free account
3. Create API key
4. Save the key securely

### Step 2: Push to GitHub
```bash
# Make the deployment script executable (if not already)
chmod +x deploy.sh

# Run deployment script
./deploy.sh
```

Or manual Git commands:
```bash
git init
git add .
git commit -m "Day 4: Hybrid AI Deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/TradeMirror.git
git push -u origin main
```

### Step 3: Deploy to Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io/)
2. Sign in with GitHub
3. Click "New App"
4. Select your TradeMirror repository
5. Set configuration:
   - **Main file path**: `prod/ui/app.py`
   - **Python version**: 3.9+
6. In **Advanced Settings** → **Secrets**, add:
```toml
STREAMLIT_SERVER_STATE = "cloud"
GROQ_API_KEY = "your_actual_groq_api_key_here"
```
7. Click "Deploy"

## 🧪 Testing

### Local Testing
```bash
# Test local AI functionality
streamlit run prod/ui/app.py
# Should use Ollama and your RTX 5070
```

### Cloud Testing
1. Visit your deployed app URL
2. Test AI coaching features
3. Should use Groq API automatically

## 🔒 Security Notes

- `.gitignore` prevents sensitive data from being uploaded
- API keys stored securely in Streamlit Cloud secrets
- No financial data transmitted externally
- All processing happens locally or through secured APIs

## 🆘 Troubleshooting

### Common Issues

**Local Ollama Not Working:**
- Ensure `ollama serve` is running
- Check if models are downloaded: `ollama list`
- Install required model: `ollama pull llama3`

**Cloud Deployment Issues:**
- Verify Groq API key is correct
- Check Streamlit Cloud logs for errors
- Ensure all dependencies are in `requirements.txt`

**Git Push Problems:**
- Check GitHub credentials
- Verify repository exists
- Ensure you have write permissions

## 📊 Performance Comparison

| Environment | AI Provider | Speed | Cost | Accessibility |
|-------------|-------------|-------|------|---------------|
| Local       | Ollama/RTX 5070 | Fastest | Free | Requires local setup |
| Cloud       | Groq API | Fast | Free tier | Universal access |

## 🔄 Updates & Maintenance

To update your deployed application:
1. Make changes locally
2. Commit and push to GitHub
3. Streamlit Cloud will auto-deploy

For major updates, consider:
- Testing locally first
- Updating requirements.txt if needed
- Checking API usage limits