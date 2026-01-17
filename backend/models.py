from datetime import datetime
from sqlalchemy import Text, String, Integer, BigInteger, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.sql import func

from db import Base

class Guild(Base):
    __tablename__ = "guilds"
    __table_args__ = (
        UniqueConstraint("name", "realm", "faction", name="uq_guild_name_realm_faction"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    edit_token: Mapped[str] = mapped_column(String(80), index=True)

    name: Mapped[str] = mapped_column(String(64), index=True)
    realm: Mapped[str] = mapped_column(String(64), index=True)
    faction: Mapped[str] = mapped_column(String(16), index=True)     # Alliance/Horde
    language: Mapped[str] = mapped_column(String(16), index=True)    # DE/EN

    raid_days: Mapped[list[str]] = mapped_column(ARRAY(String(8)), default=list)
    raid_time_start: Mapped[str] = mapped_column(String(8), default="20:00")
    raid_time_end: Mapped[str] = mapped_column(String(8), default="23:00")

    progress: Mapped[dict] = mapped_column(JSONB, default=dict)      # {"SSC":"4/6","TK":"3/4"}
    needs: Mapped[list] = mapped_column(JSONB, default=list)         # [{"class":"Warrior","spec":"Fury","role":"DPS","prio":3}]

    loot_system: Mapped[str] = mapped_column(String(64), default="Loot Council")
    contact_character: Mapped[str] = mapped_column(String(64), default="")
    discord: Mapped[str] = mapped_column(String(256), default="")
    website: Mapped[str] = mapped_column(String(256), default="")
    description: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    applications: Mapped[list["Application"]] = relationship(back_populates="guild", cascade="all, delete-orphan")


class Player(Base):
    __tablename__ = "players"
    __table_args__ = (
        UniqueConstraint("name", "realm", name="uq_player_name_realm"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    edit_token: Mapped[str] = mapped_column(String(80), index=True)

    name: Mapped[str] = mapped_column(String(64), index=True)
    realm: Mapped[str] = mapped_column(String(64), index=True)
    faction: Mapped[str] = mapped_column(String(16), index=True)
    language: Mapped[str] = mapped_column(String(16), index=True)

    class_name: Mapped[str] = mapped_column(String(32), index=True)
    spec: Mapped[str] = mapped_column(String(32), index=True)
    role: Mapped[str] = mapped_column(String(16), index=True)        # DPS/Tank/Heal

    skill_rating: Mapped[int] = mapped_column(Integer, default=3, index=True)  # 1..5
    professions: Mapped[list[str]] = mapped_column(ARRAY(String(32)), default=list)
    attunements: Mapped[list[str]] = mapped_column(ARRAY(String(32)), default=list)
    availability: Mapped[list[str]] = mapped_column(ARRAY(String(8)), default=list)

    logs_url: Mapped[str] = mapped_column(String(256), default="")
    note: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    applications: Mapped[list["Application"]] = relationship(back_populates="player", cascade="all, delete-orphan")


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("guild_id", "player_id", name="uq_application_guild_player"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    guild_id: Mapped[int] = mapped_column(Integer, ForeignKey("guilds.id"), index=True)
    player_id: Mapped[int] = mapped_column(Integer, ForeignKey("players.id"), index=True)

    message: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending/accepted/rejected

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    guild: Mapped[Guild] = relationship(back_populates="applications")
    player: Mapped[Player] = relationship(back_populates="applications")

class CharacterImport(Base):
    __tablename__ = "character_imports"
    __table_args__ = (
        UniqueConstraint("name", "realm", name="uq_character_import_name_realm"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    guid: Mapped[str | None] = mapped_column(Text, unique=True, nullable=True)

    name: Mapped[str] = mapped_column(String(64), index=True)
    realm: Mapped[str] = mapped_column(String(64), index=True)

    level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    class_file: Mapped[str | None] = mapped_column(String(32), nullable=True)
    race_file: Mapped[str | None] = mapped_column(String(32), nullable=True)
    faction: Mapped[str | None] = mapped_column(String(16), nullable=True)
    guild_name: Mapped[str | None] = mapped_column(String(64), nullable=True)

    exported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
