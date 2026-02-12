# ✅ FINBOT Setup Checklist

## Before You Start

- [ ] Python 3.8 or higher installed
- [ ] Terminal/Command Prompt access
- [ ] Text editor (VS Code, PyCharm, etc.)
- [ ] Internet connection (for dependencies)

## Installation Steps

### 1️⃣ Get Your Groq API Key (2 minutes)

- [ ] Visit [https://console.groq.com](https://console.groq.com)
- [ ] Click "Sign Up" or "Log In"
- [ ] Navigate to "API Keys" section
- [ ] Click "Create API Key"
- [ ] Copy the key (starts with `gsk_`)
- [ ] Save it somewhere safe

### 2️⃣ Set Up the Project (3 minutes)

```bash
# Navigate to the project folder
cd finbot-clean

# Install Python dependencies
pip install -r requirements.txt

# Create .env file from template
cp .env.example .env

# Edit .env file and paste your Groq API key
# Replace 'your_groq_api_key_here' with your actual key
```

**Windows Users:**
```cmd
copy .env.example .env
notepad .env
```

**Mac/Linux Users:**
```bash
nano .env
# or
code .env
```

Your `.env` file should look like:
```
GROQ_API_KEY=gsk_your_actual_key_here_1234567890
```

- [ ] Dependencies installed successfully
- [ ] `.env` file created
- [ ] API key added to `.env`

### 3️⃣ Test the Installation (1 minute)

```bash
# Run the application
streamlit run app.py
```

Expected output:
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

- [ ] App starts without errors
- [ ] Browser opens automatically
- [ ] You see the FINBOT interface

### 4️⃣ First Test Run (2 minutes)

- [ ] Click "Browse files" in the app
- [ ] Upload `sample_data.csv` (included in project)
- [ ] Wait for processing (~3 seconds)
- [ ] See data overview with metrics
- [ ] Click "🚀 Analyze Data"
- [ ] Wait for analysis (~5-10 seconds)
- [ ] See results: Health Score, Risk Level, Insights

### 5️⃣ Test Chatbot (2 minutes)

- [ ] In sidebar, select "💬 Chatbot Q&A"
- [ ] Type: "What is the total income?"
- [ ] Press Enter
- [ ] Wait for response (~3-5 seconds)
- [ ] See a data-driven answer
- [ ] Ask a follow-up question
- [ ] Confirm chatbot remembers context

## Troubleshooting Checklist

### Issue: "Module not found" error

- [ ] Verified you're in the `finbot-clean` directory
- [ ] Ran `pip install -r requirements.txt`
- [ ] Using Python 3.8 or higher (`python --version`)
- [ ] Try: `pip install --upgrade pip` then reinstall

### Issue: "GROQ_API_KEY not found"

- [ ] `.env` file exists in project root
- [ ] `.env` file contains: `GROQ_API_KEY=gsk_...`
- [ ] No spaces around the `=` sign
- [ ] API key is valid (test on console.groq.com)
- [ ] Restarted the application after creating `.env`

### Issue: "File upload failed"

- [ ] File is CSV or Excel (.csv, .xlsx, .xls)
- [ ] File size is under 10MB
- [ ] File has valid data (not empty)
- [ ] File is not corrupted
- [ ] Try the provided `sample_data.csv` first

### Issue: "Analysis takes too long"

- [ ] Check your internet connection
- [ ] Verify Groq API is working (check console.groq.com)
- [ ] File might be too large (try smaller file)
- [ ] Check Groq API rate limits

### Issue: "Chatbot doesn't respond"

- [ ] Data is uploaded first
- [ ] API key is valid
- [ ] Internet connection is stable
- [ ] Try refreshing the page
- [ ] Check browser console for errors (F12)

## Optional Enhancements

### Install Optional Dependencies

For better visualizations:
```bash
pip install plotly matplotlib seaborn
```

- [ ] Plotly installed
- [ ] Can create charts (future feature)

### Set Up Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

- [ ] Virtual environment created
- [ ] Virtual environment activated
- [ ] Dependencies installed in venv

## Customization Checklist

### Modify Settings (Optional)

Edit `config/settings.py` to customize:

- [ ] Change memory window size
- [ ] Adjust confidence thresholds
- [ ] Modify max file size
- [ ] Update model temperature

### Change UI Theme (Optional)

Create `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#4F46E5"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F3F4F6"
textColor = "#1F2937"
font = "sans serif"
```

- [ ] Created `.streamlit` folder
- [ ] Created `config.toml`
- [ ] Customized colors
- [ ] Restarted app to see changes

## Production Deployment Checklist

### For Cloud Deployment (Streamlit Cloud, Heroku, etc.)

- [ ] Create `secrets.toml` with API key
- [ ] Update `.gitignore` to exclude `.env`
- [ ] Test on local before deploying
- [ ] Set up environment variables on platform
- [ ] Test the deployed version

### Security Checklist

- [ ] Never commit `.env` file to Git
- [ ] API key is in environment variables only
- [ ] `.gitignore` includes `.env`
- [ ] No sensitive data in code
- [ ] Regular API key rotation

## Success Criteria

You're ready when:

- ✅ App starts without errors
- ✅ Can upload and analyze CSV files
- ✅ Analysis returns health scores and insights
- ✅ Chatbot responds to questions
- ✅ Conversation history is maintained
- ✅ Can switch between Analysis and Chatbot modes
- ✅ Sample data works perfectly

## Next Steps After Setup

1. **Read Documentation**
   - [ ] Read `README.md` for full features
   - [ ] Review `ARCHITECTURE.md` for technical details
   - [ ] Check code comments to understand implementation

2. **Test With Your Data**
   - [ ] Prepare your CSV/Excel file
   - [ ] Upload and analyze
   - [ ] Ask questions in chatbot mode
   - [ ] Review insights and recommendations

3. **Customize**
   - [ ] Modify prompts in agent files
   - [ ] Adjust UI in `app.py`
   - [ ] Add new features as needed

4. **Share**
   - [ ] Star the repository ⭐
   - [ ] Share with friends
   - [ ] Contribute improvements

## Need Help?

- 📖 Check `README.md` for documentation
- 🚀 Read `QUICKSTART.md` for quick reference
- 💡 Review `ARCHITECTURE.md` for technical details
- 🐛 Look at error messages carefully
- 💬 Create an issue on GitHub

## Completion

Setup is complete when all checkboxes above are checked! 

**Status:** [ ] Complete / [ ] In Progress

**Date Completed:** _____________

**Notes:**
_______________________________________________________
_______________________________________________________
_______________________________________________________

---

**Congratulations! You're ready to use FINBOT! 🎉**
