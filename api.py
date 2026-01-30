from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
from typing import Dict, Any

from core.synapse_bot import SynapseBot
from core.logger import logger
from core.skills import delete_skill, upload_skill_zip
from core.config import load_config

app = FastAPI(title="SynapseBot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development convenience
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Agent App instance
agent_app = SynapseBot()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    
class SkillRequest(BaseModel):
    name: str
    description: str
    instructions: str
    
class SkillResponse(BaseModel):
    name: str
    description: str
    path: str

@app.on_event("startup")
async def startup_event():
    logger.info("Starting SynapseBot API...")
    await agent_app.initialize()

@app.get("/health")
async def health_check():
    return {"status": "ok", "agent_initialized": agent_app.agent is not None}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not agent_app.agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        response_content = await agent_app.agent.run(request.message)
        return ChatResponse(response=response_content)
    except Exception as e:
        logger.error(f"Error processing chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint using Server-Sent Events."""
    if not agent_app.agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    from fastapi.responses import StreamingResponse
    
    async def event_generator():
        try:
            async for chunk in agent_app.agent.run_stream(request.message):
                yield chunk
        except Exception as e:
            logger.error(f"Error in stream: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/skills")
async def list_skills():
    return  [
        {
            "name": s.metadata.name,
            "description": s.metadata.description,
            "path": s.path
        } 
        for s in agent_app.skills
    ]

@app.post("/skills/upload")
async def upload_skill(file: UploadFile = File(...)):
    # Determine user skills path from config
    config = load_config()
    user_skills_path = config.storage.user_skills_path
    
    # Validate file type
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are allowed")
    
    try:
        # Save uploaded file temporarily
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        # Extract and validate
        skill_names = upload_skill_zip(user_skills_path, tmp_file_path)
        
        # Clean up temp file
        import os
        os.unlink(tmp_file_path)
        
        # Reload skills
        await agent_app.reload_skills()
        return {"status": "uploaded", "names": skill_names}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error uploading skill: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/skills/{name}")
async def delete_skill_endpoint(name: str):
    config = load_config()
    user_skills_path = config.storage.user_skills_path
    
    deleted = delete_skill(user_skills_path, name)
    if deleted:
        await agent_app.reload_skills()
        return {"status": "deleted"}
    else:
        raise HTTPException(status_code=404, detail="Skill not found")

@app.get("/mcp/tools")
async def list_mcp_tools():
    tools = agent_app.registry.list_tools()
    return [
        {
            "name": t.name,
            "description": t.description,
            "input_schema": t.input_schema,
            "source": t.source
        }
        for t in tools
    ]

@app.get("/config/mcp")
async def get_mcp_config():
    config = load_config()
    path = config.storage.user_mcp_config_path
    if os.path.exists(path):
        with open(path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                 return {"mcpServers": {}}
    return {"mcpServers": {}}

@app.post("/config/mcp")
async def update_mcp_config(request: Dict[str, Any]):
    config = load_config()
    path = config.storage.user_mcp_config_path
    
    # Validate structure strictly?
    if "mcpServers" not in request:
        raise HTTPException(status_code=400, detail="Missing mcpServers key")
        
    try:
        with open(path, "w") as f:
            json.dump(request, f, indent=2)
        return {"status": "updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/reload")
async def reload_mcp():
    try:
        await agent_app.reload_mcp()
        return {"status": "reloaded"}
    except Exception as e:
        logger.error(f"Error reloading MCP: {e}")
        raise HTTPException(status_code=500, detail=str(e))
