#!/usr/bin/env python3
"""
Convert Logo.png to Logo.ico for Windows applications
This creates a Windows .ico icon file suitable for installers and executables
"""

import os
from PIL import Image

def create_ico():
    """Convert Logo.png to Logo.ico"""
    
    input_path = "Logo.png"
    output_path = "Logo.ico"
    
    if not os.path.exists(input_path):
        print(f"❌ Error: {input_path} not found")
        return False
    
    try:
        print(f"🔄 Converting {input_path} to {output_path}...")
        
        # Open the PNG image
        img = Image.open(input_path)
        
        # Convert to RGB if it has alpha channel (RGBA or RGBA with transparency)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Create a white background
            bg = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            bg.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = bg
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize to standard icon sizes (Windows accepts multiple sizes in one .ico file)
        # Create different sizes for best quality at different scales
        sizes = [(16, 16), (32, 32), (64, 64), (128, 128), (256, 256)]
        icon_images = []
        
        for size in sizes:
            # Use high-quality resampling
            resized = img.resize(size, Image.Resampling.LANCZOS)
            icon_images.append(resized)
        
        # Save as .ico with all sizes
        icon_images[0].save(
            output_path,
            format='ICO',
            sizes=sizes
        )
        
        print(f"✅ Successfully created {output_path}")
        print(f"   Sizes: {', '.join([f'{s[0]}x{s[1]}' for s in sizes])}")
        return True
        
    except Exception as e:
        print(f"❌ Error converting image: {e}")
        return False

if __name__ == "__main__":
    create_ico()
