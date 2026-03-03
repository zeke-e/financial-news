#!/usr/bin/env python3
"""
Financial News Analyzer with Claude
Fetches daily financial news and generates macro rates-focused analysis
Sends analysis via email
"""

import os
import json
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from anthropic import Anthropic
import socket
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import base64
   
try:
   socket.create_connection(("smtp.gmail.com", 587), timeout=5)
   print("✓ Can reach Gmail SMTP")
except Exception as e:
   print(f"✗ Cannot reach Gmail: {e}")
   
try:
   socket.gethostbyname("gmail.com")
   print("✓ DNS resolution works")
except Exception as e:
   print(f"✗ DNS failed: {e}")

# Initialize the Anthropic client
client = Anthropic()


def fetch_financial_news():
    """
    Fetch financial news from NewsAPI.
    Requires a free API key from https://newsapi.org/
    """
    try:
        import requests
    except ImportError:
        print("Error: 'requests' library not found.")
        print("Install it with: pip install requests")
        return None

    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        print("Error: NEWS_API_KEY environment variable not set")
        print("1. Get a free API key at https://newsapi.org/")
        print("2. Run: export NEWS_API_KEY='your_key_here'")
        return None

    # Fetch top financial news
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": "(Federal Reserve OR macro OR inflation OR interest rates OR currency OR bonds OR treasury OR GDP)",
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": 10,
        "apiKey": api_key,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data["status"] != "ok":
            print(f"Error from NewsAPI: {data.get('message', 'Unknown error')}")
            return None

        articles = data.get("articles", [])
        return articles
    except requests.exceptions.RequestException as e:
        print(f"Error fetching news: {e}")
        return None


def format_news_for_analysis(articles):
    """Format articles into a readable format for Claude analysis"""
    if not articles:
        return "No financial news articles found."

    formatted_news = "## Financial News Summary\n\n"
    for i, article in enumerate(articles, 1):
        formatted_news += f"**Article {i}: {article['title']}**\n"
        formatted_news += f"Source: {article['source']['name']}\n"
        formatted_news += f"Published: {article['publishedAt']}\n"
        formatted_news += f"Summary: {article.get('description', 'No description available')}\n\n"

    return formatted_news


def analyze_with_claude(news_content):
    """
    Send news to Claude for macro rates-focused analysis
    """
    system_prompt = """You are a macro rates trading analyst at a bulge bracket investment bank.
Your role is to analyze daily financial news and provide insights relevant to:
- Federal Reserve policy and interest rate decisions
- Treasury market dynamics and yield curve implications
- Currency markets and FX implications
- Inflation data and economic indicators
- Geopolitical events affecting macro markets
- Cross-asset correlations and trading implications

Provide a concise but insightful analysis that would be useful for a rates trader.
Focus on what matters for fixed income markets, include key takeaways and potential trading implications."""

    user_message = f"""Here's today's financial news. Please provide:
1. **Key Market Movers**: The most significant stories and their immediate implications
2. **Macro Implications**: How these developments affect rates, inflation expectations, and Fed policy
3. **Market Technicals**: Any significant technical levels or chart implications mentioned
4. **Trading Insights**: Potential trading themes or opportunities this creates
5. **Tail Risks**: Any risks or unknowns to watch

{news_content}"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        return message.content[0].text
    except Exception as e:
        return f"Error calling Claude API: {e}\nMake sure your ANTHROPIC_API_KEY is set correctly."


def send_email(analysis, recipient_email):
    """Send the analysis via Gmail SMTP"""
    sender_email = "zeke.abramowicz8@gmail.com"
    app_password = os.getenv("GMAIL_APP_PASSWORD")
    
    if not app_password:
        print("Error: GMAIL_APP_PASSWORD not set")
        return False
    
    try:
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = recipient_email
        message["Subject"] = f"Daily Financial News Analysis - {datetime.now().strftime('%B %d, %Y')}"
        
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6;">
                <h2>Daily Financial News Analysis</h2>
                <p><em>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</em></p>
                <hr>
                <pre style="white-space: pre-wrap; word-wrap: break-word;">
{analysis}
                </pre>
                <hr>
                <p><small>This analysis was generated by Claude analyzing the day's financial news.</small></p>
            </body>
        </html>
        """
        
        message.attach(MIMEText(html_body, "html"))
        
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.send_message(message)
        
        print(f"✓ Email sent successfully to {recipient_email}")
        return True
        
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def save_analysis(analysis):
    """Save analysis to a file with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"financial_analysis_{timestamp}.txt"

    with open(filename, "w") as f:
        f.write(f"Financial News Analysis\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")
        f.write(analysis)

    return filename


def main():
    """Main execution flow"""
    print("=" * 60)
    print("Financial News Analyzer with Claude")
    print("=" * 60)
    print()

    # Fetch news
    print("Fetching financial news...")
    articles = fetch_financial_news()

    if not articles:
        print("Failed to fetch news. Exiting.")
        return

    print(f"Found {len(articles)} relevant articles")
    print()

    # Format news
    formatted_news = format_news_for_analysis(articles)

    # Analyze with Claude
    print("Analyzing with Claude...")
    analysis = analyze_with_claude(formatted_news)

    print()
    print("=" * 60)
    print("ANALYSIS RESULTS")
    print("=" * 60)
    print()
    print(analysis)
    print()

    # Save to file
    filename = save_analysis(analysis)
    print(f"Analysis saved to: {filename}")
    
    # Send email
    print("Sending email...")
    recipient_email = "zeke.abramowicz8@gmail.com"
    if send_email(analysis, recipient_email):
        print("✓ Daily briefing emailed successfully")
    else:
        print("✗ Failed to send email")


if __name__ == "__main__":
    main()
