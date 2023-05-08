import openai
from faunadb import query as q
from faunadb.client import FaunaClient
from dotenv import load_dotenv
import os

load_dotenv()

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



