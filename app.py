from flask import Flask, request, jsonify
from slack_sdk import WebClient
import openai
import os
import threading
import httpx

# Optional: Clean up proxies
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("OPENAI_PROXY", None)

app = Flask(__name__)

# Slack setup
slack_client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))

# Background task to avoid Slack timeout
def process_message(user_input, channel_id):
    try:
        # Prepare prompt
        prompt = (
            "You are a helpful product support engineer. "
            "Rewrite the following email to be customer-centric and grammatically correct:\n\n"
            f"{user_input}"
        )

        # Create OpenAI client with proxy disabled
        transport = httpx.HTTPTransport(proxy=None)
        ai_client = openai.OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url="https://api.openai.com/v1",
            http_client=httpx.Client(transport=transport)
        )

        # Request GPT-4 response
        response = ai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=300,
            temperature=0.7
        )

        # Extract and send improved email
        improved_email = response.choices[0].message.content.strip()
        slack_client.chat_postMessage(channel=channel_id, text=improved_email)

    except Exception as e:
        print("Background error:", e)

# Slack endpoint to receive slash commands
@app.route("/slack/events", methods=["POST"])
def handle_slack_event():
    user_input = request.form.get("text", "")
    channel_id = request.form.get("channel_id", "")

    print("Received input:", user_input)
    print("Channel ID:", channel_id)

    # Respond quickly and process message in background
    threading.Thread(target=process_message, args=(user_input, channel_id)).start()

    return jsonify(response_type="ephemeral", text="Got it! Reframing your message..."), 200
