# simpleLlama
A Simple webserver for generating text with GPTQ-For-Llama, no bloat no bullshit

To get it setup download https://github.com/turboderp/exllama, follow the setup steps.

Drop the files from this repo into the exllama directory.

Add a model to the models directory

install flask and flask_expects_json with pip. 

run the server.py file


I created a discord bot as an example project for the server, When mentioned it will respond. if you want to continue a conversation you must reply to the messages instead of just mentioning. If you have restarted the server and a reply chain has been going a while it will take a long time to build the reply chain the first time as message retreival is fairly slow. they are cached in memory once fetched so it will get faster for subsequent messages  https://gist.github.com/NO-ob/3ca286a68659a0fcf7aca829e2605f00

## Endpoint /models - GET

This will return a list of models in the model directory


Response
```
{
    "models": [
        {
            "modelFile": "vicuna-13B-1.1-GPTQ-4bit-128g.latest.safetensors",
            "path": "./models/vicuna-13B-1.1-GPTQ-4bit-128g"
        },
        {
            "modelFile": "vicuna-13B-1.1-GPTQ-4bit-128g.compat.no-act-order.pt",
            "path": "./models/vicuna-13B-1.1-GPTQ-4bit-128g"
        },
        {
            "modelFile": "pyg7b-4bit-128g.safetensors",
            "path": "./models/pygmalion-7b-4bit-128g-cuda"
        },
    ]
}
```

## Endpoint /models/load - POST

Post JSON to this url to load a model 
```
{
  "modelFile": "pyg7b-4bit-128g.safetensors",
  "path": "./models/pygmalion-7b-4bit-128g-cuda"
}
```


## Endpoint /chat - POST

Post JSON to this endpoint to generate text, a model must already be loaded theres currently no error handling. A trimmed output will be returned which should only be the last message in the prompt. An example json file is in the prompts directory. If the posted json has a list of emotions in the character prompt those will be used on a second text gen with a built in prompt to generate and emotion based on the last few messages in the chat.

The chat endpoint can take your full list of messages in the chat history field the message chain is built by adding the messages from the characters chatExample and the chatHsitory messages. The amount of messages added depends on the token limitof the model it will add them until the token count is the (models max tokens - max_new_tokens) from the genParams

Response 
```
{
    "emotion": "happy",
    "message": "I'm doing great, thanks for asking! Just excited to share my love of Pokémon with everyone. How about you?"
}
```

