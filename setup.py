import os
```python
import json

def setup_directories():
    """Create necessary directories if they don't exist."""
    directories = ["converted", "logs"]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created directory: {directory}")

def setup_exported_posts():
    """Create exported_posts.json if it doesn't exist."""
    if not os.path.exists("exported_posts.json"):
        with open("exported_posts.json", "w") as f:
            json.dump([], f)
            print("Created exported_posts.json")

def setup_logging_config():
    """Create a basic logging configuration file."""
    config = {
        "version": 1,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            },
        },
        "handlers": {
            "file": {
                "class": "logging.FileHandler",
                "level": "INFO",
                "formatter": "standard",
                "filename": "logs/newsletter_migrator.log",
                "mode": "a",
            },
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            }
        },
        "loggers": {
            "": {
                "handlers": ["file", "console"],
                "level": "INFO",
            }
        }
    }
    
    if not os.path.exists("logging_config.json"):
        with open("logging_config.json", "w") as f:
            json.dump(config, f, indent=4)
            print("Created logging_config.json")

if __name__ == "__main__":
    setup_directories()
    setup_exported_posts()
    setup_logging_config()
    print("Setup complete!")
```
