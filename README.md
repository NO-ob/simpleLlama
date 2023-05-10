# simpleLlama
A Simple webserver for generating text with GPTQ-For-Llama, no bloat no bullshit

To get it setup download https://github.com/qwopqwop200/GPTQ-for-LLaMa, follow the setup steps.

Drop the files from this repo into the GPTQ-For-Llama directory.

Add a model to the models directory

install flask with pip. 

run the server.py file


You can make a discord bot to use as a frontend quite easily I have added the functionality to my bot here https://gist.github.com/NO-ob/498e86889a4945b508dce86f5b451b5e 

At lines 207-211 it checks if its been mentioned, if the bot has been mentioned it will build a reply chain of messages and add them to the prompt template. it will then send those to the server and post the response as a reply to the discord message

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

Post JSON to this endpoint to generate text, a model must already be loaded theres currently not error handling. A trimmed output will be returned which should only be the last message in the prompt. An example json file is in the prompts directory

Response 
```
{
    "message": "Ok well firstly I am an expert trainer who specializes in training Pokémon. I train Pokémon everyday and make sure they stay healthy and happy. I also take part in many competitions such as battles and shows. I try to win each time and become number one!"
}
```

