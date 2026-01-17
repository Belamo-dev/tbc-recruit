import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Set

from fastapi import FastAPI, Depends, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import insert

from import_wpe import decode_export_string, summarize_payload

from db import Base, engine, get_db
from models import Guild, Player, Application, CharacterImport
from schemas import (
    GuildCreate, GuildOut, GuildCreated,
    PlayerCreate, PlayerOut, PlayerCreated,
    ApplicationCreate, ApplicationOut,
    ImportRequest, ImportSummary,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="TBC Recruit API")

cors = os.getenv("CORS_ORIGINS", "")
origins = [o.strip() for o in cors.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Allowed realms
allowed_realms_env = os.getenv("ALLOWED_REALMS", "Spineshatter,Thunderstrike")
ALLOWED_REALMS: Set[str] = {r.strip() for r in allowed_realms_env.split(",") if r.strip()}

def validate_realm(realm: str):
    if realm not in ALLOWED_REALMS:
        raise HTTPException(
            status_code=400,
            detail=f"Realm not allowed. Allowed: {', '.join(sorted(ALLOWED_REALMS))}"
        )

# Mini rate limit
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))
_rl_bucket: Dict[str, List[datetime]] = {}

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.method in ("POST", "PUT", "DELETE") and request.url.path.startswith("/api/"):
        ip = request.client.host if request.client else "unknown"
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=1)
        arr = _rl_bucket.get(ip, [])
        arr = [t for t in arr if t > window_start]
        if len(arr) >= RATE_LIMIT_PER_MINUTE:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        arr.append(now)
        _rl_bucket[ip] = arr
    return await call_next(request)

def require_token(entity_token: str, provided: Optional[str]):
    if not provided or provided != entity_token:
        raise HTTPException(status_code=401, detail="Invalid or missing edit token")

def guild_to_out(g: Guild) -> GuildOut:
    return GuildOut(
        id=g.id,
        name=g.name,
        realm=g.realm,
        faction=g.faction,
        language=g.language,
        raid_days=g.raid_days or [],
        raid_time_start=g.raid_time_start,
        raid_time_end=g.raid_time_end,
        progress=g.progress or {},
        needs=g.needs or [],
        loot_system=g.loot_system,
        contact_character=g.contact_character,
        discord=g.discord,
        website=g.website,
        description=g.description,
    )

def player_to_out(p: Player) -> PlayerOut:
    return PlayerOut(
        id=p.id,
        name=p.name,
        realm=p.realm,
        faction=p.faction,
        language=p.language,
        class_name=p.class_name,
        spec=p.spec,
        role=p.role,
        skill_rating=p.skill_rating,
        professions=p.professions or [],
        attunements=p.attunements or [],
        availability=p.availability or [],
        logs_url=p.logs_url,
        note=p.note,
    )

@app.get("/api/health")
def health():
    return {"ok": True, "allowed_realms": sorted(ALLOWED_REALMS)}

# Guilds
@app.post("/api/guilds", response_model=GuildCreated)
def create_guild(payload: GuildCreate, db: Session = Depends(get_db)):
    realm = payload.realm.strip()
    validate_realm(realm)

    token = secrets.token_urlsafe(24)
    g = Guild(
        edit_token=token,
        name=payload.name.strip(),
        realm=realm,
        faction=payload.faction,
        language=payload.language.strip(),
        raid_days=payload.raid_days,
        raid_time_start=payload.raid_time_start,
        raid_time_end=payload.raid_time_end,
        progress=payload.progress,
        needs=payload.needs,
        loot_system=payload.loot_system.strip(),
        contact_character=payload.contact_character.strip(),
        discord=payload.discord.strip(),
        website=payload.website.strip(),
        description=payload.description.strip(),
    )
    db.add(g)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Guild already exists or invalid data")
    db.refresh(g)
    return {"guild": guild_to_out(g), "edit_token": token}

@app.get("/api/guilds", response_model=List[GuildOut])
def list_guilds(
    db: Session = Depends(get_db),
    realm: Optional[str] = None,
    faction: Optional[str] = None,
    language: Optional[str] = None,
    q: Optional[str] = None,
    need_class: Optional[str] = None,
    need_role: Optional[str] = None,
):
    stmt = select(Guild)

    if realm:
        realm = realm.strip()
        validate_realm(realm)
        stmt = stmt.where(Guild.realm == realm)
    else:
        stmt = stmt.where(Guild.realm.in_(sorted(ALLOWED_REALMS)))

    if faction:
        stmt = stmt.where(Guild.faction == faction)
    if language:
        stmt = stmt.where(Guild.language == language)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(Guild.name.ilike(like))

    rows = db.execute(stmt).scalars().all()
    out: List[GuildOut] = []
    for g in rows:
        needs = g.needs or []
        if need_class:
            if not any((n.get("class") == need_class) or (n.get("class_name") == need_class) for n in needs):
                continue
        if need_role:
            if not any(n.get("role") == need_role for n in needs):
                continue
        out.append(guild_to_out(g))
    return out

@app.get("/api/guilds/{guild_id}", response_model=GuildOut)
def get_guild(guild_id: int, db: Session = Depends(get_db)):
    g = db.get(Guild, guild_id)
    if not g or g.realm not in ALLOWED_REALMS:
        raise HTTPException(404, "Guild not found")
    return guild_to_out(g)

@app.put("/api/guilds/{guild_id}", response_model=GuildOut)
def update_guild(
    guild_id: int,
    payload: GuildCreate,
    db: Session = Depends(get_db),
    x_edit_token: Optional[str] = Header(default=None),
):
    g = db.get(Guild, guild_id)
    if not g:
        raise HTTPException(404, "Guild not found")
    require_token(g.edit_token, x_edit_token)

    realm = payload.realm.strip()
    validate_realm(realm)

    g.name = payload.name.strip()
    g.realm = realm
    g.faction = payload.faction
    g.language = payload.language.strip()
    g.raid_days = payload.raid_days
    g.raid_time_start = payload.raid_time_start
    g.raid_time_end = payload.raid_time_end
    g.progress = payload.progress
    g.needs = payload.needs
    g.loot_system = payload.loot_system.strip()
    g.contact_character = payload.contact_character.strip()
    g.discord = payload.discord.strip()
    g.website = payload.website.strip()
    g.description = payload.description.strip()

    db.commit()
    db.refresh(g)
    return guild_to_out(g)

@app.delete("/api/guilds/{guild_id}")
def delete_guild(
    guild_id: int,
    db: Session = Depends(get_db),
    x_edit_token: Optional[str] = Header(default=None),
):
    g = db.get(Guild, guild_id)
    if not g:
        raise HTTPException(404, "Guild not found")
    require_token(g.edit_token, x_edit_token)
    db.delete(g)
    db.commit()
    return {"deleted": True}

# Players
@app.post("/api/players", response_model=PlayerCreated)
def create_player(payload: PlayerCreate, db: Session = Depends(get_db)):
    realm = payload.realm.strip()
    validate_realm(realm)

    token = secrets.token_urlsafe(24)
    p = Player(
        edit_token=token,
        name=payload.name.strip(),
        realm=realm,
        faction=payload.faction,
        language=payload.language.strip(),
        class_name=payload.class_name.strip(),
        spec=payload.spec.strip(),
        role=payload.role,
        skill_rating=payload.skill_rating,
        professions=payload.professions,
        attunements=payload.attunements,
        availability=payload.availability,
        logs_url=payload.logs_url.strip(),
        note=payload.note.strip(),
    )
    db.add(p)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Player already exists or invalid data")
    db.refresh(p)
    return {"player": player_to_out(p), "edit_token": token}

@app.get("/api/players", response_model=List[PlayerOut])
def list_players(
    db: Session = Depends(get_db),
    realm: Optional[str] = None,
    faction: Optional[str] = None,
    language: Optional[str] = None,
    class_name: Optional[str] = None,
    spec: Optional[str] = None,
    role: Optional[str] = None,
    min_skill: Optional[int] = None,
    q: Optional[str] = None,
):
    stmt = select(Player)

    if realm:
        realm = realm.strip()
        validate_realm(realm)
        stmt = stmt.where(Player.realm == realm)
    else:
        stmt = stmt.where(Player.realm.in_(sorted(ALLOWED_REALMS)))

    if faction:
        stmt = stmt.where(Player.faction == faction)
    if language:
        stmt = stmt.where(Player.language == language)
    if class_name:
        stmt = stmt.where(Player.class_name == class_name)
    if spec:
        stmt = stmt.where(Player.spec == spec)
    if role:
        stmt = stmt.where(Player.role == role)
    if min_skill is not None:
        stmt = stmt.where(Player.skill_rating >= min_skill)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(Player.name.ilike(like))

    rows = db.execute(stmt).scalars().all()
    return [player_to_out(p) for p in rows]

@app.get("/api/players/{player_id}", response_model=PlayerOut)
def get_player(player_id: int, db: Session = Depends(get_db)):
    p = db.get(Player, player_id)
    if not p or p.realm not in ALLOWED_REALMS:
        raise HTTPException(404, "Player not found")
    return player_to_out(p)

@app.put("/api/players/{player_id}", response_model=PlayerOut)
def update_player(
    player_id: int,
    payload: PlayerCreate,
    db: Session = Depends(get_db),
    x_edit_token: Optional[str] = Header(default=None),
):
    p = db.get(Player, player_id)
    if not p:
        raise HTTPException(404, "Player not found")
    require_token(p.edit_token, x_edit_token)

    realm = payload.realm.strip()
    validate_realm(realm)

    p.name = payload.name.strip()
    p.realm = realm
    p.faction = payload.faction
    p.language = payload.language.strip()
    p.class_name = payload.class_name.strip()
    p.spec = payload.spec.strip()
    p.role = payload.role
    p.skill_rating = payload.skill_rating
    p.professions = payload.professions
    p.attunements = payload.attunements
    p.availability = payload.availability
    p.logs_url = payload.logs_url.strip()
    p.note = payload.note.strip()

    db.commit()
    db.refresh(p)
    return player_to_out(p)

@app.delete("/api/players/{player_id}")
def delete_player(
    player_id: int,
    db: Session = Depends(get_db),
    x_edit_token: Optional[str] = Header(default=None),
):
    p = db.get(Player, player_id)
    if not p:
        raise HTTPException(404, "Player not found")
    require_token(p.edit_token, x_edit_token)
    db.delete(p)
    db.commit()
    return {"deleted": True}

# Applications
@app.post("/api/applications", response_model=ApplicationOut)
def apply(payload: ApplicationCreate, db: Session = Depends(get_db)):
    g = db.get(Guild, payload.guild_id)
    p = db.get(Player, payload.player_id)
    if not g or not p:
        raise HTTPException(404, "Guild or Player not found")

    if g.realm not in ALLOWED_REALMS or p.realm not in ALLOWED_REALMS:
        raise HTTPException(400, "Realm not allowed")

    a = Application(
        guild_id=g.id,
        player_id=p.id,
        message=payload.message.strip(),
        status="pending",
    )
    db.add(a)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Already applied or invalid")
    db.refresh(a)

    return ApplicationOut(
        id=a.id,
        guild_id=a.guild_id,
        player_id=a.player_id,
        message=a.message,
        status=a.status,
        created_at=a.created_at.isoformat(),
    )

@app.get("/api/guilds/{guild_id}/applications", response_model=List[ApplicationOut])
def guild_apps(
    guild_id: int,
    db: Session = Depends(get_db),
    x_edit_token: Optional[str] = Header(default=None),
):
    g = db.get(Guild, guild_id)
    if not g:
        raise HTTPException(404, "Guild not found")
    require_token(g.edit_token, x_edit_token)

    if g.realm not in ALLOWED_REALMS:
        raise HTTPException(404, "Guild not found")

    stmt = select(Application).where(Application.guild_id == guild_id)
    rows = db.execute(stmt).scalars().all()
    return [
        ApplicationOut(
            id=a.id,
            guild_id=a.guild_id,
            player_id=a.player_id,
            message=a.message,
            status=a.status,
            created_at=a.created_at.isoformat(),
        )
        for a in rows
    ]

@app.post("/api/import")
def import_character(req: ImportRequest, db: Session = Depends(get_db)):
    try:
        payload = decode_export_string(req.exportString)
        summary = summarize_payload(payload)

        name = (summary.get("name") or "").strip()
        realm = (summary.get("realm") or "").strip()
        if not name or not realm:
            raise HTTPException(status_code=400, detail="Missing character name or realm")

        validate_realm(realm)

        exported_at = None
        exported_at_raw = summary.get("exportedAt")
        if exported_at_raw:
            try:
                exported_at = datetime.fromisoformat(exported_at_raw.replace("Z", "+00:00"))
            except Exception:
                exported_at = None

        guid = (summary.get("guid") or "").strip() or None

        values = {
            "guid": guid,
            "name": name,
            "realm": realm,
            "level": summary.get("level"),
            "class_file": summary.get("classFile"),
            "race_file": summary.get("raceFile"),
            "faction": summary.get("faction"),
            "guild_name": summary.get("guildName"),
            "exported_at": exported_at,
            "payload": payload,
            "updated_at": func.now(),
        }

        if guid:
            stmt = insert(CharacterImport).values(**values)
            stmt = stmt.on_conflict_do_update(
                index_elements=[CharacterImport.guid],
                set_=values,
            ).returning(CharacterImport.id)
        else:
            stmt = insert(CharacterImport).values(**values)
            stmt = stmt.on_conflict_do_update(
                index_elements=[CharacterImport.name, CharacterImport.realm],
                set_=values,
            ).returning(CharacterImport.id)

        new_id = db.execute(stmt).scalar()
        db.commit()

        return {"ok": True, "id": int(new_id) if new_id is not None else None, "summary": ImportSummary(**summary)}

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
