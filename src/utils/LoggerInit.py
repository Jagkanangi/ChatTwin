import os
import logging.config
from pathlib import Path

def init():
    # 1. Define Paths relative to this file
    CURRENT_DIR = Path(__file__).parent
    SRC_DIR = CURRENT_DIR.parent
    PROJECT_ROOT = SRC_DIR.parent # This is /app in Docker

    # 2. Setup Log File Path
    log_file_path_env = os.getenv('LOG_FILE_PATH')

    if log_file_path_env:
        log_file_path = Path(log_file_path_env)
    else:
        # Use PROJECT_ROOT so logs are at the top level
        log_dir = PROJECT_ROOT / 'logs'
        log_dir.mkdir(exist_ok=True)
        log_file_path = log_dir / 'chattwin.log'

    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # 3. Locate Config (Inside src/config)
    config_path = SRC_DIR / 'config' / 'logger.conf'

    # 4. Initialize
    logging.config.fileConfig(
        config_path,
        defaults={'log_file_path': str(log_file_path)}
    )