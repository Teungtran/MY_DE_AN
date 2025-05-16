import logging
import os
from pathlib import Path

from dotenv import load_dotenv
import yaml

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def load_yaml(file_path: str):
    """
    Load a YAML file and return its contents as a Python dictionary.

    :param file_path: Path to the YAML file
    :return: The parsed data from the YAML file, or None if an error occurred
    """
    try:
        with open(file_path, "r") as file:
            data = yaml.safe_load(file)
            if data is None:
                logger.warning("YAML file %s is empty.", file_path)
            return data
    except FileNotFoundError:
        logger.error('Error: The file "%s" was not found.', file_path)
    except yaml.YAMLError as e:
        logger.error("Error parsing YAML file: %s", e)
    except Exception as e:
        logger.exception("An unexpected error occurred while loading YAML: %s", e)
    return None


def load_config():
    """
    Load config/config.yaml relative to the project root.
    :return: Dictionary config or None
    """
    try:
        root_path = Path(__file__).resolve().parents[2]
        config_file_path = root_path / "config" / "config.yaml"

        if config_file_path.exists():
            config_data = load_yaml(str(config_file_path))
            if config_data:
                logger.info("✅ Config loaded from %s", config_file_path)
                return config_data
            else:
                logger.warning("⚠️ Config file is empty or invalid at %s", config_file_path)
        else:
            logger.warning("⚠️ Config file not found at %s", config_file_path)
    except Exception as e:
        logger.exception("Unexpected error loading config: %s", e)

    return {}

CONFIG = load_config()

if __name__ == "__main__":
    print(CONFIG)