from __future__ import annotations

import logging
import os
import warnings
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging() -> None:
    log_dir = Path(os.getenv("SMARTSPEND_LOG_DIR", Path(__file__).resolve().parent / "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "smartspend.log"

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    # Default to ERROR in local dev so terminal stays readable.
    # To restore verbose logs later, set SMARTSPEND_LOG_LEVEL=INFO.
    root_logger.setLevel(os.getenv("SMARTSPEND_LOG_LEVEL", "ERROR").upper())

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(log_file, maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    file_handler.setFormatter(formatter)

    root_logger.addHandler(stream_handler)
    root_logger.addHandler(file_handler)

    # Keep third-party libraries quiet unless they emit errors.
    noisy_loggers = [
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "prophet",
        "cmdstanpy",
        "tensorflow",
        "faiss",
        "absl",
    ]
    for name in noisy_loggers:
        logging.getLogger(name).setLevel(logging.ERROR)

    # Suppress warning-level noise from ML stack in terminal.
    # Comment these back in if you want to debug model convergence/training behavior.
    warnings.filterwarnings("ignore", category=UserWarning)
    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", message=".*ConvergenceWarning.*")
    warnings.filterwarnings("ignore", message=".*oneDNN custom operations are on.*")
    warnings.filterwarnings("ignore", message=".*Do not pass an `input_shape`/`input_dim` argument.*")

    try:
        from sklearn.exceptions import ConvergenceWarning  # type: ignore

        warnings.filterwarnings("ignore", category=ConvergenceWarning)
    except Exception:
        pass
