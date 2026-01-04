from src.config.logging_config import parse_log_level

def build_cli_options(args):
    return {
        'max_concurrent_downloads': args.concurrent,
        'apply_overlay': not args.no_overlay,
        'write_metadata': not args.no_metadata,
        'max_attempts': args.attempts,
        'strict_location': args.strict_location,
        'jpeg_quality': args.jpeg_quality,
        'convert_to_jxl': not args.no_jxl,
        'image_overlay_workers': args.image_overlay_workers,
        'log_level': parse_log_level(args.log_level),
        'request_timeout': args.request_timeout,
        'ffmpeg_timeout': args.ffmpeg_timeout,
        'stream_chunk_size': args.stream_chunk_size * 1024
    }
