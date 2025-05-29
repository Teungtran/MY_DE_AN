import logging
import os
from pathlib import Path

from dotenv import load_dotenv
import yaml

load_dotenv()

logger = logging.getLogger(__name__)


def load_yaml(file_path: str):
    """
    Load a YAML file and return its contents as a Python object (e.g., dictionary, list).

    :param file_path: Path to the YAML file
    :return: The parsed data from the YAML file
    """

    try:
        with open(file_path, "r") as file:
            # Using safe_load to avoid arbitrary code execution risks
            data = yaml.safe_load(file)
    except FileNotFoundError:
        logger.error('Error: The file "%s" was not found.', file_path)
    except yaml.YAMLError as e:
        logger.error("Error parsing YAML file: %s", e)
    except Exception as e:
        logger.exception("An unexpected error occurred: %s", e)
    return data


def load_config():
    """
    Get the absolute path of the current directory where the script is executed
    """
    # Define the path to the config.yaml file
    config_file_path = Path("config/config.yaml")

    if not os.path.isabs(config_file_path):
        root_path = Path(__file__).parents[2]
        config_file_path = root_path / config_file_path

    # Check if the config.yaml file exists
    if os.path.exists(config_file_path):
        config_data = load_yaml(str(config_file_path))  # Load the content of the YAML file
        logger.info("Config data loaded successfully from %s.", config_file_path)
        return config_data
    else:
        logger.warning("Config file not found at %s", config_file_path)
        return None


CONFIG = load_config()


if __name__ == "__main__":
    print(CONFIG)
