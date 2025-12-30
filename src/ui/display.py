import sys
import unicodedata
import threading
import time

display_lock = threading.Lock()

def format_time(seconds):
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds // 60:.0f}m {seconds % 60:.0f}s"
    else:
        return f"{seconds // 3600:.0f}h {(seconds % 3600) // 60:.0f}m"


def display_width(text: str) -> int:
    width = 0
    for character in text:
        if unicodedata.category(character) in ('Mn', 'Me', 'Cf'):
            continue
        east_asian_width = unicodedata.east_asian_width(character)
        if east_asian_width in ('W', 'F'):
            width += 2
            continue
        codepoint = ord(character)
        if (0x1F300 <= codepoint <= 0x1F5FF) or (0x1F600 <= codepoint <= 0x1F64F) or (0x1F680 <= codepoint <= 0x1F6FF) or (0x2600 <= codepoint <= 0x26FF) or (0x2700 <= codepoint <= 0x27BF) or (0x1F900 <= codepoint <= 0x1F9FF):
            width += 2
            continue
        width += 1
    return width

def pad_line(content, total_width=70):
    visible_width = display_width(content)
    padding_needed = total_width - visible_width
    return content + (' ' * max(0, padding_needed))


def update_progress_threadsafe(completed, total, success, failed, start_time, filename, ui_shown):
    from src.ui.display import update_progress
    with display_lock:
        return update_progress(completed, total, success, failed, start_time, filename, ui_shown)


def print_status_threadsafe(total_files, completed_files, success, failed, total_time, message):
    from src.ui.display import print_status
    with display_lock:
        print_status(total_files, completed_files,
                     success, failed, total_time, message)


def print_info(message):
    with display_lock:
        print(message)


def clear_lines(n):
    with display_lock:
        for _ in range(n):
            sys.stdout.write('\033[F\033[K')

def print_status(current, total, successful, failed, elapsed_time, current_file=""):
    remaining = total - current
    percent = (current / total * 100) if total > 0 else 0

    bar_length = 55
    filled_bar_length = int(bar_length * current / total) if total > 0 else 0
    progress_bar_display = '█' * filled_bar_length + \
        '░' * (bar_length - filled_bar_length)

    if current > 0:
        avg_time = elapsed_time / current
        eta = avg_time * remaining
        estimated_time_remaining_string = format_time(eta)
    else:
        estimated_time_remaining_string = "calculating..."

    elapsed_time_string = format_time(elapsed_time)

    max_file_len = 60
    if len(current_file) > max_file_len:
        display_file = current_file[:max_file_len - 3] + "..."
    else:
        display_file = current_file.ljust(max_file_len)

    line1 = ' SNAPCHAT MEMORIES DOWNLOADER '
    line2 = f"  [{progress_bar_display}] {percent:5.1f}%"
    line3 = f"  📥 Downloaded: {successful:>5}  │  ❌ Failed: {failed:>5}  │  ⏳ Remaining: {remaining:>5}"
    line4 = f"  ⏱️  Elapsed: {elapsed_time_string:>10}  │  🕐 ETA: {estimated_time_remaining_string:>30}"
    line5 = f"  📄 {display_file}"

    print(f"╔{'═' * 70}╗")
    print(f"║{pad_line(line1)}║")
    print(f"╠{'═' * 70}╣")
    print(f"║{pad_line(line2)}║")
    print(f"╠{'═' * 70}╣")
    print(f"║{pad_line(line3)}║")
    print(f"║{pad_line(line4)}║")
    print(f"╠{'═' * 70}╣")
    print(f"║{pad_line(line5)}║")
    print(f"╚{'═' * 70}╝")

def update_progress(completed, total, successful, failed, start_time, current_file, ui_shown):
    if ui_shown:
        clear_lines(10)

    elapsed = time.time() - start_time
    print_status(completed, total, successful, failed,
                 elapsed, f"Downloading: {current_file}")
    return True
