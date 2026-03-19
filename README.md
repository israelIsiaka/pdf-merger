# PDF Merger

A simple desktop app to merge multiple PDF files into one. Works on Mac and Windows.

## Features

- Add individual PDFs or an entire folder
- Reorder files before merging
- Live progress bar
- Skips corrupted files without crashing

## Run locally

```bash
pip install pypdf
python merge_pdfs.py
```

## Build a standalone app

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "PDF Merger" merge_pdfs.py
```

Run on Mac to get a `.app`, run on Windows to get a `.exe`.
