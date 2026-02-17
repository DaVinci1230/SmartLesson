@echo off
echo ========================================
echo SmartLesson - Quick Deployment Setup
echo ========================================
echo.

REM Check if git is installed
where git >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Git is not installed!
    echo Please download from: https://git-scm.com/download/win
    echo.
    pause
    exit /b 1
)

echo [1/6] Initializing git repository...
git init
if %ERRORLEVEL% NEQ 0 (
    echo Git already initialized or error occurred
)

echo.
echo [2/6] Adding files to git...
git add .

echo.
echo [3/6] Creating initial commit...
git commit -m "Initial commit - SmartLesson application"

echo.
echo [4/6] Creating main branch...
git branch -M main

echo.
echo ========================================
echo NEXT STEPS:
echo ========================================
echo 1. Create a new repository on GitHub:
echo    - Go to: https://github.com/new
echo    - Repository name: SmartLesson
echo    - Click "Create repository" (DO NOT initialize with README)
echo.
echo 2. Copy your GitHub username (you'll need it next)
echo.
set /p USERNAME="Enter your GitHub username: "
echo.
echo [5/6] Linking to GitHub...
git remote add origin https://github.com/%USERNAME%/SmartLesson.git

echo.
echo [6/6] Pushing to GitHub...
echo You may be asked to authenticate with GitHub
git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo SUCCESS! Code pushed to GitHub
    echo ========================================
    echo.
    echo FINAL STEPS - Deploy to Streamlit Cloud:
    echo ========================================
    echo 1. Go to: https://share.streamlit.io
    echo 2. Click "Sign in with GitHub"
    echo 3. Click "New app"
    echo 4. Select:
    echo    - Repository: %USERNAME%/SmartLesson
    echo    - Branch: main
    echo    - Main file: app.py
    echo 5. Click "Advanced settings"
    echo 6. In Secrets, paste this:
    echo    GEMINI_API_KEY = "paste-your-gemini-api-key-here"
    echo 7. Click "Deploy!"
    echo.
    echo Your app will be live at:
    echo https://%USERNAME%-smartlesson.streamlit.app
    echo ========================================
) else (
    echo.
    echo [ERROR] Failed to push to GitHub
    echo Check if the repository exists and you have access
    echo You can try manually: git push -u origin main
)

echo.
pause
