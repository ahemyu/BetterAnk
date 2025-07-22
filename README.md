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

then start the postgres server locally (will be moved to cloud soon inshallah)

then start the FastAPI backend with python main.py 
Then you can create and get flashcards via the api    

#### See you Space Cowboy ...
![spiku](https://github.com/user-attachments/assets/9089303e-fff8-43d7-ad22-2b01a56509a0)
