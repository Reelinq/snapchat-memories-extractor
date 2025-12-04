# Logging Implementation Summary

## Overview
The application now includes comprehensive structured logging with dual output formats:
1. **JSON Logs** - Machine-readable structured logs for analysis and debugging
2. **Console Output** - Human-readable colorized console output with timestamps

## Key Features

### Structured JSON Logging
- File output: `logs/snapchat_extractor_YYYYMMDD_HHMMSS.jsonl` (one JSON object per line)
- Each log entry includes:
  - `timestamp`: ISO format UTC timestamp
  - `level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - `logger`: Logger name
  - `message`: The log message
  - `module`: Python module name
  - `function`: Function name
  - `line`: Line number
  - `exception`: Exception details (if applicable)
  - Custom extra data fields (passed via `extra_data` parameter)

### Human Console Output
- Color-coded by log level (DEBUG=Cyan, INFO=Green, WARNING=Yellow, ERROR=Red, CRITICAL=Magenta)
- Includes timestamp and formatted message
- Only uses colors when outputting to a terminal (not when redirected)

## File Changes

### New Files
- **`logger.py`** - Complete logging module with JSON and console formatters

### Modified Files
- **`config.py`**
  - Added `logs_folder` configuration (default: `logs/`)
  - Added `log_level` configuration (default: `logging.INFO`)
  - Logs folder created in `__post_init__`

- **`main.py`**
  - Initializes logging on startup
  - Logs application start, configuration, completion, and errors
  - Handles KeyboardInterrupt with warning log

- **`downloader.py`**
  - Imports logger module
  - Logs retry attempts
  - Logs user interruption events
  - Uses logger for structured error reporting

- **`ui/display.py`**
  - Imports logger module
  - Logs individual download errors in `print_error_summary()`

- **`services/download_service.py`**
  - Imports logger module
  - Logs HTTP errors, network errors, and processing errors
  - Logs successful file processing
  - Provides debug information for troubleshooting

## Usage Examples

### Starting the application
```bash
python main.py
```

Console output:
```
2025-12-04 10:30:45 [INFO] Snapchat Memories Extractor started
2025-12-04 10:30:45 [DEBUG] Configuration: concurrent=5, overlay=True, metadata=True
2025-12-04 10:30:45 [INFO] JSON logs being written to: logs/snapchat_extractor_20251204_103045.jsonl
```

JSON log file (logs/snapchat_extractor_20251204_103045.jsonl):
```json
{"timestamp": "2025-12-04T10:30:45.123456", "level": "INFO", "logger": "snapchat_extractor", "message": "Snapchat Memories Extractor started", "module": "main", "function": "__main__", "line": 9}
{"timestamp": "2025-12-04T10:30:45.234567", "level": "DEBUG", "logger": "snapchat_extractor", "message": "Configuration: concurrent=5, overlay=True, metadata=True", "module": "main", "function": "__main__", "line": 11}
```

### Log Levels
- **DEBUG**: Detailed processing information for troubleshooting (file operations, HTTP responses, etc.)
- **INFO**: General informational messages (startup, completion, major events)
- **WARNING**: Warning messages (user interruption, retry attempts)
- **ERROR**: Error messages (failed downloads, exceptions)
- **CRITICAL**: Critical application failures

## Accessing Logs

1. **Console logs**: Displayed in real-time as the application runs
2. **JSON logs**:
   - Location: `logs/` directory
   - Format: JSONL (one JSON object per line)
   - Can be parsed programmatically or analyzed with tools like `jq`

## Log Rotation

Currently, a new JSON log file is created each time the application starts (timestamp-based). Implement manual log rotation or use Python's `RotatingFileHandler` if needed for long-running processes.

## Future Enhancements

1. Add command-line argument for log level (--log-level)
2. Implement automatic log rotation (daily, size-based)
3. Add syslog support for enterprise deployments
4. Add metrics collection from logs (success rate, average download time, etc.)
