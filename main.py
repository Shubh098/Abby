from urllib import response
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from huggingface_hub import InferenceClient
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
import redis
# Request Body Model
class Message(BaseModel):
    message: str


app = FastAPI()

# Redis client configuration
redis_client = redis.StrictRedis(host="localhost", port=6379, db=0, decode_responses=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins or specify your frontend's URL
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/chat", response_class=HTMLResponse)
async def serve_chat():
    return FileResponse("chat.html")

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Chat API! Visit /chat to access the chat UI."}


client = InferenceClient(
    "meta-llama/Meta-Llama-3-8B-Instruct",
    token="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",
)

@app.post("/send_message")
async def chat(message: Message):
    try:
        # Call the OpenAI API (or any LLM service you want)
        # data = await request.json()
        # user_message = data.get("message")
        user_message = message.message 
        redis_key = f"chat:{user_message}"
        cached_response = redis_client.get(redis_key)
        
        if cached_response:
            print("Fetching from Redis cache")
            return {"reply": cached_response}
        
        # print(user_message)
        full_reply = ""
        for message in client.chat_completion(
            messages=[
                {"role": "user", "content":user_message},
            ],
            max_tokens=500,  
            stream=True,
        ):   
            print(message.choices[0].delta.content, end="")  
            full_reply += message.choices[0].delta.content
            print("hey")  
        # Extract the LLM's response
        
        redis_client.set(redis_key, full_reply, ex=3600)
        print("hey--------------------------------------")
        print(full_reply)
        return {"reply": full_reply}
        if response.status_code == 200:
            reply = response.json()["choices"][0]["message"]["content"]
            return {"reply": reply}
        else:
            raise HTTPException(status_code=500, detail="Failed to fetch from LLM")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

