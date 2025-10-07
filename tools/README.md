Image compression helper

This folder contains `compress_images.py`, a script that compresses images in a folder to an approximate target size.

Requirements
- Python Pillow: pip install pillow

Example usage

```bash
python3 tools/compress_images.py --dir frontend/uploads --target-kb 8 --backup
```

Notes
- The script converts images to JPEG for better compression. PNGs with transparency are flattened onto white.
- Use `--dry-run` to see what would change without overwriting files.
- Use `--backup` to keep a `.bak` copy of each original file before overwriting.
