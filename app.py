from flask import Flask, request
import requests
import openai

app = Flask(__name__)

# OpenAI API Key
openai.api_key = 'your-openai-api-key'

# Chatwoot API Key
chatwoot_api_key = 'CHHUUQQ4smRuYm6BvQuAnDt1'
chatwoot_url = "https://app.chatwoot.com"
chatwoot_bot_token = "CHHUUQQ4smRuYm6BvQuAnDt1"

@app.route('/chatwoot-webhook', methods=['POST'])
def handle_webhook():
    # Get the webhook data from Chatwoot
    data = request.json
    print(data)
    user_message = data['content']  # User's message from Chatwoot
    conversation_id = data['conversation']['id']
    contact = data['sender']['id']
    account = data['account']['id']
    message_type = data['message_type']
    print(account)
    print('ptatham')

    # Instead of calling OpenAI, return a fixed response
    bot_response = "Lxme trading is a trading platfrom which have multiple things for a women. They can use it any way they want to."
    chatwoot_msg = 'None'
    # Send the fixed bot response back to Chatwoot
    if message_type == 'incoming':
        if user_message == "talk":
            print('talk')
            chatwoot_msg = send_message_to_team(account, conversation_id, bot_response)
        else:
            chatwoot_msg = send_message_to_chatwoot(account, conversation_id, bot_response)

    return chatwoot_msg



def get_openai_response(user_message):
    # Call OpenAI's GPT-3 model for a response
    response = openai.Completion.create(
        engine="text-davinci-003",  # You can use any GPT model you prefer
        prompt=user_message,
        max_tokens=150
    )
    return response.choices[0].text.strip()

def send_message_to_team(account, conversation, bot_response):
    data = {
        'team_id': 6075
    }

    print(data)
    print('it came here')
    url = f"{chatwoot_url}/api/v1/accounts/{account}/conversations/{conversation}/assignments"
    headers = {"Content-Type": "application/json",
               "Accept": "application/json",
               "api_access_token": f"{chatwoot_bot_token}"}

    r = requests.post(url,
                      json=data, headers=headers)
        
    

    # Check for response errors
    if response.status_code != 200:
        print(f"Error sending message to Chatwoot: {response.status_code}, {response.text}")
    else:
        print("Message sent to Chatwoot successfully")
    return r.json()

def send_message_to_chatwoot(account, conversation, bot_response):
    data = {
        'content': bot_response
    }

    print(data)
    print('it came here')
    url = f"{chatwoot_url}/api/v1/accounts/{account}/conversations/{conversation}/messages"
    headers = {"Content-Type": "application/json",
               "Accept": "application/json",
               "api_access_token": f"{chatwoot_bot_token}"}

    r = requests.post(url,
                      json=data, headers=headers)
        
    

    # Check for response errors
    if r.status_code != 200:
        print(f"Error sending message to Chatwoot: {response.status_code}, {response.text}")
    else:
        print("Message sent to Chatwoot successfully")
    return r.json()


if __name__ == '__main__':
    app.run(port=5000)
