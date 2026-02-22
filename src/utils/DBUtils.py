
import yaml
import os
import re
from functools import reduce
import operator
from threading import Lock
import logging

logger = logging.getLogger(__name__)


class DBConfig:
    """
    A singleton class to manage database configuration from a YAML file.
    It handles environment variable substitution.
    """
    _instance = None
    _lock = Lock()

    # Static keys for easy access to config values
    KEY_DB_HOST = "Connection.DB_HOST"
    KEY_DB_PORT = "Connection.DB_PORT"
    KEY_DB_TYPE = "Connection.DB_TYPE"

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        with self._lock:
            if hasattr(self, '_initialized'):
                return
            self._initialized = True
            
            # This path is relative to the project root.
            config_path = "src/config/db_config.yaml"
            with open(config_path, "r") as f:
                raw_config = f.read()

            def env_var_replacer(match):
                var_name, default_value = match.groups()
                return os.getenv(var_name, default_value)

            # Expanded variables with defaults, e.g., ${VAR:-default}
            expanded_config = re.sub(r'\$\{([^:}]+):-([^}]+)\}', env_var_replacer, raw_config)
            # Expanded simple variables, e.g., ${VAR}
            expanded_config = os.path.expandvars(expanded_config)
            
            self._config = yaml.safe_load(expanded_config)

    def get(self, key_path):
        """
        Retrieves a value from the nested config using a dot-separated key path.
        Example: get(DBConfig.KEY_DB_HOST)
        """
        try:
            keys = key_path.split('.')
            return reduce(operator.getitem, keys, self._config)
        except (KeyError, TypeError):
            logger.error(f"Configuration key '{key_path}' not found.")
            raise KeyError(f"Configuration key '{key_path}' not found.")

_db_config_instance = DBConfig()

def get_config(key_path):
    """
    A convenience function to get a configuration value from the singleton DBConfig instance.
    """
    return _db_config_instance.get(key_path)
