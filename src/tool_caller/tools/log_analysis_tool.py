import re
import time
import logging
from collections import Counter
from typing import Any, Dict
from ..tools.base import BaseTool, ToolResponse, ToolSchema
from ..config.settings import get_settings

logger = logging.getLogger(__name__)

class LogAnalysisTool(BaseTool):
    """
    Analyzes log files and generates a summary report.
    Supports common log formats with levels: INFO, WARNING, ERROR, DEBUG.
    Uses the log file path from application settings.
    """

    def __init__(self):
        self.settings = get_settings()
        self.log_pattern = re.compile(
            r'(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})?\s*(?P<level>INFO|ERROR|WARNING|DEBUG)?\s*(?P<message>.*)'
        )

    @property
    def name(self) -> str:
        return "log_analysis"

    @property
    def description(self) -> str:
        return "Analyzes the application log file and generates a report with counts of log levels and top errors."

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters={
                "type": "object",
                "properties": {
                    "top_n": {
                        "type": "integer",
                        "description": "Number of top errors to return",
                        "default": 5
                    }
                },
                "required": []
            }
        )

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        top_n = parameters.get("top_n", 5)
        if not isinstance(top_n, int) or top_n <= 0:
            return False
        return True

    async def _run(self, **kwargs) -> Any:
        top_n = int(kwargs.get("top_n", 5))
        
        # Get log file path from settings
        log_file_path = str(self.settings.log_file.absolute())
        
        start_time = time.time()
        level_counts = Counter()
        error_messages = Counter()
        first_timestamp, last_timestamp = None, None
        total_lines = 0

        try:
            with open(log_file_path, "r", encoding="utf-8") as f:
                for line in f:
                    total_lines += 1
                    match = self.log_pattern.match(line.strip())
                    if match:
                        ts, level, msg = match.groups()
                        if ts:
                            if not first_timestamp:
                                first_timestamp = ts
                            last_timestamp = ts
                        if level:
                            level_counts[level] += 1
                            if level == "ERROR" and msg:
                                # Clean up the error message for better grouping
                                clean_msg = msg.strip()
                                error_messages[clean_msg] += 1

            # Calculate processing time
            processing_time = time.time() - start_time

            report = {
                "file_path": log_file_path,
                "total_lines_processed": total_lines,
                "log_entries_with_levels": sum(level_counts.values()),
                "log_levels": dict(level_counts),
                "time_range": {
                    "start": first_timestamp, 
                    "end": last_timestamp
                },
                "top_errors": [
                    {"message": msg, "count": count} 
                    for msg, count in error_messages.most_common(top_n)
                ],
                "processing_time_seconds": round(processing_time, 4)
            }

            logger.info(f"Log analysis completed for {log_file_path} in {processing_time:.4f}s")
            return report

        except FileNotFoundError:
            error_msg = f"Log file not found: {log_file_path}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"Log analysis failed: {str(e)}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)