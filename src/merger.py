"""
PDF Merger core logic.
Handles PDF merging operations with error handling.
"""
import os
from pathlib import Path
from typing import List, Tuple
from pypdf import PdfWriter


class PDFMerger:
    """Handles PDF merging operations."""
    
    def __init__(self):
        self.pdf_files: List[str] = []
    
    def add_file(self, filepath: str) -> bool:
        """Add a PDF file to the merge list."""
        if filepath not in self.pdf_files and os.path.isfile(filepath):
            self.pdf_files.append(filepath)
            return True
        return False
    
    def add_files(self, filepaths: List[str]) -> int:
        """Add multiple PDF files. Returns count of added files."""
        added = 0
        for filepath in filepaths:
            if self.add_file(filepath):
                added += 1
        return added
    
    def add_folder(self, folder_path: str) -> int:
        """Add all PDF files from a folder. Returns count of added files."""
        if not os.path.isdir(folder_path):
            return 0
        
        added = 0
        for filename in sorted(os.listdir(folder_path)):
            if filename.lower().endswith(".pdf"):
                filepath = os.path.join(folder_path, filename)
                if self.add_file(filepath):
                    added += 1
        return added
    
    def remove_file(self, index: int) -> bool:
        """Remove a file by index."""
        if 0 <= index < len(self.pdf_files):
            self.pdf_files.pop(index)
            return True
        return False
    
    def move_file_up(self, index: int) -> bool:
        """Move a file up in the list."""
        if 0 < index < len(self.pdf_files):
            self.pdf_files[index - 1], self.pdf_files[index] = \
                self.pdf_files[index], self.pdf_files[index - 1]
            return True
        return False
    
    def move_file_down(self, index: int) -> bool:
        """Move a file down in the list."""
        if 0 <= index < len(self.pdf_files) - 1:
            self.pdf_files[index + 1], self.pdf_files[index] = \
                self.pdf_files[index], self.pdf_files[index + 1]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all files."""
        self.pdf_files.clear()
    
    def get_file_count(self) -> int:
        """Get total number of files."""
        return len(self.pdf_files)
    
    def get_filenames(self) -> List[str]:
        """Get list of filenames (not full paths)."""
        return [os.path.basename(path) for path in self.pdf_files]
    
    def merge(self, output_path: str) -> Tuple[bool, str]:
        """
        Merge PDF files to output path.
        Returns (success: bool, message: str)
        """
        if not self.pdf_files:
            return False, "No PDF files to merge."
        
        if not output_path or not output_path.strip():
            return False, "No output path specified."
        
        try:
            writer = PdfWriter()
            errors = []
            
            for filepath in self.pdf_files:
                try:
                    writer.append(filepath)
                except Exception as e:
                    errors.append((os.path.basename(filepath), str(e)))
            
            # Write output
            with open(output_path, "wb") as f:
                writer.write(f)
            
            # Prepare message
            total = len(self.pdf_files)
            successful = total - len(errors)
            message = f"Successfully merged {successful} of {total} files."
            
            if errors:
                error_details = "\n".join([f"  • {name}: {err}" for name, err in errors])
                message += f"\n\nSkipped {len(errors)} file(s):\n{error_details}"
            
            return True, message
        
        except Exception as e:
            return False, f"Failed to merge PDFs: {str(e)}"
