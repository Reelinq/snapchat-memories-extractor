# Snapchat Memories Extractor

Download all your Snapchat memories with metadata (date, location) embedded directly into images and videos.

## Features

- ✅ Downloads images and videos from Snapchat export JSON
- ✅ Embeds EXIF metadata (date taken, GPS coordinates) into images
- ✅ Writes creation time and GPS into video files
- ✅ Progressive JSON pruning (safe to Ctrl+C and resume)
- ✅ Fail-fast: Skips files with missing datetime metadata
- ✅ **Zero system dependencies**: Everything installs via pip!

## Prerequisites

- **Python 3.10+**

## Quick Start (All Platforms)

1. **Clone or download this repository**
   ```bash
   git clone git@github.com:Reelinq/snapchat-memories-extractor.git
   cd snapchat-memories-extractor
   ```

2. **Create Python virtual environment**

   **Windows (PowerShell):**
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

   **macOS/Linux:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install all dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Add your Snapchat export JSON**
   - Login and export your data from Snapchat: https://accounts.snapchat.com/accounts/downloadmydata
   - Select the `Export your Memories` and `Export JSON Files` option and continue

   ![export configuration](https://github.com/user-attachments/assets/dfcdb6a0-e554-46e8-bdba-77fe41c88a03)

   - Extract the ZIP and place `memories_history.json` into `data/` folder

5. **Run the downloader**
   ```bash
   python main.py
   ```

Your files will be saved to `downloads/` with full metadata embedded.

## Troubleshooting

### Download links expired
Snapchat download links expire after a period of time. If downloads fails, try to export a fresh `memories_history.json` from Snapchat and replace the old one in the `data/` folder.

### Missing `memories_history.json`
When exporting your data from Snapchat, make sure you select both:
- ✅ **Export your Memories**
- ✅ **Export JSON Files**

Without these options, the JSON file won't be included in your export.

### Still having issues?
Please open a new [issue](https://github.com/Reelinq/snapchat-memories-extractor/issues) with:
- Your Python version (`python --version`)
- Operating system
- Error message or unexpected behavior
- Whether the issue is with images or videos

## License

MIT License - feel free to use and modify as needed.
