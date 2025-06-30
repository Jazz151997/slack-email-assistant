from flask import Flask, request, jsonify
from slack_sdk import WebClient
import openai
import os
import threading
import httpx

# Optional: Clean up any inherited proxy settings
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("OPENAI_PROXY", None)

app = Flask(__name__)

# Slack client initialization
slack_client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))

# Background task to handle OpenAI + Slack messaging
def process_message(user_input, channel_id):
    try:
        prompt = (
            "You are a helpful product support engineer. "
            "Rewrite the following email to be customer-centric and grammatically correct:\n\n"
            f"{user_input}"
        )

        # Configure OpenAI client with no proxy
        transport = httpx.HTTPTransport(proxy=None)
        ai_client = openai.OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url="https://api.openai.com/v1",
            http_client=httpx.Client(transport=transport)
        )

        # Use GPT-3.5-Turbo (widely available)
        response = ai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=300,
            temperature=0.7
        )

        improved_email = response.choices[0].message.content.strip()

        # Post improved response to Slack channel
        slack_client.chat_postMessage(channel=channel_id, text=improved_email)

    except Exception as e:
        print("Background error:", e)

# Slack endpoint
@app.route("/slack/events", methods=["POST"])
def handle_slack_event():
    user_input = request.form.get("text", "")
    channel_id = request.form.get("channel_id", "")

    print("Received input:", user_input)
    print("Channel ID:", channel_id)

    # Process in background to prevent Slack timeouts
    threading.Thread(target=process_message, args=(user_input, channel_id)).start()

    return jsonify(response_type="ephemeral", text="Got it! Reframing your message..."), 200

# Optional health check route
@app.route("/", methods=["GET"])
def index():
    return "Slack Email Assistant is running!", 200
