import structlog
from structlog.stdlib import LoggerFactory
from structlog.processors import TimeStamper, StackInfoRenderer, format_exc_info
from structlog.typing import Processor, EventDict
from typing import List, Optional
from rich.console import Console

console = Console()

def get_console_output() -> Processor:
    return structlog.dev.ConsoleRenderer(
        colors=True,
        exception_formatter=structlog.dev.default_exception_formatter,
    )

def get_json_output() -> Processor:
    return structlog.processors.JSONRenderer()

def get_file_output(log_file: str) -> Processor:
    return structlog.processors.JSONRenderer(file=open(log_file, "a"))

def get_rich_console_output() -> Processor:
    def rich_renderer(_, __, event_dict: EventDict) -> str:
        level = event_dict.get("level", "info").upper()
        message = event_dict.get("event", "")
        extra = {k: v for k, v in event_dict.items() if k not in {"level", "event", "timestamp"}}
        console.print(f"[bold]{level}[/bold]: {message}")
        if extra:
            console.print(extra, style="dim")
        return ""
    return rich_renderer

def configure_logging(
    log_level: str = "INFO",
    log_format: str = "console",
    log_file: Optional[str] = None,
    use_rich: bool = False
) -> structlog.stdlib.BoundLogger:
    processors: List[Processor] = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        TimeStamper(fmt="iso"),
        StackInfoRenderer(),
        format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if log_format == "console":
        processors.append(get_rich_console_output() if use_rich else get_console_output())
    elif log_format == "json":
        processors.append(get_json_output())

    if log_file:
        processors.append(get_file_output(log_file))

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    root_logger = structlog.get_logger()
    root_logger.setLevel(log_level)
    return root_logger

def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    logger = structlog.get_logger(name)
    return logger.bind(module=name) if name else logger
