# 🚀 Deployment Guide - SmartLesson

Complete step-by-step guide to deploy SmartLesson online so your teacher can access it.

## Method 1: Streamlit Community Cloud (FREE & EASIEST) ⭐

### Step 1: Get Your Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Get API Key"** or **"Create API Key"**
4. Copy the API key (starts with `AIzaSy...`)
5. **Save it somewhere safe** - you'll need it later

### Step 2: Create a GitHub Account (if you don't have one)

1. Go to [github.com](https://github.com)
2. Click **"Sign up"**
3. Follow the registration process

### Step 3: Install Git (if not installed)

**Windows:**
1. Download from [git-scm.com](https://git-scm.com/download/win)
2. Run installer with default settings

**Mac:**
```bash
brew install git
```

**Verify installation:**
```bash
git --version
```

### Step 4: Push Your Code to GitHub

Open PowerShell in your project folder (`D:\SOFTWARE ENGINEERING\SmartLesson`):

```powershell
# Initialize git repository
git init

# Add all files
git add .

# Commit files
git commit -m "Initial commit - SmartLesson application"

# Create repository on GitHub (you'll need to do this manually first)
# Go to github.com → Click "+" → "New repository"
# Name it: SmartLesson
# DO NOT initialize with README (we already have one)
# Click "Create repository"

# Then link and push (replace YOUR-USERNAME with your GitHub username):
git remote add origin https://github.com/YOUR-USERNAME/SmartLesson.git
git branch -M main
git push -u origin main
```

### Step 5: Deploy to Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click **"Sign up"** or **"Sign in with GitHub"**
3. Authorize Streamlit to access your GitHub
4. Click **"New app"**
5. Fill in the form:
   - **Repository:** `YOUR-USERNAME/SmartLesson`
   - **Branch:** `main`
   - **Main file path:** `app.py`
6. Click **"Advanced settings"**
7. In **"Secrets"** section, add:
   ```toml
   GEMINI_API_KEY = "your-actual-gemini-api-key-here"
   ```
8. Click **"Deploy!"**

### Step 6: Access Your App

- Your app will be live at: `https://YOUR-USERNAME-smartlesson.streamlit.app`
- Share this URL with your teacher
- The app is **public** by default (anyone with the link can access)

### Step 7: Make it Private (Optional)

If you want to restrict access:

1. Go to your app dashboard on Streamlit Cloud
2. Click **"Settings"**
3. Under **"Sharing"**, enable **"Restrict viewing to specific users"**
4. Add email addresses of people who can access (your teacher's email)

---

## Method 2: Deploy with ngrok (Temporary/Testing)

If you just want to quickly share for a demo:

1. **Install ngrok:**
   - Download from [ngrok.com](https://ngrok.com/download)
   - Unzip to a folder (e.g., `C:\ngrok`)

2. **Run your Streamlit app locally:**
   ```powershell
   cd "D:\SOFTWARE ENGINEERING\SmartLesson"
   venv\Scripts\activate
   streamlit run app.py
   ```

3. **In a new PowerShell window:**
   ```powershell
   cd C:\ngrok
   .\ngrok http 8501
   ```

4. **Share the URL** shown (e.g., `https://abcd-1234.ngrok.io`)

⚠️ **NOTE:** This URL changes every time you restart ngrok. Free tier has limitations.

---

## Method 3: Heroku (Alternative Cloud Platform)

### Prerequisites:
- Heroku account ([signup.heroku.com](https://signup.heroku.com))
- Heroku CLI installed

### Steps:

1. **Create Procfile:**
   ```
   web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
   ```

2. **Create setup.sh:**
   ```bash
   mkdir -p ~/.streamlit/
   echo "\
   [server]\n\
   port = $PORT\n\
   enableCORS = false\n\
   headless = true\n\
   \n\
   " > ~/.streamlit/config.toml
   ```

3. **Deploy:**
   ```bash
   heroku login
   heroku create your-app-name
   heroku config:set GEMINI_API_KEY=your-gemini-api-key
   git push heroku main
   ```

---

## Troubleshooting

### Issue: "ModuleNotFoundError"
**Solution:** Make sure `requirements.txt` includes all dependencies:
```bash
pip freeze > requirements.txt
```

### Issue: "GEMINI_API_KEY not found"
**Solution:** 
- Streamlit Cloud: Add it in Secrets section
- Local: Set environment variable
- Heroku: Use `heroku config:set`

### Issue: App crashes on startup
**Solution:**
1. Check logs in Streamlit Cloud dashboard
2. Verify all packages in requirements.txt are compatible
3. Test locally first: `streamlit run app.py`

### Issue: Can't push to GitHub
**Solution:**
```bash
# Check your git config
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Try pushing again
git push -u origin main
```

---

## Updating Your Deployed App

After making changes:

```bash
# Save your changes
git add .
git commit -m "Description of changes"
git push

# Streamlit Cloud auto-deploys after each push
```

---

## Cost Summary

| Platform | Cost | Best For |
|----------|------|----------|
| **Streamlit Cloud** | FREE (1 private app) | Most users, easy setup |
| **ngrok** | FREE (limited) | Quick demos, testing |
| **Heroku** | FREE tier available | Alternative to Streamlit |

---

## Security Checklist

✅ API keys in secrets, not in code  
✅ .env file in .gitignore  
✅ No sensitive data in git repository  
✅ Repository can be private on GitHub  
✅ Streamlit app can restrict viewers  

---

## Need Help?

- **Streamlit Community:** [discuss.streamlit.io](https://discuss.streamlit.io)
- **Streamlit Docs:** [docs.streamlit.io](https://docs.streamlit.io)
- **GitHub Docs:** [docs.github.com](https://docs.github.com)

---

## Quick Access

**Your app URL will be:**
```
https://YOUR-GITHUB-USERNAME-smartlesson.streamlit.app
```

Share this link with your teacher! 🎓
