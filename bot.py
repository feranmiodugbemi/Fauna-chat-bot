import telebot
from faunadb import query as q
from faunadb.objects import Ref
from faunadb.client import FaunaClient
import openai
from dotenv import load_dotenv
import json
import os
load_dotenv()
bot = telebot.TeleBot(os.getenv("BOT_SECRET"))

def prompt(username, question):
    # Create a FaunaDB client
    client = FaunaClient(secret=os.getenv('FAUNA_SECRET_KEY'))
    data = {
        "username": username,
        "message": {
            "role": "user",
            "content": question
        }
    }
    result = client.query(
        q.create(
            q.collection("Messages"),
            {
            "data": data
            }
        )
    )
    index_name = "users_messages_by_username"
    username = username
    # Paginate over all the documents in the collection using the index
    result = client.query(
        q.map_(
            lambda ref: q.get(ref),
            q.paginate(q.match(q.index(index_name), username))
        )
    )

    messages = []

    for document in result['data']:
        message = document['data']['message']
        messages.append(message)

    # Set up OpenAI API
    openai.api_key = os.getenv('OPENAI_SECRET_KEY')

    # Define the assistant's persona in a system message
    system_message = {"role":"system", "content" : "A helpful assistant that provides accurate information."}

    # Construct the conversation prompt with user messages and the system message
    prompt_with_persona = [system_message] + [
        {"role": "user", "content": message["content"]} if message["role"] == "user"
        else {"role": "assistant", "content": message["content"]} for message in messages
    ]

    # Generate a response from the model
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=prompt_with_persona
    )

    # Extract the generated reply from the API response
    generated_reply = response["choices"][0]["message"]["content"]
    
    newdata = {
        "username": username,
        "message": {
            "role": "assistant",
            "content": generated_reply
        }
    }
    result = client.query(
        q.create(
            q.collection("Messages"),
            {
            "data": newdata
            }
        )
    )

    return generated_reply



def chat(question, user):
    client = FaunaClient(
        secret=os.getenv('FAUNA_SECRET_KEY')
    )
    global chat_list
    userid = user.from_user.id
    username = user.from_user.username
    user_exists = client.query(
        q.exists(q.match(q.index("users_by_id"), userid)))
    if user_exists:
        reply = prompt(username, question)
        return reply
    else:
        return "🌿🤖 Hello! Welcome to the fauna and gpt3 powered bot! 🌟💫\nThis user is not logged in , type /start or click on it to login"


def image(prompt, user):
    client = FaunaClient(
        secret=os.getenv('FAUNA_SECRET_KEY')
    )
    userid = user.from_user.id
    openai.api_key = os.getenv('OPENAI_SECRET_KEY')
    user_exists = client.query(
        q.exists(q.match(q.index("users_by_id"), userid)))
    if user_exists:
        generated_image = openai.Image.create(
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        image_url = generated_image['data'][0]['url']
        return image_url
    else:
        return "🌿🤖 Hello! Welcome to the fauna and gpt3 powered bot! 🌟💫\nThis user is not logged in , type /start or click on it to login"





print("Started.........")


user_state = {}


@bot.message_handler(commands=['start'])
def start_message(message):
    client = FaunaClient(
        secret=os.getenv('FAUNA_SECRET_KEY')
    )
    user_id = message.from_user.id
    username = message.from_user.username
    user_exists = client.query(
        q.exists(q.match(q.index("users_by_id"), user_id)))
    if not user_exists:
        client.query(
            q.create(
                q.collection("Users"),
                {
                    "data": {
                        "user_id": user_id,
                        "username": username
                    }
                }
            )
        )
    bot.reply_to(message, "🌿🤖 Hello! Welcome to the fauna and gpt3 powered bot! 🌟💫\nTo begin, type /chat or click on it")


@bot.message_handler(commands=['chat'])
def chat_message(message):
    # Set the user's state to 'help' and output a help message
    user_state[message.chat.id] = 'chat'
    bot.reply_to(message, "Hello, how may i help you: ")
    
    
    


@bot.message_handler(commands=['image'])
def image_message(message):
    # Set the user's state to 'help' and output a help message
    user_state[message.chat.id] = 'image'
    bot.reply_to(message, "What kind of image are you creating today: ")





@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if message.chat.id in user_state and user_state[message.chat.id] == 'chat':
        chat_message = message.text
        user = message
        bot.reply_to(message, chat(chat_message, user))

    elif message.chat.id in user_state and user_state[message.chat.id] == 'start':
        user = message
        bot.reply_to(message, user)
        user_state[message.chat.id] = None

    elif message.chat.id in user_state and user_state[message.chat.id] == 'image':
        image_prompt = message.text
        user = message
        bot.reply_to(message, image(image_prompt, user))
        user_state[message.chat.id] = 'image'
        bot.send_message(message.chat.id, "What Image are you creating again?")

    



bot.polling()
