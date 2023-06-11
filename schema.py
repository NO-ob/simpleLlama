chatSchema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "type": "object",
    "properties": {
        "userName": {
            "type": "string"
        },
        "genParams": {
            "type": "object",
            "properties": {
                "min_length": {
                    "type": "integer"
                },
                "max_length": {
                    "type": "integer"
                },
                "top_p": {
                    "type": "number"
                },
                "min_p": {
                    "type": "number"
                },
                "top_k": {
                    "type": "number"
                },
                "temperature": {
                    "type": "number"
                },
                "token_repetition_penalty_max": {
                    "type": "number"
                },
                "token_repetition_penalty_sustain": {
                    "type": "integer"
                },
                "token_repetition_penalty_decay": {
                    "type": "integer"
                },
                "max_new_tokens": {
                    "type": "integer"
                },
                "beams": {
                    "type": "integer"
                },
                "beam_length": {
                    "type": "integer"
                }
            },
            "required": [
                "max_new_tokens"
            ]
        },
        "character": {
            "type": "object",
            "properties": {
                "charName": {
                    "type": "string"
                },
                "persona": {
                    "type": "string"
                },
                "greeting": {
                    "type": "string"
                },
                "emotions": {
                    "type": "array",
                    "items":
                    {
                        "type": "string"
                    },

                },
                "chatExample": {
                    "type": "array",
                    "items":



                    {
                        "type": "object",
                        "properties": {
                            "chatType": {
                                "type": "string"
                            },
                            "message": {
                                "type": "string"
                            }
                        },
                        "required": [
                            "chatType",
                            "message"
                        ]
                    }

                }
            },
            "required": [
                "charName",
                "persona",
                "greeting",
                "chatExample"
            ]
        },
        "promptTemplate": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string"
                },
                "character": {
                    "type": "string"
                },
                "user": {
                    "type": "string"
                }
            },
            "required": [
                "prompt",
                "character",
                "user"
            ]
        },
        "chatHistory": {
            "type": "array",
            "items": {}
        }
    },
    "required": [
        "userName",
        "genParams",
        "character",
        "promptTemplate",
        "chatHistory"
    ]
}
