from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import uuid
import json
import asyncio
from typing import Dict, Any

from core.synapse_bot import SynapseBot
from core.logger import logger
from core.skills import delete_skill, upload_skill_zip
from core.config import get_config

app = FastAPI(title="SynapseBot API", version="0.1.0")

config = get_config()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development convenience
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Agent App instance
agent_app = SynapseBot()

@app.on_event("startup")
async def startup_event():
    logger.info("Starting SynapseBot API...")
    await agent_app.initialize()
    await agent_app.start()
    
    # Initialize Slack Bot if enabled
    if agent_app.config.channels.slack.enabled:
        from core.channels.slack import SlackBot
        # Pass event_bus
        slack_bot = SlackBot(agent_app.config, agent_app.registry, agent_app.event_bus)
        # Start in background
        asyncio.create_task(slack_bot.start())

    # Initialize Feishu Bot if enabled
    if agent_app.config.channels.feishu.enabled:
        from core.channels.feishu import FeishuBot
        # Pass event_bus
        feishu_bot = FeishuBot(agent_app.config, agent_app.registry, agent_app.event_bus)
        # Start in background
        asyncio.create_task(feishu_bot.start())

    # Initialize Web Bot if enabled
    if agent_app.config.channels.web.enabled:
        from core.channels.web import WebBot
        # Pass event_bus
        web_bot = WebBot(agent_app.config, agent_app.registry, agent_app.event_bus)
        # Start in background
        asyncio.create_task(web_bot.start())
        # Initialize Web Bot Router
        app.include_router(web_bot.router)
        

@app.get("/health")
async def health_check():
    return {"status": "ok", "agent_initialized": agent_app.dispatcher is not None}

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

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a general file for the agent to use."""
    # Generate unique filename to preserve extension but avoid collisions
    ext = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(config.storage.upload_dir, unique_name)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # We return the absolute path so the agent can read it directly
        abs_path = os.path.abspath(file_path)
        return {
            "name": file.filename,
            "path": abs_path,
            "url": f"/files/{unique_name}",
            "size": file_size,
            "type": file.content_type or "application/octet-stream"
        }
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/{filename}")
async def get_file(filename: str):
    """Serve uploaded or generated files."""
    search_dirs = [
        config.storage.upload_dir,
        config.storage.data_path
    ]
    
    target_path = None
    for directory in search_dirs:
        possible_path = os.path.join(directory, filename)
        if os.path.exists(possible_path) and os.path.isfile(possible_path):
            target_path = possible_path
            break
            
    if not target_path:
        raise HTTPException(status_code=404, detail="File not found")
        
    return FileResponse(target_path)

@app.post("/mcp/reload")
async def reload_mcp():
    try:
        await agent_app.reload_mcp()
        return {"status": "reloaded"}
    except Exception as e:
        logger.error(f"Error reloading MCP: {e}")
        raise HTTPException(status_code=500, detail=str(e))

import pty
from fastapi import WebSocket, WebSocketDisconnect
# Reuse WebSocket import but careful about naming collision if we import again
# Just use the top level import

@app.websocket("/ws/shell")
async def websocket_shell(websocket: WebSocket):
    await websocket.accept()
    
    # Create PTY
    master_fd, slave_fd = pty.openpty()
    
    # Spawn shell
    shell = os.environ.get("SHELL", "/bin/bash")
    pid = os.fork()
    
    if pid == 0:
        # Child process
        os.setsid()
        os.dup2(slave_fd, 0)
        os.dup2(slave_fd, 1)
        os.dup2(slave_fd, 2)
        os._exit(os.execv(shell, [shell]))
    
    # Parent process
    os.close(slave_fd)
    
    async def read_from_pty():
        try:
            while True:
                # Read from PTY 
                data = await asyncio.to_thread(os.read, master_fd, 1024)
                if not data:
                    break
                await websocket.send_bytes(data)
        except OSError:
            pass # Process exited
        except Exception as e:
            logger.error(f"Error reading from PTY: {e}")

    try:
        # Start reading task
        read_task = asyncio.create_task(read_from_pty())
        
        while True:
            # Receive from WebSocket
            data = await websocket.receive()
            
            if "text" in data:
                # Resize command? Or just text input?
                msg = data["text"]
                if msg.startswith("RESIZE:"):
                    try:
                        _, rows, cols = msg.split(":")
                        # Set window size
                        winsize = struct.pack("HHHH", int(rows), int(cols), 0, 0)
                        fcntl.ioctl(master_fd, termios.TIOCSWINSZ, winsize)
                    except Exception as e:
                        logger.error(f"Failed to resize PTY: {e}")
                else:
                     os.write(master_fd, msg.encode())
            elif "bytes" in data:
                 os.write(master_fd, data["bytes"])
                 
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket shell error: {e}")
    finally:
        # Cleanup
        try:
            os.kill(pid, signal.SIGTERM)
            os.waitpid(pid, 0)
        except Exception:
            pass
        try:
            os.close(master_fd)
        except Exception:
            pass
        logger.info("Shell session closed")
