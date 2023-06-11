
from copy import deepcopy
import json
from flask import Flask, g, request
import torch
from repos.model_repo import LlamaModel, LlamaModelRepo
from flask_expects_json import expects_json
import schema
app = Flask(__name__)

modelRepo = LlamaModelRepo()
llamaModel = None
model = None


emotionsPromptTemplate = {
    "firstUser": "User1",
    "secondUser": "User2",
    "genParams": {
        "max_length": 1000,
        "top_p": 0.7,
        "temperature": 0.44,
        "repetition_penalty": 1.6,
        "max_new_tokens": 5
    },
    "character": {
        "charName": "EmotionEngine",
        "persona": "EmotionEngine will listen to messages between two users and describe the facial expression of the last user using one of these values: @{emotions}. EmotionEngine must always return one of the values from the previous list based on how it thinks the last user is feeling. EmotionEngine is an computer system designed to understand how a user is feeling based on their cummunication with another user. EmotionEngine will always respond with the appropriate expression from the previously mentioned list. If EmotionEngine doesn't know the correct expression it will say 'unkown'\n",
        "emotions": [],
        "chatExample": [
            {
                "chatType": "user1",
                "message": "H-hi My name is Braixen! I'm going to be moving in with you today I-i hope we can get along"
            },
            {
                "chatType": "user2",
                "message": "*I gesture her to come in* Hello welcome your room will be upstairs on the left side"
            },
            {
                "chatType": "user1",
                "message": "N-nice to meet you. Th-thank you for taking me in"
            },
            {
                "chatType": "system",
                "message": "happy"
            },
            {
                "chatType": "user1",
                "message": "*Braixen wags her tail* Okay thankyou. Th-thankyou for everything"
            },
            {
                "chatType": "user2",
                "message": "God youre so hot cutie"
            },
            {
                "chatType": "user1",
                "message": "*braixen turns around and barks at him* Dont call me that!"
            },
            {
                "chatType": "system",
                "message": "angry"
            },
            {
                "chatType": "user1",
                "message": "Okay sorry i will not say it again"
            },
            {
                "chatType": "user2",
                "message": "Great, thankyou!"
            },
            {
                "chatType": "system",
                "message": "normal"
            },
        ]
    },
    "promptTemplate": {
        "prompt": "@{persona} \n @{instructions} \n\n<START> \n ${chatExample}${chat}",
        "system": "@{charName}: ${message} \n",
        "user1": "&{firstUser}: ${message} \n",
        "user2": "&{secondUser}: ${message} \n",

    },
    "chatHistory": []

}


@app.route('/models', methods=['GET'])
def models():
    modelRepo.findModels()
    return {"models": modelRepo.models}


@app.route('/models/load', methods=['POST'])
def load_model():
    json = request.get_json()
    try:
        modelRepo.loadModel(LlamaModel(json['path'], json['modelFile']))
    except Exception as e:
        return str(e), 404
    return "Model loaded", 200


@app.route('/chat', methods=['POST'])
@expects_json(schema.chatSchema)
def chat():
    respjson = g.data

    print("Got chat hist ===============================================")
    print(respjson["chatHistory"])
    print("==================================================================")

    username = respjson["userName"]
    charname = respjson["character"]["charName"]

    prompt = modelRepo.buildPrompt(deepcopy(respjson))
    print("Got Prompt ===============================================")
    print(prompt)
    print("==================================================================")

    chatOutput = modelRepo.chat(prompt, respjson["genParams"])
    chatOutput = chatOutput.replace(prompt, "").split(f"{username}:")[0].replace(
        f"{charname}:", "").replace("<s>", "").replace("</s>", "").replace("<END>", "").lstrip().rstrip()

    print("Got Chat ===============================================")
    print(chatOutput)
    print("==================================================================")

    emotion = None
    responseDict = {"message": chatOutput}

    if respjson["character"]["emotions"]:
        print("Getting emotion for ===============================================")
        print(respjson["character"]["emotions"])
        print("==================================================================")

        emotionsPrompt = deepcopy(emotionsPromptTemplate)
        print("==================================================================")
        print(emotionsPrompt)
        print("==================================================================")

        emotionsPrompt["chatHistory"] = respjson["chatHistory"] if len(
            respjson["chatHistory"]) < 5 else respjson["chatHistory"][-4:]
        isFirst = True
        for message in reversed(emotionsPrompt["chatHistory"]):
            if isFirst:
                message["chatType"] = "user1"
                isFirst = False
            else:
                message["chatType"] = "user2"
                isFirst = True

        emotionsPrompt["chatHistory"].append({
            "chatType": "user2",
            "message": chatOutput
        })

        emotionsPrompt["character"]["emotions"] = respjson["character"]["emotions"]
        emotionPrompt = modelRepo.buildPrompt(emotionsPrompt)

        print("Emotion prompt ===============================================")
        print(emotionPrompt)
        print("==================================================================")

        emotion = modelRepo.chat(emotionPrompt).replace(emotionPrompt, "").replace(
            "<s>", "").replace("</s>", "").replace("<END>", "").lstrip().rstrip()

        if emotion:
            responseDict["emotion"] = emotion

    print("Returning ===============================================")
    print(responseDict)
    print("==================================================================")
    return responseDict


# main driver function
if __name__ == '__main__':
    # run() method of Flask class runs the application
    # on the local development server.
    app.run(debug=True, host="192.168.1.237")
