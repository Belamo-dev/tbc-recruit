from pydantic import BaseModel, Field
from typing import List, Dict, Literal, Optional

Faction = Literal["Alliance", "Horde"]
Role = Literal["DPS", "Tank", "Heal"]

class GuildNeed(BaseModel):
    class_name: str = Field(alias="class", min_length=2, max_length=32)
    spec: str = Field(min_length=0, max_length=32, default="")
    role: Role
    prio: int = Field(ge=1, le=5, default=3)

    class Config:
        populate_by_name = True

class GuildCreate(BaseModel):
    name: str = Field(min_length=2, max_length=64)
    realm: str = Field(min_length=2, max_length=64)
    faction: Faction
    language: str = Field(default="DE", max_length=16)

    raid_days: List[str] = Field(default_factory=list)
    raid_time_start: str = Field(default="20:00", max_length=8)
    raid_time_end: str = Field(default="23:00", max_length=8)

    progress: Dict[str, str] = Field(default_factory=dict)
    needs: List[dict] = Field(default_factory=list)  # wir akzeptieren dict fuer einfache Frontend integration

    loot_system: str = Field(default="Loot Council", max_length=64)
    contact_character: str = Field(default="", max_length=64)
    discord: str = Field(default="", max_length=256)
    website: str = Field(default="", max_length=256)
    description: str = Field(default="", max_length=4000)

class GuildOut(BaseModel):
    id: int
    name: str
    realm: str
    faction: str
    language: str
    raid_days: List[str]
    raid_time_start: str
    raid_time_end: str
    progress: Dict[str, str]
    needs: List[dict]
    loot_system: str
    contact_character: str
    discord: str
    website: str
    description: str

class GuildCreated(BaseModel):
    guild: GuildOut
    edit_token: str


class PlayerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=64)
    realm: str = Field(min_length=2, max_length=64)
    faction: Faction
    language: str = Field(default="DE", max_length=16)

    class_name: str = Field(min_length=2, max_length=32)
    spec: str = Field(min_length=2, max_length=32)
    role: Role

    skill_rating: int = Field(default=3, ge=1, le=5)
    professions: List[str] = Field(default_factory=list)
    attunements: List[str] = Field(default_factory=list)
    availability: List[str] = Field(default_factory=list)

    logs_url: str = Field(default="", max_length=256)
    note: str = Field(default="", max_length=4000)

class PlayerOut(BaseModel):
    id: int
    name: str
    realm: str
    faction: str
    language: str
    class_name: str
    spec: str
    role: str
    skill_rating: int
    professions: List[str]
    attunements: List[str]
    availability: List[str]
    logs_url: str
    note: str

class PlayerCreated(BaseModel):
    player: PlayerOut
    edit_token: str


class ApplicationCreate(BaseModel):
    guild_id: int
    player_id: int
    message: str = Field(default="", max_length=4000)

class ApplicationOut(BaseModel):
    id: int
    guild_id: int
    player_id: int
    message: str
    status: str
    created_at: str

class ImportRequest(BaseModel):
    exportString: str


class ImportSummary(BaseModel):
    guid: Optional[str] = None
    name: str
    realm: str
    level: Optional[int] = None
    classFile: Optional[str] = None
    raceFile: Optional[str] = None
    faction: Optional[str] = None
    guildName: Optional[str] = None
    exportedAt: Optional[str] = None
