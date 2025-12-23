# Professional PDF Unredactor & Viewer (GUI)

A sophisticated, standalone GUI application used to recover underlying text from redacted PDF files. This tool creates a new "unredacted" layer over the original document, allowing you to see text that was covered by black boxes (provided the text data was not scrubbed from the file).

## 🚀 Features

### 🛠 Processing Dashboard
* **Batch Processing:** Queue multiple individual files or entire folders at once.
* **Recursive Scan:** Option to scan subdirectories for all `.pdf` files.
* **Dual Modes:**
    * **Side-by-Side:** Creates a page twice as wide, showing the original redaction on the left and the revealed text on the right.
    * **Overlay (White Text):** Writes the recovered text in white directly over the black redaction boxes on the original page.
* **Live Logging:** Real-time status updates and error reporting within the dashboard.

### 👁️ Integrated Results Viewer
* **Built-in PDF Viewer:** Review processed files immediately without leaving the app.
* **Collapsible Sidebar:** Animated file browser that can be hidden for maximum viewing area.
* **Navigation Controls:** Zoom In/Out, Fit to Width, and Page Navigation.
* **Fullscreen Mode:** Press `F11` or the Fullscreen button for a distraction-free look.
* **Independent Browsing:** Browse any folder on your system, not just the output directory.

### 🎨 Customization
* **Theme Engine:** Choose from 6 professional themes including Professional White, Soft Vanilla, Soft Sky, and more.
* **High DPI Support:** Clean, flat "Metro-style" interface with crisp borders.

## 📦 Installation

This application requires **Python 3.x** and two external libraries.

1.  **Clone or Download** this repository.
2.  **Install Dependencies:**
    ```bash
    pip install pdfplumber pymupdf
    ```
    *(Note: `tkinter` usually comes pre-installed with Python. If you are on Linux, you may need to install `python3-tk`)*.

##  ▶️ Usage

Simply run the script via Python:

```bash
python unredact_app.py

    Go to the Dashboard tab.

    Click + Add Files or + Add Folder.

    Select an Output Location.

    Choose your mode (Side-by-Side is recommended for verification).

    Click Run Batch Process.

    Once finished, the app will automatically switch to the Results Viewer tab to display your files.

⚠️ Disclaimer

This tool relies on metadata and underlying text layers remaining in the PDF. If a PDF was "flattened" as an image (rasterized) or properly sanitized using professional redaction software that removes the text layer, this tool will not be able to recover the text. It only works on redactions that were applied as cosmetic annotations over searchable text.
🤝 Credits

    GUI & Enhancements: Created by KingBarker

    Core Logic & Original Concept: Leedrake5
