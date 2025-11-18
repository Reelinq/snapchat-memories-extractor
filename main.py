import json
import os
import requests
import time
from pathlib import Path
import zipfile
from io import BytesIO
from ui import print_status, update_progress, clear_lines
from models import Memory
from metadata_utils import add_image_data, add_video_metadata

# Read the JSON file
json_path = 'data/memories_history.json'
with open(json_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Create downloads folder in repo root if it doesn't exist
downloads_folder = "downloads"
os.makedirs(downloads_folder, exist_ok=True)

# Track used names to avoid overwrites; seed with existing files
used_names = set()
try:
    used_names = {p.name for p in Path(downloads_folder).iterdir() if p.is_file()}
except Exception:
    used_names = set()

# Resolve duplicate filenames by appending _n suffix before extension
def resolve_unique_path(path: str) -> str:
    base, ext = os.path.splitext(path)
    candidate = path
    suffix = 1
    while os.path.exists(candidate) or os.path.basename(candidate) in used_names:
        candidate = f"{base}_{suffix}{ext}"
        suffix += 1
    used_names.add(os.path.basename(candidate))
    return candidate

# Keep raw items to enable pruning of successful downloads
raw_items = data.get('Saved Media', [])
success_indices = set()

# Initialize counters and timers
total_files = len(raw_items)
successful = 0
failed = 0
start_time = time.time()
total_bytes = 0

# Download each file represented by Memory models
for index, item in enumerate(raw_items, 1):
    memory = Memory.model_validate(item)
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

        # Detect if the content is a ZIP archive
        is_zip = False
        content_type = response.headers.get('Content-Type', '').lower()
        if 'zip' in content_type:
            is_zip = True
        else:
            content_head = response.content[:4]
            if content_head.startswith(b'PK\x03\x04'):
                is_zip = True

        # Prepare bytes and handling mode, then fall through to unified save/metadata
        image = False
        content_bytes = None
        if is_zip:
            with zipfile.ZipFile(BytesIO(response.content)) as zf:
                # Check for JPG or MP4 in the ZIP (ignore PNG)
                jpg_name = [n for n in zf.namelist() if n.lower().endswith(('.jpg', '.jpeg'))]
                mp4_name = [n for n in zf.namelist() if n.lower().endswith('.mp4')]

                if jpg_name:
                    content_bytes = zf.read(jpg_name[0])
                    filepath = os.path.join(downloads_folder, f"{memory.filename}.jpg")
                    image = True
                elif mp4_name:
                    content_bytes = zf.read(mp4_name[0])
                    filepath = os.path.join(downloads_folder, f"{memory.filename}.mp4")
                    image = False
                else:
                    raise Exception("ZIP did not contain a JPG or MP4 file")
        else:
            content_bytes = response.content
            image = (memory.media_type == "Image")

        # Resolve final unique path and save once, then write metadata
        filepath = resolve_unique_path(filepath)
        with open(filepath, 'wb') as f:
            f.write(content_bytes)

        try:
            if image:
                add_image_data(Path(filepath), memory)
            else:
                add_video_metadata(Path(filepath), memory)
        except Exception:
            if os.path.exists(filepath):
                os.remove(filepath)
            raise

        file_size = os.path.getsize(filepath)
        total_bytes += file_size
        successful += 1
        success_indices.add(index - 1)
        # Persist JSON after each success
        remaining = [itm for i, itm in enumerate(raw_items) if i not in success_indices]
        data['Saved Media'] = remaining
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    except requests.exceptions.HTTPError as e:
        # If 405 error on primary, try fallback URL
        status = getattr(e.response, 'status_code', None)
        if status == 405 and fallback_url:
            try:
                response = requests.get(fallback_url, timeout=30)
                response.raise_for_status()

                # Detect if the content is a ZIP archive (fallback path)
                is_zip = False
                content_type = response.headers.get('Content-Type', '').lower()
                if 'zip' in content_type:
                    is_zip = True
                else:
                    content_head = response.content[:4]
                    if content_head.startswith(b'PK\x03\x04'):
                        is_zip = True

                # Prepare bytes and handling mode as above, then unify save/metadata
                image = False
                content_bytes = None
                if is_zip:
                    with zipfile.ZipFile(BytesIO(response.content)) as zf:
                        jpg_name = [n for n in zf.namelist() if n.lower().endswith(('.jpg', '.jpeg'))]
                        mp4_name = [n for n in zf.namelist() if n.lower().endswith('.mp4')]

                        if jpg_name:
                            content_bytes = zf.read(jpg_name[0])
                            filepath = os.path.join(downloads_folder, f"{memory.filename}.jpg")
                            image = True
                        elif mp4_name:
                            content_bytes = zf.read(mp4_name[0])
                            filepath = os.path.join(downloads_folder, f"{memory.filename}.mp4")
                            image = False
                        else:
                            raise Exception("ZIP did not contain a JPG or MP4 file")
                else:
                    content_bytes = response.content
                    image = (memory.media_type == "Image")

                filepath = resolve_unique_path(filepath)
                with open(filepath, 'wb') as f:
                    f.write(content_bytes)

                try:
                    if image:
                        add_image_data(Path(filepath), memory)
                    else:
                        add_video_metadata(Path(filepath), memory)
                except Exception:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    raise

                file_size = os.path.getsize(filepath)
                total_bytes += file_size
                successful += 1
                success_indices.add(index - 1)
                remaining = [itm for i, itm in enumerate(raw_items) if i not in success_indices]
                data['Saved Media'] = remaining
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
            except Exception:
                failed += 1
        else:
            failed += 1
    except Exception:
        failed += 1

# After processing, prune successfully downloaded items from JSON and save
# Final sync is not strictly necessary due to per-success writes,
# but keep it to ensure consistency at end of run.
if success_indices:
    remaining = [itm for i, itm in enumerate(raw_items) if i not in success_indices]
    data['Saved Media'] = remaining
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Final status
clear_lines(10)
total_time = time.time() - start_time
print_status(total_files, total_files, successful, failed, total_time, "✅ COMPLETE!")
