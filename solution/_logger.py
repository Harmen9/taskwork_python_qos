import logging
from pathlib import Path

class CustomLogger():
    def __init__(self, log_file='app.log', log_dir='logs'):
        if Path(log_dir).is_absolute():
            self.log_dir = log_dir
        else:
            self.log_dir = Path.cwd() / log_dir
        self.log_file = self.log_dir / log_file
        self._setup_logging()

    def _setup_logging(self):
        self.log_dir.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
