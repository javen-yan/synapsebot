import os
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("filesystem", log_level="WARNING")

@mcp.tool()
def read_file(path: str) -> str:
    """Read specific file content."""
    try:
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        
        if not os.path.exists(path):
            return f"Error: File not found: {path}"
            
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file {path}: {str(e)}"

@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Write content to a file. Overwrites existing content."""
    try:
        if not os.path.isabs(path):
            path = os.path.abspath(path)
            
        # Ensure directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
            
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file {path}: {str(e)}"

@mcp.tool()
def list_directory(path: str = ".") -> str:
    """List files and directories in the specified path."""
    try:
        if not os.path.isabs(path):
            path = os.path.abspath(path)
            
        if not os.path.exists(path):
            return f"Error: Path not found: {path}"
            
        items = os.listdir(path)
        output = []
        for item in items:
            item_path = os.path.join(path, item)
            type_str = "DIR" if os.path.isdir(item_path) else "FILE"
            output.append(f"[{type_str}] {item}")
        return "\n".join(output)
    except Exception as e:
        return f"Error listing directory {path}: {str(e)}"

if __name__ == "__main__":
    mcp.run()
