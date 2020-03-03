from python_back_end.program_settings import PROGRAM_DIRECTORIES as pdir
import logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
            },
        },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            #"formatter": "verbose",
        },
        "svm": {
            "class": "logging.FileHandler",
            "filename": pdir.SVM_LOG_FILE,
            "mode": "w",
        },
        "listener": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "web_interface": {
            "handlers": ["console"],
            "level": logging.INFO,
        },
        "data_cloud_logger": {
            "handlers": ["console"],
            "level": logging.INFO,
        },
        "svm_writer": {
            "handlers": ["svm"],
            "level": logging.INFO,
        },

    },
}