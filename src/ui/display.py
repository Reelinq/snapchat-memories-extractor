import sys
import unicodedata

# Convert bytes to human readable format
def format_size(byte_count):
	for unit in ['B', 'KB', 'MB', 'GB']:
		if byte_count < 1024.0:
			return f"{byte_count:.1f}{unit}"
		byte_count /= 1024.0
	return f"{byte_count:.1f}TB"


# Convert seconds to human readable format
def format_time(seconds):
	if seconds < 60:
		return f"{seconds:.0f}s"
	elif seconds < 3600:
		return f"{seconds//60:.0f}m {seconds%60:.0f}s"
	else:
		return f"{seconds//3600:.0f}h {(seconds%3600)//60:.0f}m"


# Clear n lines in terminal
def clear_lines(line_count):
	for _ in range(line_count):
		sys.stdout.write('\033[F\033[K')


# Compute displayed width of a string in terminal (accounts for emojis)
def display_width(text: str) -> int:
	width = 0
	for character in text:
		# skip zero-width / combining marks
		if unicodedata.category(character) in ('Mn', 'Me', 'Cf'):
			continue
		# East Asian Wide or Fullwidth are 2 columns
		east_asian_width = unicodedata.east_asian_width(character)
		if east_asian_width in ('W', 'F'):
			width += 2
			continue
		# Common emoji/codepoint ranges - treat as width 2
		codepoint = ord(character)
		if (0x1F300 <= codepoint <= 0x1F5FF) or (0x1F600 <= codepoint <= 0x1F64F) or (0x1F680 <= codepoint <= 0x1F6FF) or (0x2600 <= codepoint <= 0x26FF) or (0x2700 <= codepoint <= 0x27BF) or (0x1F900 <= codepoint <= 0x1F9FF):
			width += 2
			continue
		# default monospace width
		width += 1
	return width


# Pad content to exact visible width (total_width columns)
def pad_line(content, total_width=70):
	visible_width = display_width(content)
	padding_needed = total_width - visible_width
	return content + (' ' * max(0, padding_needed))


def print_status(current, total, successful, failed, elapsed_time, current_file=""):
	remaining = total - current
	percent = (current / total * 100) if total > 0 else 0

	# Calculate progress bar
	bar_length = 55
	filled_bar_length = int(bar_length * current / total) if total > 0 else 0
	progress_bar_display = '█' * filled_bar_length + '░' * (bar_length - filled_bar_length)

	# Estimate time remaining
	if current > 0:
		avg_time = elapsed_time / current
		eta = avg_time * remaining
		estimated_time_remaining_string = format_time(eta)
	else:
		estimated_time_remaining_string = "calculating..."

	# Format numbers with fixed width
	elapsed_time_string = format_time(elapsed_time)

	# Truncate and pad filename to exact width
	max_file_len = 60
	if len(current_file) > max_file_len:
		display_file = current_file[:max_file_len-3] + "..."
	else:
		display_file = current_file.ljust(max_file_len)

	# Build lines with exact padding
	line1 = ' SNAPCHAT MEMORIES DOWNLOADER '
	line2 = f"  [{progress_bar_display}] {percent:5.1f}%"
	line3 = f"  📥 Downloaded: {successful:>5}  │  ❌ Failed: {failed:>5}  │  ⏳ Remaining: {remaining:>5}"
	line4 = f"  ⏱️  Elapsed: {elapsed_time_string:>10}  │  🕐 ETA: {estimated_time_remaining_string:>30}"
	line5 = f"  📄 {display_file}"

	# Print status box with exact padding
	print(f"╔{'═'*70}╗")
	print(f"║{pad_line(line1)}║")
	print(f"╠{'═'*70}╣")
	print(f"║{pad_line(line2)}║")
	print(f"╠{'═'*70}╣")
	print(f"║{pad_line(line3)}║")
	print(f"║{pad_line(line4)}║")
	print(f"╠{'═'*70}╣")
	print(f"║{pad_line(line5)}║")
	print(f"╚{'═'*70}╝")


# Update progress display for current download
def update_progress(index, total_files, successful, failed, start_time, filename):
	import time

	# Clear previous status if not first iteration
	if index > 1:
		clear_lines(10)

	elapsed = time.time() - start_time
	print_status(index - 1, total_files, successful, failed, elapsed, f"Downloading: {filename}")
