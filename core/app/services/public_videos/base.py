from __future__ import annotations

from dataclasses import dataclass
from typing import List, Protocol, Optional
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(slots=True)
class PublicVideoRecord:
    video_id: str
    title: str
    first_name: str
    last_name: str
    city: Optional[str]
    processed_path: Optional[str]
    votes: int

    @property
    def username(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


@dataclass(slots=True)
class RankingRecord:
    username: str
    city: Optional[str]
    votes: int


class PublicVideoServicePort(Protocol):
    async def list_videos(
        self,
        *,
        city: Optional[str],
        limit: int,
        offset: int,
        db: AsyncSession,
    ) -> List[PublicVideoRecord]:
        ...

    async def get_video(
        self,
        *,
        video_id: str,
        db: AsyncSession,
    ) -> PublicVideoRecord:
        ...

    async def register_vote(
        self,
        *,
        video_id: str,
        user_id: str,
        db: AsyncSession,
    ) -> None:
        ...

    async def get_rankings(
        self,
        *,
        city: Optional[str],
        limit: int,
        db: AsyncSession,
    ) -> List[RankingRecord]:
        ...
