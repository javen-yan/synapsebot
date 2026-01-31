import sys
import argparse
import asyncio
import logging

try:
    import uvicorn
except ImportError:
    uvicorn = None

from core.logger import logger

def start_server(host: str, port: int, reload: bool):
    """Starts the FastAPI server."""
    if not uvicorn:
        logger.error("[red]Error:[/red] uvicorn is not installed.")
        sys.exit(1)
        
    logger.info(f"Starting Server at http://{host}:{port}")
    uvicorn.run("server.main:app", host=host, port=port, reload=reload)

def start_cli_session():
    """Starts the interactive CLI."""
    try:
        from cli.main import start_cli
        asyncio.run(start_cli())
    except ImportError as e:
        logger.error(f"[red]Error importing CLI:[/red] {e}")
    except KeyboardInterrupt:
        pass

def main():
    parser = argparse.ArgumentParser(description="SynapseBot - AI Agent System")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # helper for server
    server_parser = subparsers.add_parser("server", help="Start the API Server")
    server_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    server_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    server_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    # helper for cli
    cli_parser = subparsers.add_parser("cli", help="Start the Interactive CLI")
    
    args = parser.parse_args()
    
    if args.command == "server":
        start_server(args.host, args.port, args.reload)
    elif args.command == "cli":
        start_cli_session()
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
