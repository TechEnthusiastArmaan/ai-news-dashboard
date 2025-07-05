import streamlit as st
import requests
import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
from datetime import datetime
import google.generativeai as genai

# ------------------ Load API Keys & Configure Gemini ------------------
load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Support both local and Streamlit Cloud
GEMINI_API_KEY =  st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")

st.text(f"GEMINI_API_KEY is: {'Yes' if 'GEMINI_API_KEY' in st.secrets else 'No'}")

if not GEMINI_API_KEY:
    st.error("❌ GEMINI_API_KEY not found. Please check your .env file or Streamlit secrets.")
else:
    genai.configure(api_key=GEMINI_API_KEY)

# ------------------ Streamlit Configuration ------------------
st.set_page_config(page_title="📰 AI News Dashboard", layout="wide")
st.markdown("<h1 style='text-align: center;'>🤖 AI News Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Summarized AI news from trusted sources. Stay updated. Stay smart.</p>", unsafe_allow_html=True)

# ------------------ Dark Mode Toggle ------------------
dark_mode = st.toggle("🌙 Enable Dark Mode", value=False)
if dark_mode:
    st.markdown("""
    <style>
    html, body, [data-testid="stApp"] {
        background-color: #0e1117;
        color: #FAFAFA;
    }
    button[class^="css-"], .stButton > button {
        background-color: #1f2937 !important;
        color: #ffffff !important;
        border: 1px solid #4b5563 !important;
    }
    button[class^="css-"]:hover, .stButton > button:hover {
        background-color: #374151 !important;
        border: 1px solid #9ca3af !important;
    }
    input, textarea {
        background-color: #1e1e1e !important;
        color: white !important;
        border: 1px solid #555 !important;
    }
    [data-testid="stExpander"] {
        background-color: #1e1e1e !important;
        color: white !important;
    }
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-thumb { background: #555; }
    </style>
    """, unsafe_allow_html=True)

# ------------------ Subtopic Filtering ------------------
st.markdown("### 🎯 Select AI Subtopic")
topics = {
    "All": "",
    "NLP": "natural language processing",
    "Robotics": "robotics",
    "Ethics": "ai ethics",
    "Healthcare": "ai healthcare",
    "Finance": "ai finance"
}
selected_topic = st.selectbox("Choose AI Subtopic", list(topics.keys()), label_visibility="collapsed")

# ------------------ Refresh Button ------------------
if st.button("🔄 Refresh News Feed"):
    st.cache_data.clear()
    st.rerun()

# ------------------ Fetch News ------------------
@st.cache_data(ttl=3600)
def fetch_ai_news(query):
    base_query = "artificial intelligence OR machine learning"
    topic_query = f" AND {query}" if query else ""
    url = f"https://newsapi.org/v2/everything?q={base_query + topic_query}&sortBy=publishedAt&language=en&pageSize=10&apiKey={NEWS_API_KEY}"
    response = requests.get(url)
    return response.json().get("articles", [])

# ------------------ Summarize with Gemini ------------------
@st.cache_data(ttl=86400)
def summarize_with_gemini(text, url):
    if not text:
        return "No content available to summarize."
    prompt = f"You are a professional content writer. Summarize this article in 2-3 sentences:\n\n{text}\n\nURL: {url}"
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        st.error(f"\u274c Gemini API error: {e}")
        return "Summary not available due to an API error."

# ------------------ Email Sending ------------------
def send_email(recipient, subject, body):
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_SENDER
        msg["To"] = recipient
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception:
        return False

# ------------------ Main News Feed ------------------
with st.spinner("📱 Fetching latest AI news..."):
    articles = fetch_ai_news(topics[selected_topic])

if not articles:
    st.warning("⚠️ No news found or API limit exceeded.")
else:
    summaries = []
    for i, article in enumerate(articles):
        with st.expander(f"📰 {i+1}. {article['title']}"):
            st.markdown(f"**🗳 Source:** {article['source']['name']}")
            st.markdown(f"**📅 Published:** {datetime.strptime(article['publishedAt'], '%Y-%m-%dT%H:%M:%SZ').strftime('%B %d, %Y %I:%M %p')}")
            st.markdown(f"🔗 [Read full article]({article['url']})")
            summary = summarize_with_gemini(article.get("description") or article.get("content") or "", article["url"])
            st.markdown("### 📌 Summary")
            st.write(summary)
            summaries.append(f"{article['title']}\n{summary}\n{article['url']}\n")

# ------------------ Email Subscription ------------------
st.markdown("---")
st.markdown("### 📧 Get Top 5 AI News Summaries via Email")
with st.form("email_form"):
    email_input = st.text_input("Enter your email address")
    send_btn = st.form_submit_button("📬 Send Email")
    if send_btn and email_input:
        email_body = "\n\n".join(summaries[:5])
        if send_email(email_input, "Your AI News Digest", email_body):
            st.success("✅ Email sent successfully!")
        else:
            st.error("❌ Failed to send email. Check your credentials or try again.")

# ------------------ Footer ------------------
st.markdown("---")
st.markdown("<div style='text-align: center; font-size: 14px;'>Built with ❤️ by <b>Armaan Wadhwa</b> | Powered by Streamlit, Gemini & NewsAPI</div>", unsafe_allow_html=True)
