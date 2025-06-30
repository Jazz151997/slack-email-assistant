from flask import Flask, request, jsonify
from slack_sdk import WebClient
import openai
import os
import threading

# Optional: Clean up proxies
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("OPENAI_PROXY", None)

app = Flask(__name__)

# Slack & OpenAI setup
client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))
openai.api_key = os.environ.get("OPENAI_API_KEY")
openai.base_url = "https://api.openai.com/v1"

# Background task to avoid Slack timeout
def process_message(user_input, channel_id):
    try:
        prompt = (
            "You are a helpful product support engineer. "
            "Rewrite the following email to be customer-centric and grammatically correct:\n\n"
            f"{user_input}"
        )

        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=300,
            temperature=0.7
        )

        improved_email = response.choices[0].message.content.strip()
        client.chat_postMessage(channel=channel_id, text=improved_email)

    except Exception as e:
        print("Background error:", e)

# Slack event endpoint
@app.route("/slack/events", methods=["POST"])
def handle_slack_event():
    user_input = request.form.get("text", "")
    channel_id = request.form.get("channel_id", "")

    print("Received input:", user_input)
    print("Channel ID:", channel_id)

    # Start OpenAI & Slack logic in background thread
    threading.Thread(target=process_message, args=(user_input, channel_id)).start()

    # Respond within 3s to avoid Slack timeout
    return jsonify(response_type="ephemeral", text="Got it! Reframing your message..."), 200
