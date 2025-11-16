import json
import os
import requests
import time

# Read the JSON file
with open('data/memories_history.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Create downloads folder in repo root if it doesn't exist
downloads_folder = "downloads"
os.makedirs(downloads_folder, exist_ok=True)

# Initialize counters and timers
total_files = len(data['Saved Media'])
successful = 0
failed = 0
start_time = time.time()
total_bytes = 0

print(f"Starting download of {total_files} files...\n")

# Download each file from the JSON data
for index, memory in enumerate(data['Saved Media'], 1):
    download_link = memory['Media Download Url']
    date = memory['Date']
    media_type = memory['Media Type']

    # Replace spaces with underscores and colons with hyphens for valid Windows filename
    filename_base = date.replace(' ', '_').replace(':', '-')

    # Determine file extension based on media type
    extension = '.jpg' if media_type == 'Image' else '.mp4'
    filename = f"{filename_base}{extension}"
    filepath = os.path.join(downloads_folder, filename)

    # Print progress
    elapsed_time = time.time() - start_time
    percent = (index / total_files) * 100
    print(f"[{index}/{total_files}] ({percent:.1f}%) Downloading: {filename}... ", end='', flush=True)

    try:
        # Try Media Download Url first
        response = requests.get(download_link, timeout=30)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            f.write(response.content)

        file_size = os.path.getsize(filepath)
        total_bytes += file_size
        successful += 1
        print("✓")

    except requests.exceptions.HTTPError as e:
        # If 405 error, try the regular Download Link
        if e.response.status_code == 405:
            try:
                alt_link = memory['Download Link']
                response = requests.get(alt_link, timeout=30)
                response.raise_for_status()

                with open(filepath, 'wb') as f:
                    f.write(response.content)

                file_size = os.path.getsize(filepath)
                total_bytes += file_size
                successful += 1
                print("✓ (alt link)")

            except Exception as e2:
                failed += 1
                print(f"✗ Failed: {str(e2)}")
        else:
            failed += 1
            print(f"✗ Failed: {str(e)}")
    except Exception as e:
        failed += 1
        print(f"✗ Failed: {str(e)}")

# Final status
total_time = time.time() - start_time
total_mb = total_bytes / (1024 * 1024)
print(f"\n{'='*60}")
print(f"✅ DOWNLOAD COMPLETE!")
print(f"{'='*60}")
print(f"Total files: {total_files}")
print(f"Successful: {successful}")
print(f"Failed: {failed}")
print(f"Total size: {total_mb:.2f} MB")
print(f"Time elapsed: {total_time:.1f} seconds")
print(f"Average speed: {total_mb/total_time:.2f} MB/s" if total_time > 0 else "Average speed: N/A")
print(f"{'='*60}")
