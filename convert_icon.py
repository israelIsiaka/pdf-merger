#!/usr/bin/env python3
"""
Convert Logo.png to Logo.icns for macOS bundling
"""
import os
import subprocess
from PIL import Image

def convert_png_to_icns(png_path, icns_path):
    """Convert PNG to ICNS using PIL and macOS iconutil"""

    if not os.path.exists(png_path):
        print(f"Error: {png_path} not found")
        return False

    try:
        # Create temporary iconset directory
        iconset_dir = "/tmp/AppIcon.iconset"
        os.makedirs(iconset_dir, exist_ok=True)

        # Open the PNG
        img = Image.open(png_path)

        # Required sizes for macOS icons
        sizes = [16, 32, 64, 128, 256, 512, 1024]

        for size in sizes:
            resized = img.resize((size, size), Image.Resampling.LANCZOS)
            resized.save(f"{iconset_dir}/icon_{size}x{size}.png")

            resized_2x = img.resize((size * 2, size * 2), Image.Resampling.LANCZOS)
            resized_2x.save(f"{iconset_dir}/icon_{size}x{size}@2x.png")

        # Convert iconset to icns
        result = subprocess.run(
            ["iconutil", "-c", "icns", iconset_dir, "-o", icns_path],
            capture_output=True,
            text=True
        )

        # Cleanup
        subprocess.run(["rm", "-rf", iconset_dir])

        if result.returncode == 0:
            print(f"Successfully created {icns_path}")
            return True
        else:
            print(f"Error: {result.stderr}")
            return False

    except Exception as e:
        print(f"Error converting icon: {e}")
        return False

if __name__ == "__main__":
    png_file = "Logo.png"
    icns_file = "Logo.icns"

    if os.path.exists(png_file):
        convert_png_to_icns(png_file, icns_file)
    else:
        print(f"WARNING: {png_file} not found in current directory")
        print("Please add Logo.png to the project root and run this script again")
