import argparse

def get_cli_args():
    parser = argparse.ArgumentParser(description='Snapchat Memories Downloader')
    parser.add_argument('--stream-chunk-size', '-S', type=int, default=1024, metavar='KB',
                        help='Size of each chunk in kilobytes (default: 1024, i.e. 1 MB). Short: -S')
    parser.add_argument('--ffmpeg-timeout', '-f', type=int, default=60, metavar='SECONDS',
                        help='Seconds to wait for ffmpeg operations (default: 60). Short: -f')
    parser.add_argument('--request-timeout', '-t', type=int, default=30, metavar='SECONDS',
                        help='Seconds to wait for HTTP requests (default: 30). Short: -t')
    parser.add_argument('--concurrent', '-c', type=int, default=5,
                        metavar='N', help='Concurrent downloads (default: 5). Short: -c')
    parser.add_argument('--no-overlay', '-O', default=False, action='store_true',
                        help='Skip applying PNG overlay (default: overlay applied). Short: -O')
    parser.add_argument('--no-metadata', '-M', default=False, action='store_true',
                        help='Skip writing metadata (default: metadata written). Short: -M')
    parser.add_argument('--attempts', '-a', type=int, default=3,
                        metavar='N', help='Max retry attempts (default: 3). Short: -a')
    parser.add_argument('--strict', '-s', default=False, dest='strict_location',
                        action='store_true', help='Fail downloads when location metadata is missing. Short: -s')
    parser.add_argument('--jpeg-quality', '-q', type=int, default=95,
                        metavar='N', help='JPEG quality 1-100 (default: 95). Short: -q')
    parser.add_argument('--no-jxl', '-J', default=False, action='store_true',
                        help='Skip JPGXL conversion and keep original JPEG (default: convert to lossless JPGXL). Short: -J')
    parser.add_argument('--log-level', '-l', type=str, default='OFF', metavar='LEVEL',
                        help='Logging level: 0=OFF, 1=CRITICAL, 2=ERROR, 3=WARNING, 4=INFO, 5=DEBUG. Can also use names: OFF, CRITICAL, ERROR, WARNING, INFO, DEBUG (default: 0/OFF). Short: -l')
    return parser.parse_args()
