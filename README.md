# BetterAnk

The idea for this app arose from my need to create and edit flashcards easier with the help of current LLM technologies for learning japanese. 
The core of the app will be very similar to [Anki](https://apps.ankiweb.net/) but much simpler and specifically tailored to learning japanese. 
The vision is to be able to use it just like anki, with the addition of allowing upload of images of online lessons which then with tool calling
from llms get turned into flashcards for the relevant concepts. 

## Usage

### backend
first cd into backend/app and then run: 
```bash
python -r requirements.txt
```

then run
```bash
docker compose up
```
to start the local postgres database.
then start the FastAPI backend with 
```bash
python main.py 
```
Then you can create and get users, decks, flashcards, reviews via the api    
The review system is based on the sm2 implementation of [alankan886/SuperMemo2](https://github.com/alankan886/SuperMemo2)
### frontend
I want to try to use vanilla js for the frontend to actually learn some web concepts deeply. 
This frontend ofc will call the FastAPI backend endpoints.
I will serve the backend and static frontend file from the same FastAPI backend. 
#### See you Space Cowboy ...
![spiku](https://github.com/user-attachments/assets/9089303e-fff8-43d7-ad22-2b01a56509a0)
