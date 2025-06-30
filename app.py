from flask import Flask, request
from slack_sdk import WebClient
import openai
import os

app = Flask(__name__)

client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
openai.api_key = os.environ["OPENAI_API_KEY"]

@app.route("/slack/events", methods=["POST"])
def handle_slack_event():
    user_input = request.form.get("text", "")
    channel_id = request.form.get("channel_id", "")

    prompt = (
        "You are a helpful product support engineer. "
        "Rewrite the following email to be customer-centric and grammatically correct:\n\n"
        f"{user_input}"
    )

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}],
        max_tokens=300,
        temperature=0.7
    )

    improved_email = response.choices[0].message.content.strip()

    client.chat_postMessage(channel=channel_id, text=improved_email)
    return "", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
