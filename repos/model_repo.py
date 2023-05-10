from enum import Enum
import os
import re
from utils.modelutils import DEV
from transformers import AutoTokenizer
from transformers import LlamaForCausalLM
import torch

from llama_inference import load_quant


class ModelType(Enum):
    SAFETENSORS = "safetensors"
    PT = "pt"

class LlamaModel(dict):
    path = str
    modelFile = str
    ModelType = ModelType
    def __init__(self, path : str, modelFile: str):
        dict.__init__(self, path=path,modelFile=modelFile)
        self.path = path
        self.modelFile = modelFile
        self.modelType = ModelType(modelFile[modelFile.rfind(".") +1:])


class LlamaModelRepo:
    llamaModel: LlamaModel = None
    loadedModel: LlamaForCausalLM = None
    def __init__(self):
        self.models: list = []
        self.modelsDir: str = './models'

    def getModelsFromSubDir(self, path: str):
        models: list = []
        for filename in os.listdir(path): 
            if filename[filename.rfind(".") +1:] in [e.value for e in ModelType]:
                models.append(LlamaModel(path,filename))
                print(path, flush=True)
        return models

    def findModels(self):
        for filename in os.listdir(self.modelsDir):
            if(not os.path.isdir(filename)):
                self.models.extend(self.getModelsFromSubDir(self.modelsDir + "/" + filename))

    def loadModel(self, llamaModel: LlamaModel):
        self.llamaModel = llamaModel
        self.loadedModel = load_quant(llamaModel.path, llamaModel.path+"/"+llamaModel.modelFile, 4, 128)
        return 
    
    def chat(self, text: str, params:dict = {}):
        
        self.loadedModel.to(DEV)
        tokenizer = AutoTokenizer.from_pretrained(self.llamaModel.path, use_fast=False)
        input_ids = tokenizer.encode(text, return_tensors="pt").to(DEV)

        with torch.no_grad():
            generated_ids = self.loadedModel.generate(
                input_ids,
                do_sample=True,
                min_length=params.get("min_length",0 ),
                top_p=params.get("top_p",0.7),
                temperature=params.get("temperature", 0.44),
                repetition_penalty=params.get("repetition_penalty", 1.2),
                max_new_tokens=params.get("max_new_tokens",512)
            )
        return tokenizer.decode([el.item() for el in generated_ids[0]])
    
        
    
    def buildPrompt(self, chatHistory: list, character: dict, modelTemplate: dict):
        externalRegex = "@{([aA-zZ]*)}"
        promptRegex = "\${([aA-zZ]*)}"
        prompt = modelTemplate["prompt"]
        externalToken = re.findall(externalRegex,prompt)
        
        chatTokens = re.findall(promptRegex,prompt)
        #Make token replacement recursive or something or do it all at the end after building the string
        for token in chatTokens:
            if token == "chat":
                compiledChatHistory = ""
                for message in chatHistory:
                    messageStr = ""
                    if message["chatType"] == "user":
                        messageStr = modelTemplate["userChatFormat"]
                        messageStr = messageStr.replace("@{userMessage}", message["message"])
                        messageStr = messageStr.replace("^{chatTokenUser}", modelTemplate["chatTokenUser"])
                    elif message["chatType"] == "character":
                        messageStr = modelTemplate["characterChatFormat"]
                        messageStr = messageStr.replace("@{characterMessage}", message["message"])
                        messageStr = messageStr.replace("^{chatTokenCharacter}", modelTemplate["chatTokenCharacter"])
                        
                    compiledChatHistory += messageStr
                prompt = prompt.replace(f"${{chat}}", compiledChatHistory)

        for token in externalToken:
            if token in character:
                prompt = prompt.replace(f"@{{{token}}}", character[token])
            else:
                prompt = prompt.replace(f"@{{{token}}}", "")        

        return(prompt)