import pandas as pd
import ollama
import time
import subprocess
import numpy as np
from multiprocessing import Pool
from tqdm import tqdm

tweets = pd.read_csv('./data/tweets/trumptweets.csv')

def update_progress(*args):
    pbar.update(1)

num_prev_chats = 3
num_permutations_each = 2
model = 'gemma2:2b'

def generate_previous_chats(num_chats):
    chat_titles = []
    chat_values = []
    # Get a good prompt to work with
    model_input = [{
        'role': 'system',
        'content': f"You are a prompt engineer, you want to generate random and useful possible prompts for training a large language model with." 
    },{
        'role': 'user',
        'content': 'Come up with a random topic to talk to a large language model about. Make this topic less than 10 words and only repond the topic with no special characters or extra text.'
    }]
    model_input = model_input
        + [ollama.chat(model=model, messages=model_input)['message']]
        + [{
            'role': 'user',
            'content': 'Now generate a convincing summary of a chat you might have had with a user about this topic. Limit it to 150 words.'
        }]

def generate_prompt(tweet):
    chats = [{
        'role': 'system',
        'content': f"You are a chatbot assistant that keeps a running memory of all conversations you've had. Here is a list of all the converations you've had recently: `{prevChatTitleString}`. Before answering each question you will be asked: 'Do you want to reference a previous chat?' respond to this query with ONLY a number or 'no'. After this you will get the content of that message and confirmation you can now answer the question." 
    }]
    return ollama.chat(model='gemma2:2b', messages=[
        {
            'role': 'user',
            'content': f'You are a prompt engineer trying to fine tune a large language model to be better at generating Donald Trump tweets. Generate a appropriate prompt that would yield a similar result to this Donald Trump tweet: `{tweet}`. Only generate the prompt without any markup, extra text, or title and make sure not to directly quote the tweet.',
        },
    ])['message']['content']


vectorized_generate_prompt = np.vectorize(generate_prompt)

start = time.time()
with Pool(5) as p:
    tweets['query'] = list(tqdm(
        p.imap(vectorized_generate_prompt, tweets['content']), total=tweets.shape[0]))
end = time.time()

print(f'Took: {end - start} seconds')

process.terminate()
print("Killed ollama server")

tweets.to_csv('./data/rdtWithQueries.csv', index=False)
