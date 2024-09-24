from flask import Flask, request
import requests
import openai
from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool
from dotenv import load_dotenv
from pathlib import Path
import os
import json
from flask import Flask, request, render_template, jsonify, send_file

app = Flask(__name__)

load_dotenv()


# Set up the environment keys
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["SERPER_API_KEY"] = os.getenv("SERPER_API_KEY")




# Company-specific details
COMPANY_NAME = "Lxme"
COMPANY_DOMAIN = "lxme.in"
COMPANY_ROLE = f'{COMPANY_NAME} Information Specialist'
COMPANY_GOAL = f'Provide accurate and detailed information about {COMPANY_NAME} products, services, and solutions available on lxme.in.'
COMPANY_BACKSTORY = (
    f'You are a knowledgeable specialist in {COMPANY_NAME}\'s offerings. '
    f'You provide detailed information about their products, services, '
    f'and solutions available on lxme.in, including any innovations and key features.'
)

# Initialize the SerperDevTool with company-specific search settings
class CompanySerperDevTool(SerperDevTool):
    def search(self, query):
        # Search the company website
        company_query = f"site:{COMPANY_DOMAIN} {query}"
        results = super().search(company_query)
        relevant_results = [result for result in results if COMPANY_DOMAIN in result.get('link', '')]
        return results

search_tool = CompanySerperDevTool()

# Agent setups
company_info_agent = Agent(
    role=COMPANY_ROLE,
    goal=COMPANY_GOAL,
    verbose=True,
    memory=True,
    backstory=COMPANY_BACKSTORY,
    tools=[search_tool]
)

out_of_context_agent = Agent(
    role='Context Checker',
    goal=f'Determine if a question is relevant to {COMPANY_NAME} and politely decline if not.',
    verbose=True,
    memory=True,
    backstory=(
        f'You are responsible for determining if a question is relevant to {COMPANY_NAME}. '
        f'If the question is not related, you respond politely indicating that the question is out of context and '
        f'that only {COMPANY_NAME}-related information is provided.'
    )
)

# Centralized Task
centralized_task = Task(
    description=(
        f'Determine if the {{user_query}} is related to {COMPANY_NAME} and respond appropriately. '
        f'If the query is about {COMPANY_NAME}, provide a detailed and informative response. '
        f'Respond in JSON format with two keys: "answer" and "questions". '
        f'The "answer" key should contain the response, and the "questions" key should be an array of three follow-up questions '
        f'that are relevant to {COMPANY_NAME}.'
        f'Ensure the response is in valid JSON format.'
    ),
    expected_output='A JSON object containing "answer", and "questions" without any unescaped newline characters and without any codeblock.',
    agent=Agent(
        role=f'{COMPANY_NAME} Information Bot',
        goal=f'Provide comprehensive information about {COMPANY_NAME} and its offerings.',
        verbose=True,
        memory=True,
        backstory=(
            f'You are an intelligent bot specializing in {COMPANY_NAME} information. You provide detailed responses '
            f'about {COMPANY_NAME}\'s products, services, and innovations.'
        ),
        tools=[search_tool],
        allow_delegation=True
    )
)

# Centralized Crew setup
centralized_crew = Crew(
    agents=[company_info_agent, out_of_context_agent],
    tasks=[centralized_task],
    process=Process.sequential
)

# Helper function to check links
def check_links(links, user_query):
    web_links = []
    youtube_links = []
    for link in links:
        if COMPANY_DOMAIN in link:
            web_links.append(link)
        if "youtube.com" in link and "watch" in link:
            youtube_links.append(link)
    return web_links, youtube_links



# Chatwoot API Key
chatwoot_api_key = 'fw2s9VCfe7Rik8d84wsP2YDo'
chatwoot_url = "https://app.chatwoot.com"
chatwoot_bot_token = "fw2s9VCfe7Rik8d84wsP2YDo"

@app.route('/chatwoot-webhook', methods=['POST'])
def handle_webhook():
    # Get the webhook data from Chatwoot
    data = request.json
 
    user_message = data['content']  # User's message from Chatwoot
    conversation_id = data['conversation']['id']
    contact = data['sender']['id']
    account = data['account']['id']
    message_type = data['message_type']
    print(account)
    print('ptatham')
    team_name = ""
    try:
        team_exists = 'team' in data['conversation']['meta'] 
        print(f'team: {team_exists}')
        team_name = data['conversation']['meta']['team']['name'] if team_exists else 'No team assigned'
        print(team_name)
    except:
        
        team_name = 'No team assigned'

    # Instead of calling OpenAI, return a fixed response
    result = centralized_crew.kickoff(inputs={'user_query': user_message})
    chatwoot_msg = 'None'
    bot_response = "Error"
    try:
            # Parse the JSON response
            cleaned_result = str(json.loads(result.model_dump_json())['raw']).strip().replace('```json', '').replace('```', '')
            parsed_result = json.loads(cleaned_result)
            answer = parsed_result.get("answer", "")
            links = parsed_result.get("links", "")
            web_links, youtube_links = check_links(links, user_message)

            if web_links or youtube_links:
                answer += "\n\nFor your reference:\n"
                if youtube_links:
                    answer += "\nYouTube references:\n" + "\n".join(youtube_links)
                if web_links:
                    answer += "\nWeb references:\n" + "\n".join(web_links)

            questions = parsed_result.get("questions", [])
            

            
            print("Answer:", answer)  # Debugging print
            print("Questions:", questions)  # Debugging print
            bot_response = answer
            

    except json.JSONDecodeError as e:
            print("JSON Decode Error:", e)  # Debugging print
            return chatwoot_msg

    except Exception as e:
            print("An unexpected error occurred:", e)  # Debugging print
            return chatwoot_msg

    
    # Send the fixed bot response back to Chatwoot
    if message_type == 'incoming':
        if team_name != "sales":
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
