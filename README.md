# simpleLlama
A Simple webserver for generating text with GPTQ-For-Llama, no bloat no bullshit



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

