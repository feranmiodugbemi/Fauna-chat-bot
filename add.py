from faunadb import query as q
from faunadb.objects import Ref
from faunadb.client import FaunaClient
from dotenv import load_dotenv
import os

load_dotenv()
client = FaunaClient(
        secret=os.getenv('FAUNA_SECRET_KEY')
    )
# Create a FaunaDB client
data = {
    "username": "Feranmiodugbemi25",
    "message": {
      "role": "user",
      "content": "Where was it played?"
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
print(result)


