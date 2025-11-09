from __future__ import annotations

from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.video import Video, VideoStatus
from app.models.vote import Vote
from app.services.public_videos.base import (
    PublicVideoServicePort,
    PublicVideoRecord,
    RankingRecord,
)


class PublicVideoService(PublicVideoServicePort):
    async def list_videos(
        self,
        *,
        city: Optional[str],
        limit: int,
        offset: int,
        db: AsyncSession,
    ) -> List[PublicVideoRecord]:
        stmt = (
            select(
                Video.id,
                Video.title,
                Video.player_first_name,
                Video.player_last_name,
                Video.player_city,
                Video.processed_path,
                func.count(Vote.id).label("votes_count"),
            )
            .outerjoin(Vote, Vote.video_id == Video.id)
            .where(Video.status == VideoStatus.processed)
            .group_by(
                Video.id,
                Video.title,
                Video.player_first_name,
                Video.player_last_name,
                Video.player_city,
                Video.processed_path,
            )
            .order_by(func.count(Vote.id).desc())
            .limit(limit)
            .offset(offset)
        )

        if city:
            stmt = stmt.where(Video.player_city.ilike(f"%{city}%"))

        result = await db.execute(stmt)
        rows = result.all()

        return [
            PublicVideoRecord(
                video_id=str(row.id),
                title=row.title,
                first_name=row.player_first_name or "",
                last_name=row.player_last_name or "",
                city=row.player_city,
                processed_path=row.processed_path,
                votes=row.votes_count or 0,
            )
            for row in rows
        ]

    async def get_video(
        self,
        *,
        video_id: str,
        db: AsyncSession,
    ) -> PublicVideoRecord:
        stmt = (
            select(
                Video.id,
                Video.title,
                Video.player_first_name,
                Video.player_last_name,
                Video.player_city,
                Video.processed_path,
                func.count(Vote.id).label("votes_count"),
            )
            .outerjoin(Vote, Vote.video_id == Video.id)
            .where(Video.id == video_id)
            .where(Video.status == VideoStatus.processed)
            .group_by(
                Video.id,
                Video.title,
                Video.player_first_name,
                Video.player_last_name,
                Video.player_city,
                Video.processed_path,
            )
        )

        result = await db.execute(stmt)
        row = result.one_or_none()

        if not row:
            raise HTTPException(
                status_code=404,
                detail="Video no encontrado o no está disponible públicamente",
            )

        return PublicVideoRecord(
            video_id=str(row.id),
            title=row.title,
            first_name=row.player_first_name or "",
            last_name=row.player_last_name or "",
            city=row.player_city,
            processed_path=row.processed_path,
            votes=row.votes_count or 0,
        )

    async def register_vote(
        self,
        *,
        video_id: str,
        user_id: str,
        db: AsyncSession,
    ) -> None:
        result = await db.execute(select(Video).where(Video.id == video_id))
        video = result.scalar_one_or_none()

        if not video:
            raise HTTPException(status_code=404, detail="Video no encontrado")

        if video.status != VideoStatus.processed:
            raise HTTPException(
                status_code=400,
                detail="Solo se puede votar por videos procesados",
            )

        existing = await db.execute(
            select(Vote).where(
                Vote.user_id == user_id,
                Vote.video_id == video_id,
            )
        )

        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Ya has votado por este video")

        try:
            vote = Vote(user_id=user_id, video_id=video_id)
            db.add(vote)
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(status_code=400, detail="Ya has votado por este video") from None

    async def get_rankings(
        self,
        *,
        city: Optional[str],
        limit: int,
        db: AsyncSession,
    ) -> List[RankingRecord]:
        stmt = (
            select(
                Video.player_first_name,
                Video.player_last_name,
                Video.player_city,
                func.count(Vote.id).label("total_votes"),
            )
            .join(Vote, Vote.video_id == Video.id)
            .where(Video.status == VideoStatus.processed)
            .group_by(
                Video.player_first_name,
                Video.player_last_name,
                Video.player_city,
            )
            .order_by(func.count(Vote.id).desc())
            .limit(limit)
        )

        if city:
            stmt = stmt.where(Video.player_city == city)

        result = await db.execute(stmt)
        rows = result.all()

        return [
            RankingRecord(
                username=f"{row.player_first_name or ''} {row.player_last_name or ''}".strip(),
                city=row.player_city,
                votes=row.total_votes or 0,
            )
            for row in rows
        ]
