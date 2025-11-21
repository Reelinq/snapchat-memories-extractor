# Snapchat Memories Extractor

Download all your Snapchat memories with metadata (date, location) embedded directly into images and videos.

---

## ✨ Features

- ✅ Downloads images and videos from Snapchat export JSON
- ✅ Automatically overlays PNG captions on photos and videos from ZIP archives
- ✅ Embeds EXIF metadata (date taken, GPS coordinates) into images
- ✅ Writes creation time and GPS into video files
- ✅ Progressive JSON pruning (safe to Ctrl+C and resume)
- ✅ Fail-fast: Skips files with missing datetime metadata
- ✅ Zero system dependencies: Everything installs via pip!

---

## 📋 Prerequisites

- **Python 3.10+**

---

## 🚀 Quick Start

### Step 1: Clone the Repository

```bash
git clone https://github.com/Reelinq/snapchat-memories-extractor.git
cd snapchat-memories-extractor
```

### Step 2: Create Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/Scripts/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Get Your Snapchat Data

1. Login and export your data from Snapchat: https://accounts.snapchat.com/accounts/downloadmydata
2. Select **both** options: `Export your Memories`, `Export JSON Files`

   ![export configuration](https://github.com/user-attachments/assets/dfcdb6a0-e554-46e8-bdba-77fe41c88a03)

3. Extract the ZIP file and place `memories_history.json` into the `data/` folder

### Step 5: Run the Extractor

```bash
python main.py
```

**Done!** Your files will be saved to `downloads/` with full metadata embedded.

---

## ⚙️ Configuration Options

You can customize the downloader's behavior using command-line arguments:

<details>
<summary><b>🔄 Concurrent Downloads: --concurrent N</b></summary>

**What it does:**
- Controls the number of simultaneous downloads
- **Default**: `5` concurrent downloads
- Higher values = faster downloads, but may trigger rate limiting
- Lower values = slower but more stable

**Examples**:

Use default (5 concurrent downloads):
```bash
python main.py
```

Conservative - 3 concurrent downloads:
```bash
python main.py --concurrent 3
```

Faster - 10 concurrent downloads:
```bash
python main.py --concurrent 10
```

Sequential - 1 download at a time (slowest, but safest):
```bash
python main.py --concurrent 1
```

**💡 Recommendations:**
- **3-5 concurrent downloads**: Safe default, respectful to Snapchat's servers
- **10-15 concurrent downloads**: Faster, works well on most home connections
- **20+ concurrent downloads**: May trigger rate limiting or server throttling
- **1 concurrent download**: Use only if experiencing connection issues

> ⚠️ **Note**: Setting too high may result in rate limiting or failed downloads. If you experience issues, reduce the concurrent value.

</details>

<details>
<summary><b>🔁 Retry Attempts: --attempts N</b></summary>

**What it does:**
- Automatically retries the entire download process if files fail
- **Default**: `3` attempts (runs the download process up to 3 times)
- Useful for handling temporary network errors, server timeouts, or rate limiting
- Stops early if all downloads succeed before max attempts

**Examples**:

Default - try up to 3 times:
```bash
python main.py
```

Single attempt - no retries:
```bash
python main.py --attempts 1
```

Aggressive retries - try up to 5 times:
```bash
python main.py --attempts 5
```

**💡 Recommendations:**
- **3 attempts** (default): Good balance for most situations
- **1 attempt**: Use if you want manual control over retries
- **5+ attempts**: Use for unstable connections or large archives

**How it works:**
1. First attempt downloads all files from the JSON
2. If any files fail, waits 2 seconds then retries ALL failed files
3. Continues until all files succeed or max attempts reached
4. Progress resets between attempts for clarity

> **Example**: If 5 out of 100 files fail on attempt 1, attempt 2 only retries those 5 failed files.

</details>

<details>
<summary><b>🎨 Media Overlays: --no-overlay</b></summary>

**What it does:**
- Snapchat stores your memories with separate layers for text, stickers, drawings, etc. you added
- **By default**, this tool automatically applies those edits on top of your photos and videos, just like you see them in the Snapchat app
- **Images**: Text, stickers, drawings, etc. are permanently added to the image
- **Videos**: Text, stickers, drawings, etc. are burned into the video throughout playback
- Use `--no-overlay` if you want the original media **without** any of your edits

**Examples**:

Default behavior - downloads photos/videos WITH text, stickers, drawings, etc.:
```bash
python main.py
```

Skip overlays - downloads original photos/videos WITHOUT any edits:
```bash
python main.py --no-overlay
```

**💡 Recommendations:**
- **Default (with overlays)**: Best for preserving your memories exactly as you saved them in Snapchat
- **With `--no-overlay`**: Best if you want clean, unedited original photos/videos for editing or archival purposes

> **Example**: If you saved a photo with "Best day ever! 🎉" text, heart stickers, and some doodles on it in Snapchat, the default download will include all of that. With `--no-overlay`, you get the clean original photo without any edits.

</details>

---

## 🔧 Troubleshooting

<details>
<summary><b>⏰ Download Links Expired</b></summary>

Snapchat download links expire after a period of time. If downloads fail, try to export a fresh `memories_history.json` from Snapchat and replace the old one in the `data/` folder.

</details>

<details>
<summary><b>📄 Missing 'memories_history.json'</b></summary>

When exporting your data from Snapchat, make sure you select **both** options:
- ✅ **Export your Memories**
- ✅ **Export JSON Files**

Without these options, the JSON file won't be included in your export.

</details>

<details>
<summary><b>🆘 Still Having Issues?</b></summary>

Please open a new [issue](https://github.com/Reelinq/snapchat-memories-extractor/issues) with the following information:
- Your Python version (`python --version`)
- Operating system
- Error message or unexpected behavior
- Whether the issue is with images or videos

</details>

---

## 📜 License

MIT License - feel free to use and modify as needed.
