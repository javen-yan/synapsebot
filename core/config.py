import os
import yaml
from pathlib import Path
from pydantic import BaseModel, Field

class LLMConfig(BaseModel):
    base_url: str
    api_key: str
    model: str

class StorageConfig(BaseModel):
    data_path: str = "./data"
    
    @property
    def system_skills_path(self) -> str:
        return os.path.join(self.data_path, "system", "skills")
    
    @property
    def system_mcp_config_path(self) -> str:
        return os.path.join(self.data_path, "system", "mcp_config.json")
    
    @property
    def user_skills_path(self) -> str:
        return os.path.join(self.data_path, "user", "skills")
    
    @property
    def user_mcp_config_path(self) -> str:
        return os.path.join(self.data_path, "user", "mcp_config.json")

    def ensure_structure(self):
        """Ensure all required directories and files exist."""
        # Create directories
        for path in [self.system_skills_path, self.user_skills_path]:
            os.makedirs(path, exist_ok=True)
            
        # Create MCP config files if they don't exist
        default_mcp_config = '{"mcpServers": {}}'
        
        for path in [self.system_mcp_config_path, self.user_mcp_config_path]:
            # Ensure parent dir exists
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            if not os.path.exists(path):
                with open(path, "w") as f:
                    f.write(default_mcp_config)
    

class Config(BaseModel):
    llm: LLMConfig
    storage: StorageConfig
    log_level: str = "INFO"

def load_config(config_path: str = "config.yaml") -> Config:
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)
    
    # Expand env vars in API Key
    api_key = raw_config.get("llm", {}).get("api_key", "")
    if api_key.startswith("${") and api_key.endswith("}"):
        env_var = api_key[2:-1]
        raw_config["llm"]["api_key"] = os.getenv(env_var, "")
        
    config = Config(**raw_config)
    config.storage.ensure_structure()
    
    return config
