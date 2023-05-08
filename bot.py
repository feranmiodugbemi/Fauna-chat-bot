import telebot
from faunadb import query as q
from faunadb.objects import Ref
from faunadb.client import FaunaClient
import openai
from dotenv import load_dotenv
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
    system_message = "Assistant: A helpful assistant that provides accurate information."

    # Construct the conversation prompt with user messages and the system message
    conversation_prompt = "\n".join([f"User: {message['content']}\nAssistant:" for message in messages])

    # Prepend the system message to the conversation prompt
    prompt_with_persona = f"{system_message}\n{conversation_prompt}"

    # Generate a response from the model
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt_with_persona,
        max_tokens=50  # Adjust the desired response length
    )

    # Extract the generated reply from the API response
    generated_reply = response.choices[0]["text"]
    
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


def image(image):
    return image


def reset():
    return


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
    bot.reply_to(
        message, "🌿🤖 Hello! Welcome to the fauna and gpt3 powered bot! 🌟💫\nTo begin, type /chat or click on it")


@bot.message_handler(commands=['chat'])
def help_message(message):
    # Set the user's state to 'help' and output a help message
    user_state[message.chat.id] = 'chat'
    bot.reply_to(message, "Hello, how may i help you: ")


@bot.message_handler(commands=['image'])
def help_message(message):
    # Set the user's state to 'help' and output a help message
    user_state[message.chat.id] = 'image'
    bot.reply_to(message, "What kind of image are you creating today: ")


@bot.message_handler(commands=['reset'])
def help_message(message):
    # Set the user's state to 'help' and output a help message
    user_state[message.chat.id] = 'reset'
    bot.reply_to(message, "Resetting chat......... ")


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
        chat_image = message.text
        bot.reply_to(message, chat(chat_image))
        user_state[message.chat.id] = 'image'

    elif message.chat.id in user_state and user_state[message.chat.id] == 'reset':
        chat_reset = message.text
        bot.reply_to(message, reset())
        user_state[message.chat.id] = None


bot.polling()
