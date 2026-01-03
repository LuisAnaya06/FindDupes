# File Comparer - Video Duplicate Analyzer

A powerful Python application for finding duplicate and similar video files using AI-powered fuzzy matching.

## Features

- 🔍 **Exact Duplicate Detection** - Uses SHA256 hashing to find identical files
- 🤖 **AI-Powered Similarity** - Fuzzy name matching to find similar files (even with different names)
- 📁 **Multi-Folder Analysis** - Compare multiple folders against each other
- 🎥 **Video File Focus** - Optimized for video files (MP4, AVI, MKV, MOV, M3U8, etc.)
- 🖼️ **Video Thumbnails** - Preview thumbnails for all video files (requires opencv-python)
- ▶️ **Quick Play** - Open videos in external player with one click
- ⏹️ **Stop Analysis** - Cancel long-running scans anytime
- 📊 **Smart Sorting** - Sort groups by size or similarity score
- 🗑️ **Safe Deletion** - Send files to Recycle Bin (not permanent deletion)
- 💾 **Save/Load Results** - Export and import analysis results
- 🎨 **Modern GUI** - Clean, dark-themed interface with CustomTkinter
- ⚙️ **Customizable Patterns** - Add your own regex patterns for filename normalization

## Installation

1. Install Python 3.8 or higher (Python 3.13 recommended for full features)

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. **(Optional)** Enable video thumbnails:
   - Requires Python 3.13 or lower
   - Uncomment the last two lines in `requirements.txt`
   - Run: `pip install numpy opencv-python`

## Usage

1. Run the application:
```bash
python main.py
```

2. Click "Add Folder" to select folders to analyze

3. Choose analysis type:
   - **Find Exact Duplicates** - Finds identical files
   - **Find Similar Files** - Finds files with similar names (adjust threshold slider)

4. Review results grouped by duplicates
   - Use the **Sort by** dropdown to organize groups:
     - **Size (Largest)** - See biggest duplicates first
     - **Size (Smallest)** - See smallest duplicates first
     - **Similarity (Highest)** - See most similar groups first
     - **Similarity (Lowest)** - See least similar groups first
   - Click **Play** button to open videos in your default player
   - Preview videos using thumbnails (if opencv installed)

5. Select files to delete using checkboxes

6. Click "Send Selected to Trash" to safely delete files

## Features Overview

### Exact Duplicate Detection
- Compares file content using SHA256 hashing
- Groups files by size first for optimization
- 100% accuracy for identical files

### Similar File Detection
- Uses advanced fuzzy string matching (RapidFuzz)
- Intelligent filename normalization removes quality tags, codecs, years, etc.
- Multi-factor scoring: normalized names (50%), original names (20%), file size (30%)
- Adjustable similarity threshold (50-100%)
- Great for finding renamed files or variations

### Advanced Filename Normalization
The app intelligently cleans filenames before comparison by removing:
- Resolution markers (1080p, 720p, 4K, etc.)
- Source types (BluRay, WEBRip, DVDRip, etc.)
- Codecs (x264, x265, HEVC, etc.)
- Audio formats (AAC, DTS, 5.1, etc.)
- Release groups (YIFY, RARBG, etc.)
- Years, brackets, and metadata

**Customization:** Edit `filename_patterns.py` to add your own regex patterns! See the file for detailed documentation and examples.

### Safe Deletion
- Uses `send2trash` library
- Files go to Recycle Bin
- Can be recovered if deleted by mistake

### Export/Import
- Save analysis results as JSON
- Load previous results without re-scanning
- Share results with others

## Requirements

### Core Dependencies (Required)
- Python 3.8+ (Python 3.13 recommended for thumbnail support)
- customtkinter 5.2.2+
- send2trash 1.8.3+
- rapidfuzz 3.6.1+
- Pillow 10.2.0+

### Optional Dependencies (For Thumbnails)
- opencv-python 4.12.0+
- numpy <2 (required by opencv)

**Note:** Thumbnail generation requires Python 3.13 or lower (Python 3.14+ not yet supported due to numpy/opencv compatibility)

## Video Formats Supported

MP4, AVI, MKV, MOV, WMV, FLV, WEBM, M4V, MPEG, MPG, 3GP, F4V, TS, M3U8

**Thumbnail support:** All formats supported by OpenCV/ffmpeg (MP4, MKV, M4V, TS, WEBM, M3U8, etc.)

## Tips

- Use exact duplicate detection first for fastest results
- Adjust similarity threshold for similar files (80% is recommended)
- Select folders at the root level to scan all subfolders
- Click on video thumbnails or use the play button to preview files
- Use the stop button to cancel long scans
- Sort groups by "Size (Largest)" to find space-wasting duplicates quickly
- Sort groups by "Similarity (Highest)" to review the most confident matches first
- Save results before closing to review later
- Install opencv-python for thumbnail previews (requires Python 3.13 or lower)

## Customizing Filename Patterns

The app uses regex patterns to normalize filenames before comparing them. You can customize these patterns without modifying the core code:

### Quick Start:

1. **Copy the template:**
   ```bash
   # Windows
   copy filename_patterns.py filename_patterns_custom.py
   
   # Linux/Mac
   cp filename_patterns.py filename_patterns_custom.py
   ```

2. **Edit your custom file:**
   Open `filename_patterns_custom.py` and modify the patterns

3. **Restart the app** - Your custom patterns will be used automatically

### Why This Approach?

- ✅ Your custom patterns stay **private** (not pushed to git)
- ✅ You can update from the repo without losing your customizations
- ✅ App works fine without custom file (uses defaults)
- ✅ Easy to test and revert changes

### Adding Custom Patterns:

**Example - Adding custom release groups:**
```python
RELEASE_GROUP_PATTERNS = [
    r'\b(sample|rarbg|yts|yify|etrg)\b',
    r'\b(YourGroup|AnotherGroup)\b',  # Add your groups here
]
```

**Example - Removing file sizes:**
```python
CUSTOM_PATTERNS = [
    r'\b\d+(\.\d+)?(gb|mb|kb)\b',  # Removes 2.5GB, 700MB
]
```

**Testing your patterns:**
1. Visit https://regex101.com (select Python flavor)
2. Test your patterns with sample filenames
3. Copy working patterns to `filename_patterns_custom.py`

See `filename_patterns.py` for complete documentation and more examples.

## License

MIT License
