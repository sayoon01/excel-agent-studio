"""채팅 세션 데이터클래스 — 대화 저장·마크다운 내보내기."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path("outputs")


@dataclass
class ChatSession:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = "새 채팅"
    messages: list = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_markdown(self) -> str:
        lines = [
            f"# {self.title}",
            f"> {self.created_at[:19].replace('T', ' ')}",
            "",
            "---",
            "",
        ]
        for msg in self.messages:
            role = "User" if msg.get("role") == "user" else "AI"
            lines += [f"### {role}", "", msg.get("content", ""), ""]
            if msg.get("code_output"):
                lines += [f"```\n{msg['code_output']}\n```", ""]
            lines += ["---", ""]
        return "\n".join(lines)

    def save_as_md(self, filename: str | None = None) -> Path:
        OUTPUT_DIR.mkdir(exist_ok=True)
        if not filename:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chat_{self.id}_{ts}.md"
        path = OUTPUT_DIR / filename
        path.write_text(self.to_markdown(), encoding="utf-8")
        return path
