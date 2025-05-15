# log_config.py
import os
import sys
import pytz
import logging
import datetime
from logging.handlers import TimedRotatingFileHandler


def setup_logging(config):
    log_level       = getattr(logging, config["log"]["level"].upper(), logging.INFO)
    log_dir         = config["log"]["directory"]
    filename_prefix = config["log"]["filename_prefix"]
    timezone        = pytz.timezone(config["log"]["timezone"])
    retention_days  = config["log"].get("retention_days", 30)

    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, f"{filename_prefix}.log")

    class ShanghaiFormatter(logging.Formatter):
        def formatTime(self, record, datefmt=None):
            dt = datetime.datetime.fromtimestamp(record.created, tz=pytz.utc)
            local_time = dt.astimezone(timezone)
            return local_time.strftime(datefmt or "%Y-%m-%d %H:%M:%S")

    formatter = ShanghaiFormatter('%(asctime)s - %(levelname)s - %(message)s')

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)

    file_handler = TimedRotatingFileHandler(
        filename=log_file_path,
        when='midnight',
        interval=1,
        backupCount=retention_days,
        encoding='utf-8',
        utc=True
    )
    file_handler.setFormatter(formatter)

    logging.basicConfig(
        level=log_level,
        handlers=[console_handler, file_handler]
    )

    logger = logging.getLogger(__name__)
    logger.info("✅ 日志初始化完成，写入目录: %s(保留 %d 天)", log_dir, retention_days)
    return logger
