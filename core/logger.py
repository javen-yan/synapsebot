import logging
from rich.console import Console
from rich.logging import RichHandler

class Logger:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            # Force terminal colors to ensure they work with prompt_toolkit's patch_stdout
            cls._instance.console = Console(force_terminal=True)
            cls._instance.logger = logging.getLogger("agent_lite")
            cls._instance._configured = False
        return cls._instance

    class RichToPromptToolkitIO:
        def write(self, text: str):
            from prompt_toolkit import print_formatted_text
            from prompt_toolkit.formatted_text import ANSI
            if text:
                 # Use print_formatted_text to render ANSI correctly through the patch
                 print_formatted_text(ANSI(text), end='')

        def flush(self):
            pass

    def configure(self, level: str = "INFO", log_file: str = None):
        """Configure the global logger."""
        if self._configured:
            return

        level = level.upper()
        log_level = getattr(logging, level, logging.INFO)
        
        # Use custom IO adapter for proper ANSI rendering in CLI
        custom_io = self.RichToPromptToolkitIO()
        self.console = Console(file=custom_io, force_terminal=True)

        # Configure logging
        handlers = [RichHandler(console=self.console, show_time=False, show_path=False, markup=True)]
        if log_file:
            handlers.append(logging.FileHandler(log_file))

        logging.basicConfig(
            level=log_level,
            format="%(message)s",
            datefmt="[%X]",
            handlers=handlers
        )
        
        self.logger.setLevel(log_level)
        self._configured = True

    def info(self, message: str, **kwargs):
        self.console.print(message, **kwargs)

    def debug(self, message: str, **kwargs):
        if self.logger.isEnabledFor(logging.DEBUG):
            self.console.print(f"[dim]{message}[/dim]", **kwargs)

    def warning(self, message: str, **kwargs):
        self.console.print(f"[yellow]{message}[/yellow]", **kwargs)

    def error(self, message: str, **kwargs):
        self.console.print(f"[red]{message}[/red]", **kwargs)
    
    def print(self, message: str, **kwargs):
        """Direct access to console print for general output."""
        self.console.print(message, **kwargs)

# Global instance
logger = Logger()
