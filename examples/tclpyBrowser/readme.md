# TCLpy Browser (`tclpyBrowser`)

A lightweight, scriptable web content extraction and audio reader utility built on a dual-engine architecture: Python handles networking, parsing, and rendering primitives, while Tcl manages the UI layout, bookmarks, and scriptable rules.

## Architecture

`tclpyBrowser` avoids heavy browser bloat by focusing entirely on content, text extraction, and automation utilities:

* **Python Core (`engine.py`)**: Manages the Tkinter window hierarchy, secure HTTPS requests, base64 image decoding, HTML text stripping, and `gTTS` (Google Text-to-Speech) audio generation.
* **Tcl UI Layer (`browser.tcl`)**: Drives toolbar structures, quick-link button creation, and event bindings.
* **Modular Scripts (`scripts/`)**: Separates configuration data like bookmarks (`bookmarks.tcl`) and request validation rules (`network.tcl`).

## File Structure

```text
tclpyBrowser/
│
├── engine.py           # Python core runtime, GUI, networking, and Tcl bridge
├── browser.tcl         # Tcl UI layout and component initialization
└── scripts/
    ├── bookmarks.tcl   # Managed quick-link collections
    └── network.tcl     # Request interceptor and rule hooks

```

## Key Features

* **Dual-Engine Bridge**: Exposes Python primitives (`navigate`, `get_url`, `set_url`, `read_aloud`) directly into the Tcl interpreter via `tclpy`.
* **Clean HTML Extraction**: Strips out noisy markup tags (`script`, `style`, `head`) using a custom Python parser to present readable text payloads.
* **Base64 Image Rendering**: Handles raw image streams dynamically via Tkinter PhotoImage references.
* **Text-to-Speech (gTTS)**: Converts extracted webpage text into playable MP3 audio summaries (`page_summary.mp3`) on demand.
* **Modular Scripting**: Easily extendable via Tcl script files for custom automation and workflow rules.

## Quick Start

1. Ensure you have Python and `tclpy` installed in your environment.
2. Navigate to the `tclpyBrowser` directory.
3. Launch the application:

```powershell
python engine.py

```