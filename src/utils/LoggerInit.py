import logging
import logging.config
from pathlib import Path
import os
# Setup logging
log_file_path_env = os.getenv('LOG_FILE_PATH')

if log_file_path_env:
    # If the environment variable is set, use it.
    # Ensure the directory exists.
    log_file_path = Path(log_file_path_env)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
else:
    # Default behavior: log inside the project structure.
    project_root = Path(__file__).parent.parent.parent
    log_dir = project_root / 'logs'
    log_dir.mkdir(exist_ok=True)  # Ensure the logs directory exists
    log_file_path = log_dir / 'chattwin.log'

config_path = Path(__file__).parent.parent / 'config' / 'logger.conf'
logging.config.fileConfig(
    config_path,
    defaults={'log_file_path': str(log_file_path)}
)

logging.getLogger(__name__).info("Logging configured.")