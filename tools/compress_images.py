#!/usr/bin/env python3
"""
compress_images.py

Simple utility to compress images in a folder to a target file size (approximate).
Uses Pillow (PIL). It will try lowering JPEG quality and scaling down dimensions until
the saved image is smaller than the requested target_kb or hits minimum quality/dimensions.

Usage:
  python3 tools/compress_images.py --dir frontend/uploads --target-kb 8

Options:
  --dir         Directory to scan for images (default: frontend/uploads)
  --target-kb   Target maximum file size in KB (default: 8)
  --dry-run     Don't overwrite files, only show what would be done
  --backup      Keep a .bak copy of original files before overwriting

Note: Install Pillow if not present:
  pip install pillow

"""

import argparse
import io
import os
import sys
from pathlib import Path

try:
    from PIL import Image
except Exception:
    print("Pillow is required for this script. Install it with: pip install pillow")
    sys.exit(1)

# Supported image extensions
IMG_EXTS = {'.jpg', '.jpeg', '.png', '.webp'}


def compress_image(path: Path, target_kb: int = 8, dry_run: bool = False, backup: bool = False) -> dict:
    """Compress a single image file so its size is approximately <= target_kb.

    Returns a dict with result info.
    """
    target_bytes = target_kb * 1024
    original_size = path.stat().st_size

    info = {
        'path': str(path),
        'original_size': original_size,
        'final_size': original_size,
        'was_compressed': False,
        'skipped': False,
        'reason': None,
    }

    if original_size <= target_bytes:
        info['skipped'] = True
        info['reason'] = 'already_small'
        return info

    try:
        with Image.open(path) as im:
            # Convert PNG/others to RGB JPEG to get much better compression in many cases
            mode = im.mode
            has_alpha = 'A' in mode or (mode == 'P' and 'transparency' in im.info)

            # Work on a copy in memory
            work_im = im.convert('RGBA') if has_alpha else im.convert('RGB')

            # Initial guess parameters
            quality = 85
            min_quality = 20
            scale = 1.0
            min_width = 200
            min_height = 200

            # Progressive approach: try decreasing quality first, then scale down, loop until size <= target
            last_good = None

            for iteration in range(20):
                # Prepare image to save: if it has alpha, paste onto white background
                if work_im.mode == 'RGBA':
                    bg = Image.new('RGB', work_im.size, (255, 255, 255))
                    bg.paste(work_im, mask=work_im.split()[3])
                    save_im = bg
                else:
                    save_im = work_im.convert('RGB')

                # Resize if scale < 1.0
                if scale < 0.999:
                    new_w = max(int(save_im.width * scale), 1)
                    new_h = max(int(save_im.height * scale), 1)
                    save_candidate = save_im.resize((new_w, new_h), Image.LANCZOS)
                else:
                    save_candidate = save_im

                buf = io.BytesIO()
                # Save as JPEG for compression effectiveness
                save_candidate.save(buf, format='JPEG', quality=quality, optimize=True)
                size = buf.tell()

                # If within target, write out
                if size <= target_bytes or (quality <= min_quality and (save_candidate.width <= min_width or save_candidate.height <= min_height)):
                    info['final_size'] = size
                    info['was_compressed'] = True
                    # Persist to disk unless dry_run
                    if not dry_run:
                        if backup:
                            bak = path.with_suffix(path.suffix + '.bak')
                            if not bak.exists():
                                path.rename(bak)
                                # after renaming, write to original path
                                out_path = path
                            else:
                                # if bak exists, don't overwrite it
                                out_path = path
                        else:
                            out_path = path

                        # Ensure parent dir exists
                        out_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(out_path, 'wb') as f:
                            f.write(buf.getvalue())
                    return info

                # Not small enough: reduce quality or scale
                # Prefer to reduce quality down to min_quality first
                if quality > min_quality:
                    quality = max(min_quality, int(quality * 0.8))
                else:
                    # reduce dimensions
                    scale *= 0.85
                    if save_candidate.width * scale < min_width or save_candidate.height * scale < min_height:
                        # give up and save current candidate at min_quality
                        quality = min_quality

                last_good = (size, quality, scale)

            # If loop exits without success, save last tried with min settings
            if last_good:
                # write last buffer (we still have buf from last iteration)
                info['final_size'] = buf.tell()
                info['was_compressed'] = True
                if not dry_run:
                    if backup:
                        bak = path.with_suffix(path.suffix + '.bak')
                        if not bak.exists():
                            path.rename(bak)
                            out_path = path
                        else:
                            out_path = path
                    else:
                        out_path = path
                    with open(out_path, 'wb') as f:
                        f.write(buf.getvalue())
                return info

    except Exception as e:
        info['reason'] = f'error:{e}'
        return info

    return info


def compress_folder(folder: Path, target_kb: int = 8, dry_run: bool = False, backup: bool = False):
    results = []
    for root, _, files in os.walk(folder):
        for fn in files:
            p = Path(root) / fn
            if p.suffix.lower() in IMG_EXTS:
                res = compress_image(p, target_kb=target_kb, dry_run=dry_run, backup=backup)
                results.append(res)
                print(f"{p}: {res.get('original_size')} -> {res.get('final_size')} (skipped={res.get('skipped')})")
    return results


def main():
    parser = argparse.ArgumentParser(description='Compress images in a folder to target KB size')
    parser.add_argument('--dir', default='frontend/uploads', help='Directory to scan')
    parser.add_argument('--target-kb', type=int, default=8, help='Target size in KB')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--backup', action='store_true')
    args = parser.parse_args()

    folder = Path(args.dir)
    if not folder.exists():
        print(f"Directory {folder} does not exist")
        sys.exit(1)

    print(f"Compressing images in {folder} to ~{args.target_kb}KB (dry_run={args.dry_run}, backup={args.backup})")
    results = compress_folder(folder, target_kb=args.target_kb, dry_run=args.dry_run, backup=args.backup)
    total_before = sum(r.get('original_size', 0) for r in results)
    total_after = sum(r.get('final_size', 0) for r in results)
    print('Done. Total before:', total_before, 'after:', total_after)


if __name__ == '__main__':
    main()
