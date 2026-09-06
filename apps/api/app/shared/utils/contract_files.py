from hashlib import sha256
from pathlib import Path

MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024
ATTACHMENT_TYPES = {
    ".pdf": ("application/pdf", b"%PDF-"),
    ".docx": (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        b"PK\x03\x04",
    ),
    ".png": ("image/png", b"\x89PNG\r\n\x1a\n"),
    ".jpg": ("image/jpeg", b"\xff\xd8\xff"),
    ".jpeg": ("image/jpeg", b"\xff\xd8\xff"),
}


def attachment_metadata(filename: str, content: bytes) -> tuple[str, str]:
    name = Path(filename.replace("\\", "/")).name
    name = "".join(char for char in name if char.isprintable()).strip()
    if not name or len(name) > 255:
        raise ValueError("A filename of 1 to 255 characters is required")
    kind = ATTACHMENT_TYPES.get(Path(name).suffix.lower())
    if not kind or not content.startswith(kind[1]):
        raise ValueError("Attach a PDF, DOCX, PNG or JPEG file")
    return name, kind[0]


def attachment_path(root: str, tenant_id: str, document_id: str) -> Path:
    tenant_folder = sha256(tenant_id.encode()).hexdigest()
    storage_root = Path(root).resolve()
    path = (storage_root / tenant_folder / document_id).resolve()
    if path.parent != storage_root / tenant_folder:
        raise ValueError("Invalid attachment path")
    return path


def write_attachment(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as target:
        try:
            target.write(content)
        except OSError:
            path.unlink(missing_ok=True)
            raise
