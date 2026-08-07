from __future__ import annotations

import zipfile
from dataclasses import dataclass, field

MAX_ARCHIVE_MEMBERS = 10_000
MAX_ARCHIVE_MEMBER_BYTES = 64 * 1024 * 1024
MAX_ARCHIVE_EXPANDED_BYTES = 256 * 1024 * 1024
MAX_ARCHIVE_COMPRESSION_RATIO = 200
MAX_SPREADSHEET_ROWS = 500_000
MAX_SPREADSHEET_CELLS = 1_000_000
MAX_PDF_PAGES = 1_000
MAX_PDF_TEXT_BYTES = 16 * 1024 * 1024
_RATIO_CHECK_MIN_BYTES = 1024 * 1024
_READ_CHUNK_BYTES = 1024 * 1024


class DocumentLimitError(ValueError):
    pass


@dataclass
class ArchiveBudget:
    archive: zipfile.ZipFile
    _consumed: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        infos = self.archive.infolist()
        if len(infos) > MAX_ARCHIVE_MEMBERS:
            raise DocumentLimitError("DOCUMENT_ARCHIVE_MEMBER_LIMIT_EXCEEDED")
        names = [item.filename for item in infos]
        if len(names) != len(set(names)):
            raise DocumentLimitError("DOCUMENT_ARCHIVE_DUPLICATE_MEMBER")

    def read(self, name: str) -> bytes:
        info = self.archive.getinfo(name)
        if info.file_size > MAX_ARCHIVE_MEMBER_BYTES:
            raise DocumentLimitError("DOCUMENT_ARCHIVE_MEMBER_TOO_LARGE")
        if (
            info.file_size >= _RATIO_CHECK_MIN_BYTES
            and info.file_size / max(1, info.compress_size) > MAX_ARCHIVE_COMPRESSION_RATIO
        ):
            raise DocumentLimitError("DOCUMENT_ARCHIVE_COMPRESSION_RATIO_EXCEEDED")
        if self._consumed + info.file_size > MAX_ARCHIVE_EXPANDED_BYTES:
            raise DocumentLimitError("DOCUMENT_ARCHIVE_EXPANDED_SIZE_EXCEEDED")

        chunks: list[bytes] = []
        actual = 0
        with self.archive.open(info) as source:
            while chunk := source.read(_READ_CHUNK_BYTES):
                actual += len(chunk)
                if actual > MAX_ARCHIVE_MEMBER_BYTES:
                    raise DocumentLimitError("DOCUMENT_ARCHIVE_MEMBER_TOO_LARGE")
                if self._consumed + actual > MAX_ARCHIVE_EXPANDED_BYTES:
                    raise DocumentLimitError("DOCUMENT_ARCHIVE_EXPANDED_SIZE_EXCEEDED")
                chunks.append(chunk)
        self._consumed += actual
        return b"".join(chunks)
