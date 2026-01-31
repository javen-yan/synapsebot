from enum import Enum

class AgentStage(Enum):
    PROMPT = "prompt"
    PROCESS = "process"
    RESPONSE = "response"