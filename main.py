import json
import os
import requests
import time
from pathlib import Path
from ui import print_status, update_progress, clear_lines
from models import Memory
from metadata_utils import add_image_data, add_video_metadata

# Read the JSON file
with open('data/memories_history.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Create downloads folder in repo root if it doesn't exist
downloads_folder = "downloads"
os.makedirs(downloads_folder, exist_ok=True)

# Map JSON entries to Memory models
memories = [Memory.model_validate(m) for m in data.get('Saved Media', [])]

# Initialize counters and timers
total_files = len(memories)
successful = 0
failed = 0
start_time = time.time()
total_bytes = 0

# Download each file represented by Memory models
for index, memory in enumerate(memories, 1):
    filename = memory.filename_with_ext
    filepath = os.path.join(downloads_folder, filename)

    # Update progress display
    update_progress(index, total_files, successful, failed, start_time, filename)

    primary_url = memory.media_download_url
    fallback_url = memory.download_link

    try:
        if not primary_url and not fallback_url:
            failed += 1
            continue

        # Try Media Download Url first when available
        if primary_url:
            response = requests.get(primary_url, timeout=30)
            response.raise_for_status()
        else:
            response = requests.get(fallback_url, timeout=30)
            response.raise_for_status()

        with open(filepath, 'wb') as f:
            f.write(response.content)

        # Add metadata for images and videos - fail if datetime missing
        try:
            if memory.media_type == "Image":
                add_image_data(Path(filepath), memory)
            else:  # Video
                add_video_metadata(Path(filepath), memory)
        except Exception:
            # Delete file if metadata writing failed
            if os.path.exists(filepath):
                os.remove(filepath)
            raise  # Re-raise to mark as failed

        file_size = os.path.getsize(filepath)
        total_bytes += file_size
        successful += 1

    except requests.exceptions.HTTPError as e:
        # If 405 error on primary, try fallback URL
        status = getattr(e.response, 'status_code', None)
        if status == 405 and fallback_url:
            try:
                response = requests.get(fallback_url, timeout=30)
                response.raise_for_status()

                with open(filepath, 'wb') as f:
                    f.write(response.content)

                # Add metadata for images and videos - fail if datetime missing
                try:
                    if memory.media_type == "Image":
                        add_image_data(Path(filepath), memory)
                    else:  # Video
                        add_video_metadata(Path(filepath), memory)
                except Exception:
                    # Delete file if metadata writing failed
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    raise  # Re-raise to mark as failed

                file_size = os.path.getsize(filepath)
                total_bytes += file_size
                successful += 1
            except Exception:
                failed += 1
        else:
            failed += 1
    except Exception:
        failed += 1

# Final status
clear_lines(10)
total_time = time.time() - start_time
print_status(total_files, total_files, successful, failed, total_time, "✅ COMPLETE!")
