from enum import Enum
import os
import re
from utils.modelutils import DEV
from transformers import AutoTokenizer
from transformers import LlamaForCausalLM
import torch

from llama_inference import load_quant

#Used in json if &{key} exists in a value it should be replaced with a value from the main json dict such as userName
mainDictTarget = "&"
#Used in json if @{key} exists in a value it should be replaced with a value from the character json dict such as charName
characterDictTarget = "@"

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
    

    def getTokens(self, text:str):
        tokenizer = AutoTokenizer.from_pretrained(self.llamaModel.path, use_fast=False)
        return tokenizer.encode(text, return_tensors="pt").to(DEV)

    def chat(self, text: str, params:dict = {}):
        
        self.loadedModel.to(DEV)
        tokenizer = AutoTokenizer.from_pretrained(self.llamaModel.path, use_fast=False)
        tokenizedPrompt = self.getTokens(text)
        with torch.no_grad():
            generated_ids = self.loadedModel.generate(
                tokenizedPrompt,
                do_sample=True,
                min_length=params.get("min_length",0 ),
                top_p=params.get("top_p",0.7),
                temperature=params.get("temperature", 0.44),
                repetition_penalty=params.get("repetition_penalty", 1.2),
                max_new_tokens=params.get("max_new_tokens",512)
            )
        return tokenizer.decode([el.item() for el in generated_ids[0]])
    

    #Replaces token in a string such as replaceToken{charName} with value in the targetDict
    def replaceTokensInString(self, string: str,  targetDict: dict, replaceToken: str):
        jsonKeys = re.findall(replaceToken + "{([aA-zZ]*)}",string)
        for key in jsonKeys:
            if key in targetDict:
                replacement = "[" + ",".join(targetDict[key]) + "]" if isinstance(targetDict[key], list) else targetDict[key]
                string = string.replace(f"{replaceToken}{{{key}}}", replacement)
            else:
                string = string.replace(f"{replaceToken}{{{key}}}", "") 
        
        jsonKeys = re.findall(replaceToken + "{([aA-zZ]*)}",string)
        if jsonKeys:
            return self.replaceTokensInString(string=string, targetDict=targetDict, replaceToken=replaceToken)
        return string
    
    #Replaces characters token in a string such as @{charName} with charName in the character map
    def replaceCharacterTokensInString(self, string: str, chatJSON: dict):
        return self.replaceTokensInString(string=string, replaceToken=characterDictTarget,targetDict=chatJSON["character"],)
    
    #Replaces main token in a string such as &{userName} with userName in the main json blob
    def replaceMainTokensInString(self, string: str, chatJSON: dict):
        return self.replaceTokensInString(string=string, replaceToken=mainDictTarget,targetDict=chatJSON)


    def buildMessage(self, chatJSON: dict, message: dict):

        #Try catch this and thow an exception then return error http response
        messageStr = chatJSON["promptTemplate"].get(message["chatType"],"")
        #Replace tokens from main json blob such as the userName
        messageStr = self.replaceCharacterTokensInString(string=messageStr, chatJSON=chatJSON)
        #Replace tokens from character json blob such as the userName
        messageStr = self.replaceMainTokensInString(string=messageStr, chatJSON=chatJSON)

        return messageStr.replace("${message}", message["message"])

    def buildMessagesUntilMaxTokenCount(self, messages: list,  chatJSON:dict, currentTokenCount: int = 0,):
        maxTokens = self.loadedModel.config.max_position_embeddings
        wantedNewTokens = chatJSON["genParams"].get("max_new_tokens",512)

        messageStrings = []
        while messages:
            messageString = self.buildMessage(message = messages.pop(), chatJSON=chatJSON)
            currentTokenCount += len(self.getTokens(messageString)[0])
            if (currentTokenCount <= (maxTokens - wantedNewTokens)):
                print(f"Added Message token count is: {currentTokenCount}")
                messageStrings.append(messageString)
            else:
                print(f"Token count hit breaking count: ${currentTokenCount}, max: ${maxTokens}, wantedTokens: ${wantedNewTokens}")
                break
        return messageStrings        


    def buildPrompt(self, chatJSON: dict):
        prompt = self.replaceCharacterTokensInString(string=chatJSON["promptTemplate"]["prompt"],  chatJSON=chatJSON)

        tokenCount = len(self.getTokens(prompt)[0])

        print(f"Token after building prompt = {tokenCount}")
        chatExampleStrings = self.buildMessagesUntilMaxTokenCount(messages=chatJSON["character"].get("chatExample",[]), chatJSON=chatJSON, currentTokenCount=tokenCount)
        chatExampleStrings.reverse()
        prompt = prompt.replace("${chatExample}", ''.join(chatExampleStrings))


        tokenCount = len(self.getTokens(prompt)[0])

        print(f"Token after building example = {tokenCount}")

        chatHistoryStrings = self.buildMessagesUntilMaxTokenCount(messages=chatJSON.get("chatHistory",[]), chatJSON=chatJSON, currentTokenCount=tokenCount)
        chatHistoryStrings.reverse()
        prompt = prompt.replace("${chat}", ''.join(chatHistoryStrings))

        
        return prompt + chatJSON["character"]["charName"] + ":"