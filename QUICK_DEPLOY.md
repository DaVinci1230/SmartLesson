# Quick Start - SmartLesson Deployment

## ⚡ FASTEST WAY (5 Minutes)

### Step 1: Get Gemini API Key (1 min)
1. Open: https://makersuite.google.com/app/apikey
2. Click "Get API Key" → "Create API Key"  
3. **Copy the key** (starts with `AIzaSy...`)

### Step 2: Push to GitHub (2 min)

**Option A - Use the automated script:**
```powershell
# Just double-click: deploy_setup.bat
# Follow the prompts
```

**Option B - Manual commands:**
```powershell
git init
git add .
git commit -m "Initial commit"
git branch -M main

# Create repository on GitHub first: https://github.com/new
# Name it: SmartLesson

# Then push (replace YOUR-USERNAME):
git remote add origin https://github.com/YOUR-USERNAME/SmartLesson.git
git push -u origin main
```

### Step 3: Deploy to Streamlit Cloud (2 min)

1. **Go to:** https://share.streamlit.io
2. **Sign in** with GitHub
3. **Click "New app"**
4. **Fill in:**
   - Repository: `YOUR-USERNAME/SmartLesson`
   - Branch: `main`
   - Main file: `app.py`
5. **Click "Advanced settings"**
6. **Add to Secrets:**
   ```toml
   GEMINI_API_KEY = "paste-your-api-key-here"
   ```
7. **Click "Deploy!"**

### Step 4: Share with Teacher

Your app will be live at:
```
https://YOUR-USERNAME-smartlesson.streamlit.app
```

**Share this URL with your teacher!** 🎓

---

## 🔧 Troubleshooting

### "Git not found"
- Download: https://git-scm.com/download/win
- Restart PowerShell after installation

### "Authentication failed"
- GitHub may ask for credentials
- Use: **Personal Access Token** instead of password
- Create at: https://github.com/settings/tokens

### "Module not found" on Streamlit
- Check `requirements.txt` is committed
- Streamlit automatically installs from it

### "API Key not working"
- Make sure no extra spaces in secrets
- Format: `GEMINI_API_KEY = "your-key"`
- Save and reboot app

---

## 📱 Alternative: Quick Demo with ngrok

Just want to show your teacher quickly?

1. **Download ngrok:** https://ngrok.com/download
2. **Run locally:**
   ```powershell
   cd "D:\SOFTWARE ENGINEERING\SmartLesson"
   streamlit run app.py
   ```
3. **In new terminal:**
   ```powershell
   ngrok http 8501
   ```
4. **Share the URL** shown (like `https://abc123.ngrok.io`)

⚠️ URL changes each time. Good for quick demos only.

---

## 📊 Comparison

| Method | Time | Permanent | Effort |
|--------|------|-----------|--------|
| **Streamlit Cloud** | 5 min | ✅ Yes | Easy |
| **ngrok** | 2 min | ❌ No | Easiest |
| **Heroku** | 15 min | ✅ Yes | Medium |

---

## ✅ Final Checklist

- [ ] Got Gemini API key
- [ ] Code pushed to GitHub
- [ ] Deployed to Streamlit Cloud
- [ ] Added API key to secrets
- [ ] App is live and accessible
- [ ] Shared URL with teacher

---

**Need help?** Read the full [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
