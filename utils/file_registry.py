"""에이전트 실행 중 생성된 결과 파일을 추적하는 레지스트리."""
from pathlib import Path

_created_files: list[Path] = []


def reset() -> None:
    _created_files.clear()


def register(path) -> Path:
    p = Path(path)
    if p not in _created_files:
        _created_files.append(p)
    return p


def get_all() -> list[Path]:
    return list(_created_files)
