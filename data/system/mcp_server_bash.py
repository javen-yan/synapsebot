import asyncio
import subprocess
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("bash", log_level="WARNING")

@mcp.tool()
def bash(command: str) -> str:
    """Execute a bash command. Use this for running scripts, listing directories, etc."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60 # 1 minute timeout
        )
        output = result.stdout
        if result.stderr:
            output += f"\nStderr: {result.stderr}"
        return output
    except subprocess.TimeoutExpired:
        return "Error: Command timed out."
    except Exception as e:
        return f"Error executing command: {str(e)}"

if __name__ == "__main__":
    mcp.run()
