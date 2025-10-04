import sys
import json
import logging
import contextvars

import colorlog
import google.cloud.logging
from google.cloud.logging_v2.handlers import CloudLoggingHandler


trace_id_var = contextvars.ContextVar("trace_id", default="no-trace")

def set_trace_id(trace_id: str):
    trace_id_var.set(trace_id)

class ContextFilter(logging.Filter):
    def filter(self, record):
        record.trace_id = trace_id_var.get()
        return True
    
class JsonFormatter(logging.Formatter):
        """Custom formatter that outputs logs as JSON."""
        def format(self, record):
            log_record = {
                "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%SZ"),
                "severity": record.levelname,
                "message": record.getMessage(),
                "logger": record.name,
                "filename": record.filename,
                "line": record.lineno,
                "process": record.process,
                "trace_id": getattr(record, "trace_id", "no-trace")
            }
            if record.exc_info:
                log_record["exception"] = self.formatException(record.exc_info)
            return json.dumps(log_record)

def get_logger(name=__name__):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Local Logging
    stdout = colorlog.StreamHandler(stream=sys.stdout)
    stdout.addFilter(ContextFilter())
    fmt = colorlog.ColoredFormatter(
        "%(name)s: %(white)s%(asctime)s%(reset)s | "
        "%(log_color)s%(levelname)s%(reset)s | "
        "%(blue)s%(filename)s:%(lineno)s%(reset)s | "
        "%(cyan)s%(trace_id)s%(reset)s | "
        "%(process)d >>> %(log_color)s%(message)s%(reset)s"
    )
    stdout.setFormatter(fmt)
    logger.addHandler(stdout)

    #Google Cloud Logging
    client = google.cloud.logging.Client()
    cloud_handler = CloudLoggingHandler(client)
    cloud_handler.addFilter(ContextFilter())
    cloud_handler.setFormatter(JsonFormatter())
    logger.addHandler(cloud_handler)

    return logger