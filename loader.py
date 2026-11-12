import io
import subprocess
import sys
import zipfile
from pathlib import Path

SUPPORTED = (".pdf", ".docx")


class NamedFile(io.BytesIO):
    """In-memory resume file that behaves like an uploaded file (has a .name)."""

    def __init__(self, data, name):
        super().__init__(data)
        self.name = name


def files_from_folder(folder, include_subfolders=False):
    """Read every PDF and Word (.docx) resume in a local folder."""
    path = Path(folder.strip().strip('"'))
    if not path.is_dir():
        raise FileNotFoundError(f"Folder not found: {path}")
    items = path.rglob("*") if include_subfolders else path.iterdir()
    found = sorted(p for p in items if p.is_file() and p.suffix.lower() in SUPPORTED
                   and not p.name.startswith("~$"))
    return [NamedFile(p.read_bytes(), p.name) for p in found]


def files_from_zip(uploaded_zip):
    """Read every PDF and Word (.docx) resume inside an uploaded ZIP file."""
    found = []
    with zipfile.ZipFile(uploaded_zip) as zf:
        for info in zf.infolist():
            name = info.filename
            if (info.is_dir() or "__MACOSX" in name or not name.lower().endswith(SUPPORTED)
                    or Path(name).name.startswith("~$")):
                continue
            found.append(NamedFile(zf.read(info), Path(name).name))
    return found


_PICKER = (
    "import tkinter as tk\n"
    "from tkinter import filedialog\n"
    "r = tk.Tk(); r.withdraw(); r.attributes('-topmost', True)\n"
    "print(filedialog.askdirectory(title='Select the folder with resumes'))\n"
)


def browse_folder():
    """Open Windows' folder picker. Works because the app runs on your own computer."""
    try:
        out = subprocess.run([sys.executable, "-c", _PICKER],
                             capture_output=True, text=True, timeout=300)
        return out.stdout.strip()
    except Exception:
        return ""