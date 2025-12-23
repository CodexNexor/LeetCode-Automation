# 🤖 LeetCode Automation with Groq AI

This project automates solving **LeetCode problems** using **Selenium** and **Groq LLM API**.  
It can:

- Open LeetCode in a real browser
- Let you **manually log in** (safe & CAPTCHA-friendly)
- Extract problem description, difficulty, and code template
- Generate an **optimized Python solution using Groq AI**
- Automatically paste and submit the solution
- Retry on failure with feedback

---

## 🚀 Features

- ✅ Manual login (avoids LeetCode bot detection)
- 🧠 AI-powered solution generation using **Groq**
- 🔁 Automatic retry mechanism
- 🧩 Supports Monaco Editor & CodeMirror
- 📄 Logs everything to `leetcode_agent.log`
- 🐍 Python-first (forces Python language)

---

## 📁 Project Structure

LeetCode-Automation

├── main.py # Main automation script


├── leetcode_agent.log # Auto-generated log file


├── .env # Environment variables (you create this)


├── requirements.txt # Python dependencies


└── README.md # Documentation



---

## 🧑‍💻 Requirements

### 1️⃣ System Requirements

- Python **3.9+**
- Google Chrome (latest)
- ChromeDriver (matching your Chrome version)

---

## 📦 Install Dependencies

### Create virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate   # Linux / Mac
venv\Scripts\activate      # Windows
pip install -r requirements.txt


🔐 Environment Variables (.env)

IMPORTANT: Never hardcode API keys in production.

Create a .env file in the root directory:

GROQ_API_KEY=gsk_your_api_key_here

🔧 How the Code Uses .env

In your main.py, replace this:

groq_api_key = "YOUR_API_KEY"


pip install python-dotenv

To Run 
python leetcode.py
```
THANKS All TO READ THIS 

