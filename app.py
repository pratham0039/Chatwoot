from flask import Flask, request
import requests
import openai

app = Flask(__name__)

# OpenAI API Key
openai.api_key = 'your-openai-api-key'

# Chatwoot API Key
chatwoot_api_key = 'your-chatwoot-api-key'


@app.route('/chatwoot-webhook', methods=['POST'])
def handle_webhook():
    # Get the webhook data from Chatwoot
    data = request.json
    user_message = data['content']  # User's message from Chatwoot
    conversation_id = data['conversation']['id']

    # Call OpenAI API to get a response
    bot_response = get_openai_response(user_message)

    # Send the bot's response back to Chatwoot
    send_message_to_chatwoot(conversation_id, bot_response)

    return {"status": "success"}, 200


def get_openai_response(user_message):
    # Call OpenAI's GPT-3 model for a response
    response = openai.Completion.create(
        engine="text-davinci-003",  # You can use any GPT model you prefer
        prompt=user_message,
        max_tokens=150
    )
    return response.choices[0].text.strip()


def send_message_to_chatwoot(conversation_id, bot_response):
    # Prepare headers for Chatwoot API call
    headers = {
        'Authorization': f'Bearer {chatwoot_api_key}',
        'Content-Type': 'application/json'
    }

    # Prepare the payload
    payload = {
        'content': bot_response,
        'message_type': 'outgoing'  # Send the message as an outgoing message from the bot
    }

    # Send the bot's response back to the user in Chatwoot
    chatwoot_reply_url = f'https://chatwoot-instance.com/api/v1/conversations/{conversation_id}/messages'
    requests.post(chatwoot_reply_url, json=payload, headers=headers)


if __name__ == '__main__':
    app.run(port=5000)
