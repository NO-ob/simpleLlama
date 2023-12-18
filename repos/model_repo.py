import sys

from exllamav2.generator.sampler import ExLlamaV2Sampler
sys.path.append("..")

from exllamav2 import (
    ExLlamaV2,
    ExLlamaV2Config,
    ExLlamaV2Cache,
    ExLlamaV2Tokenizer,
)
from exllamav2.generator import (
    ExLlamaV2BaseGenerator,
)

from enum import Enum
from genericpath import exists
import json
import os
import re
import torch


# Used in json if &{key} exists in a value it should be replaced with a value from the main json dict such as userName
mainDictTarget = "&"
# Used in json if @{key} exists in a value it should be replaced with a value from the character json dict such as charName
characterDictTarget = "@"

modelsDirectory = './models'


class ModelType(Enum):
    SAFETENSORS = "safetensors"
    PT = "pt"


class LlamaModel(dict):
    path = str
    modelFile = str
    ModelType = ModelType

    def __init__(self, path: str, modelFile: str):
        dict.__init__(self, path=path, modelFile=modelFile)
        self.path = path
        self.modelFile = modelFile
        self.modelType = ModelType(modelFile[modelFile.rfind(".") + 1:])

    def writelastLoaded(self):
        with open(f"{modelsDirectory}/lastModel.json", "w") as file:
            json.dump({"modelFile": self.modelFile, "path": self.path}, file)


class LlamaModelRepo:
    tokenizer: ExLlamaV2Tokenizer = None
    generator: ExLlamaV2BaseGenerator = None
    config: ExLlamaV2Config = None
    model: ExLlamaV2 = None
    cache: ExLlamaV2Cache = None

    def __init__(self):
        self.models: list = []
        self.modelsDir: str = modelsDirectory
        if os.path.isfile(f"{modelsDirectory}/lastModel.json"):
            with open(f"{modelsDirectory}/lastModel.json", "r") as file:
                lastModel = json.load(file)
                if {"path", "modelFile"} <= lastModel.keys():
                    try:
                        self.loadModel(LlamaModel(
                            path=lastModel["path"], modelFile=lastModel["modelFile"]))
                    except Exception as e:
                        print(str(e))

    def getModelsFromSubDir(self, path: str):
        models: list = []
        for filename in os.listdir(path):
            print(filename)
            if filename[filename.rfind(".") + 1:] in [e.value for e in ModelType]:

                models.append(LlamaModel(path, filename))
                print(path, flush=True)
        return models

    def findModels(self):
        for filename in os.listdir(self.modelsDir):
            path = self.modelsDir + "/" + filename
            if (os.path.isdir(path)):
                self.models.extend(self.getModelsFromSubDir(path))

    def loadModel(self, llamaModel: LlamaModel):
        errors = []

        modelPath = llamaModel.path 
        if (not exists(modelPath)):
            errors.append(f"{modelPath} does not exist")

        if errors:
            raise Exception("\n".join(errors))

        self.config = ExLlamaV2Config()
        self.config.model_dir = modelPath
        self.config.prepare()
        self.model = ExLlamaV2(self.config)
        self.cache = ExLlamaV2Cache(self.model, lazy=True)
        self.model.load_autosplit(self.cache)
        self.tokenizer = ExLlamaV2Tokenizer(self.config)
        self.generator = ExLlamaV2BaseGenerator(
            self.model, self.cache,self.tokenizer)
        llamaModel.writelastLoaded()
        print(f"model loaded {llamaModel.path}")

    def getTokens(self, text: str):
        return self.tokenizer.encode(text=text)

    def chat(self, text: str, params: dict = {}):
        settings = ExLlamaV2Sampler.Settings()
        
        settings.top_p = params.get("top_p", 0.8)
        settings.top_k = params.get("top_k", 50)
        settings.temperature = params.get("temperature", 0.8)
        settings.token_repetition_penalty = params.get(
            "token_repetition_penalty", 1.05)
        settings.token_repetition_range = params.get(
            "token_repetition_range", -1)
        settings.token_repetition_decay = params.get(
            "token_repetition_decay", 0)
        settings.min_p = params.get(
            "min_p", 0.0)
        print(settings.token_repetition_penalty)
     
        self.generator.warmup()
        text = self.generator.generate_simple(
            text, settings, params.get("max_new_tokens", 2000))
        return text

    # Replaces token in a string such as replaceToken{charName} with value in the targetDict

    def replaceTokensInString(self, string: str,  targetDict: dict, replaceToken: str):
        jsonKeys = re.findall(replaceToken + "{([aA-zZ]*)}", string)
        for key in jsonKeys:
            if key in targetDict:
                replacement = "[" + ",".join(targetDict[key]) + "]" if isinstance(
                    targetDict[key], list) else targetDict[key]
                string = string.replace(
                    f"{replaceToken}{{{key}}}", replacement)
            else:
                string = string.replace(f"{replaceToken}{{{key}}}", "")

        jsonKeys = re.findall(replaceToken + "{([aA-zZ]*)}", string)
        if jsonKeys:
            return self.replaceTokensInString(string=string, targetDict=targetDict, replaceToken=replaceToken)
        return string

    # Replaces characters token in a string such as @{charName} with charName in the character map
    def replaceCharacterTokensInString(self, string: str, chatJSON: dict):
        return self.replaceTokensInString(string=string, replaceToken=characterDictTarget, targetDict=chatJSON["character"],)

    # Replaces main token in a string such as &{userName} with userName in the main json blob
    def replaceMainTokensInString(self, string: str, chatJSON: dict):
        return self.replaceTokensInString(string=string, replaceToken=mainDictTarget, targetDict=chatJSON)

    def buildMessage(self, chatJSON: dict, message: dict):

        # Try catch this and thow an exception then return error http response
        messageStr = chatJSON["promptTemplate"].get(message["chatType"], "")
        # Replace tokens from main json blob such as the userName
        messageStr = self.replaceCharacterTokensInString(
            string=messageStr, chatJSON=chatJSON)
        # Replace tokens from character json blob such as the userName
        messageStr = self.replaceMainTokensInString(
            string=messageStr, chatJSON=chatJSON)

        return messageStr.replace("${message}", message["message"])

    def buildMessagesUntilMaxTokenCount(self, messages: list,  chatJSON: dict, currentTokenCount: int = 0,):
        maxTokens = self.config.max_seq_len
        wantedNewTokens = chatJSON["genParams"].get("max_new_tokens", 512)

        messageStrings = []
        while messages:
            messageString = self.buildMessage(
                message=messages.pop(), chatJSON=chatJSON)
            currentTokenCount += len(self.getTokens(messageString)[0])
            if (currentTokenCount <= (maxTokens - wantedNewTokens)):
                print(f"Added Message token count is: {currentTokenCount}")
                messageStrings.append(messageString)
            else:
                print(
                    f"Token count hit breaking count: ${currentTokenCount}, max: ${maxTokens}, wantedTokens: ${wantedNewTokens}")
                break
        return messageStrings

    def buildPrompt(self, chatJSON: dict):
        prompt = self.replaceCharacterTokensInString(
            string=chatJSON["promptTemplate"]["prompt"],  chatJSON=chatJSON)

        tokenCount = len(self.getTokens(prompt)[0])

        print(f"Token after building prompt = {tokenCount}")
        chatExampleStrings = self.buildMessagesUntilMaxTokenCount(messages=chatJSON["character"].get(
            "chatExample", []), chatJSON=chatJSON, currentTokenCount=tokenCount)
        chatExampleStrings.reverse()
        prompt = prompt.replace("${chatExample}", ''.join(chatExampleStrings))

        tokenCount = len(self.getTokens(prompt)[0])

        print(f"Token after building example = {tokenCount}")

        chatHistoryStrings = self.buildMessagesUntilMaxTokenCount(messages=chatJSON.get(
            "chatHistory", []), chatJSON=chatJSON, currentTokenCount=tokenCount)
        chatHistoryStrings.reverse()
        prompt = prompt.replace("${chat}", ''.join(chatHistoryStrings))

        return prompt + chatJSON["character"]["charName"] + ":"
