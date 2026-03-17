"""ZIM-RAG 接口模块"""

from .cli import main as cli_main
from .gui import launch_gui
from .web import launch_web, create_app

__all__ = ["cli_main", "launch_gui", "launch_web", "create_app"]
