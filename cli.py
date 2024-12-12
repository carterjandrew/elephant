import click
import requests
import sys
import os

# Replace with the base URL for Ollama if needed
OLLAMA_BASE_URL = "http://localhost:11434/api/chat"

session = requests.Session()

os.makedirs('chats', exist_ok=True)

chatTitles = []
if os.path.exists('chat-titles.txt'):
    with open('chat-titles.txt', 'r') as file:
        chatTitles = [line.strip() for line in file]

def send_request(chats, query, model_name):
    response = session.post(
        OLLAMA_BASE_URL,
        json={
            "model": model_name,
            'stream': False,
            "messages": chats + [query],
        }
    )
    if response.status_code == 200:
        bot_response = response.json().get("message", "No response from model")
        return chats + [query] + [bot_response]
    else:
        print(f"Error: {response.status_code} - {response.text}")

@click.command()
@click.argument('model_name')
def run_model(model_name):
    """
    CLI to interact with an Ollama model.
    Example:
        python cli.py modelname
    """
    click.echo(f"Running model: {model_name}")

    prevChatTitleString = result = "\n".join([f"{index}: {item}" for index, item in enumerate(chatTitles)])

    chats = [{
        'role': 'system',
        'content': f"You are a chatbot assistant that keeps a running memory of all conversations you've had. Here is a list of all the converations you've had recently: `{prevChatTitleString}`. Before answering each question you will be asked: 'Do you want to reference a previous chat?' respond to this query with ONLY a number or 'no'. After this you will get the content of that message and confirmation you can now answer the question." 
    }]
    print(chats[0])
    
    # Keep the CLI running until the user decides to exit
    while True:
        try:
            # Get user input
            user_input = input("You: ")
            print('\n')
            # Print a space character

            # Ask the model if it want's context
            chats = send_request(chats, {
                'role': 'user',
                'content': "The question is: `" + user_input + "` Do you want to reference a previous chat? Remember respond with only a number or 'no'."
            }, model_name)
            # Get our last chat so we can try to pull context
            context = chats[-1]
            print(f"Context: {context['content']}")
            try:
                num = int(context['content'])
                filePath = f"chats/{chatTitles[num]}.txt"
                with open(filePath, 'r') as file:
                    print(file.read())
                break
            except:
                chats = send_request(chats, {
                    'role': 'user',
                    'content': f"You did not ask for a previous chat or we could not parse your request. Do your best to respond to the following user prompt: {user_input}"
                }, model_name)
            print(f"{model_name}: {chats[-1]['content']}")
        
        #Exit application
        except KeyboardInterrupt:
            click.echo("Exiting the CLI. Plese wait while a chat summary is generated")
            title = send_request(chats, {
                'role': 'user',
                'content': 'If you had to describe the conversation we have had in 10 words or less, what would it be? Please only return this response.'
            }, model_name)[-1]['content'].strip('.\n')
            summary = send_request(chats, {
                'role': 'user',
                'content': 'Create a summary of the important things you have learned from this conversation so if you had to reference this conversation in the future you could.'
            }, model_name)[-1]['content']
            with open('chat-titles.txt', 'w') as file:
                file.write(f"{title}\n")
            with open(f'chats/{title}.txt', 'w') as file:
                file.write(summary)
            sys.exit(0)
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    run_model()

