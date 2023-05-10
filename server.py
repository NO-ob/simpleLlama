
import json
from flask import Flask, request
from repos.model_repo import LlamaModel, LlamaModelRepo

 
app = Flask(__name__)

modelRepo = LlamaModelRepo()
llamaModel = None
model = None


@app.route('/models', methods=['GET'])
def models():
    modelRepo.findModels()
    return {"models": modelRepo.models}

@app.route('/models/load', methods=['POST'])
def load_model():
    json = request.get_json()
    modelRepo.loadModel(LlamaModel(json['path'],json['modelFile']))
    return {'':''}

@app.route('/chat', methods=['POST'])
def chat():
    json = request.get_json()
    

    #Add validation for request json, character, prompt etc
    
    prompt = modelRepo.buildPrompt(chatHistory=json["chat_history"],character=json["character"], modelTemplate=json["prompt_template"])
    resp = modelRepo.chat(prompt,json["gen_params"])
    username = json["userName"]
    charname = json["charName"]
    return {"message" : resp.replace(prompt,"").split(f"{username}:")[0].replace(f"{charname}:","").replace("<s>","").replace(r"</s>","").replace("<END>","").lstrip().rstrip()}

@app.route('/buildPrompt', methods=['get'])
def build_prompt():
    chatHistory = None
    character = None
    modelTemplate = None

    with open('prompts/chatHist.json') as json_file:
        print("opening chathist")
        chatHistory = json.load(json_file)

    with open('prompts/pygmalion.json') as json_file:
        print("opening pygmalion")
        modelTemplate = json.load(json_file) 

    with open('prompts/dawn.json') as json_file:
        print("opening dawn")
        character = json.load(json_file)    
       
    
    modelRepo.buildPrompt(chatHistory=chatHistory, modelTemplate=modelTemplate, character=character)

    return {"prompt": modelRepo.buildChatString(chatHistory=chatHistory, modelTemplate=modelTemplate, character=character)}
    
# main driver function
if __name__ == '__main__':
 
    # run() method of Flask class runs the application
    # on the local development server.
    app.run(debug=True)
