import logging
from pathlib import Path
import os


LOG_DIR = f'{Path(__file__).parent}/logs'
if not os.path.exists(LOG_DIR):
  os.makedirs(LOG_DIR, exist_ok=True)


def create_logger(name: str):
  logger = logging.getLogger(name)
  logger.setLevel(logging.DEBUG)

  formatter = logging.Formatter('%(asctime)s - %(module)s - Line: %(lineno)d - %(levelname)s - %(message)s')

  # ch = logging.StreamHandler()
  # ch.setLevel(logging.DEBUG)
  # ch.setFormatter(formatter)
  # logger.addHandler(ch)

  fh = logging.FileHandler(f'{LOG_DIR}/{name}.log', mode='w')
  fh.setLevel(logging.DEBUG)
  fh.setFormatter(formatter)
  logger.addHandler(fh)

  return logger