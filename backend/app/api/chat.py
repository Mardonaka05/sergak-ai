"""Chat API — DMs, groups, messages, members"""
import os
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, desc, update
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.chat import Conversation, ConversationMember, Message

router = APIRouter()

# Upload directory for chat attachments
CHAT_UPLOAD_DIR = settings.BASE_DIR / "chat_uploads"
CHAT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ===== Schemas =====

class UserMini(BaseModel):
    id: int
    username: str
    full_name: str
    email: str
    role: str
    avatar_url: str = ""

    class Config:
        from_attributes = True


class MessageOut(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    sender_name: str = ""
    sender_role: str = ""
    sender_avatar: str = ""
    text: str
    attachment_url: str = ""
    attachment_type: str = ""
    attachment_name: str = ""
    attachment_duration: float = 0  # for audio
    reply_to_id: Optional[int] = None
    edited: bool = False
    deleted: bool = False
    read_by_all: bool = False  # all OTHER members have read this message
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationOut(BaseModel):
    id: int
    type: str
    name: str
    avatar_seed: str
    members: List[UserMini] = []
    last_message: Optional[MessageOut] = None
    unread_count: int = 0
    last_message_at: Optional[datetime] = None


class CreateDmIn(BaseModel):
    user_id: int


class CreateGroupIn(BaseModel):
    name: str
    member_ids: List[int]


class SendMessageIn(BaseModel):
    text: str = ""
    reply_to_id: Optional[int] = None
    attachment_url: str = ""
    attachment_type: str = ""
    attachment_name: str = ""


class EditMessageIn(BaseModel):
    text: str


class AddMembersIn(BaseModel):
    user_ids: List[int]


# ===== Helpers =====

async def _user_in_conversation(db: AsyncSession, conv_id: int, user_id: int) -> Optional[ConversationMember]:
    res = await db.execute(
        select(ConversationMember).where(
            and_(ConversationMember.conversation_id == conv_id,
                 ConversationMember.user_id == user_id)
        )
    )
    return res.scalar_one_or_none()


async def _min_other_read_id(db: AsyncSession, conv_id: int, sender_id: int) -> int:
    """Minimum last_read_message_id among members other than the sender."""
    res = await db.execute(
        select(func.min(ConversationMember.last_read_message_id)).where(
            and_(ConversationMember.conversation_id == conv_id,
                 ConversationMember.user_id != sender_id)
        )
    )
    return res.scalar() or 0


async def _serialize_message(db: AsyncSession, msg: Message, min_other_read_id: Optional[int] = None) -> MessageOut:
    sender = await db.get(User, msg.sender_id)
    if min_other_read_id is None:
        min_other_read_id = await _min_other_read_id(db, msg.conversation_id, msg.sender_id)
    # Detect audio attachments by type or extension
    att_type = msg.attachment_type or ""
    if not att_type and msg.attachment_url:
        u = msg.attachment_url.lower()
        if u.endswith(".webm") or u.endswith(".ogg") or u.endswith(".mp3") or u.endswith(".m4a") or u.endswith(".wav"):
            att_type = "audio"
    return MessageOut(
        id=msg.id, conversation_id=msg.conversation_id, sender_id=msg.sender_id,
        sender_name=(sender.full_name if sender else "") or (sender.username if sender else ""),
        sender_role=sender.role if sender else "",
        sender_avatar=(sender.avatar_url if sender else "") or "",
        text="" if msg.deleted else msg.text,
        attachment_url="" if msg.deleted else msg.attachment_url,
        attachment_type="" if msg.deleted else att_type,
        attachment_name="" if msg.deleted else msg.attachment_name,
        reply_to_id=msg.reply_to_id, edited=msg.edited, deleted=msg.deleted,
        read_by_all=(min_other_read_id >= msg.id),
        created_at=msg.created_at,
    )


async def _serialize_conv(db: AsyncSession, conv: Conversation, current_user_id: int) -> ConversationOut:
    # Members
    mres = await db.execute(
        select(User).join(ConversationMember, ConversationMember.user_id == User.id)
        .where(ConversationMember.conversation_id == conv.id)
    )
    members = [UserMini.model_validate(u) for u in mres.scalars().all()]

    # Last message
    lres = await db.execute(
        select(Message).where(Message.conversation_id == conv.id)
        .order_by(desc(Message.id)).limit(1)
    )
    last = lres.scalar_one_or_none()
    last_msg = await _serialize_message(db, last) if last else None

    # Unread count
    mem = await _user_in_conversation(db, conv.id, current_user_id)
    last_read_id = mem.last_read_message_id if mem else 0
    cres = await db.execute(
        select(func.count(Message.id)).where(
            and_(Message.conversation_id == conv.id,
                 Message.id > last_read_id,
                 Message.sender_id != current_user_id)
        )
    )
    unread = cres.scalar() or 0

    # Display name for DM: use the other participant's name
    name = conv.name
    avatar_seed = conv.avatar_seed
    if conv.type == "dm":
        other = next((u for u in members if u.id != current_user_id), None)
        if other:
            name = other.full_name or other.username
            avatar_seed = other.username

    return ConversationOut(
        id=conv.id, type=conv.type, name=name, avatar_seed=avatar_seed or f"conv{conv.id}",
        members=members, last_message=last_msg, unread_count=unread,
        last_message_at=conv.last_message_at,
    )


# ===== Endpoints =====

@router.get("/conversations", response_model=List[ConversationOut])
async def list_conversations(db: AsyncSession = Depends(get_db), current: User = Depends(get_current_user)):
    res = await db.execute(
        select(Conversation).join(ConversationMember, ConversationMember.conversation_id == Conversation.id)
        .where(ConversationMember.user_id == current.id)
        .order_by(desc(Conversation.last_message_at), desc(Conversation.id))
    )
    convs = res.scalars().all()
    return [await _serialize_conv(db, c, current.id) for c in convs]


@router.get("/unread-count")
async def total_unread(db: AsyncSession = Depends(get_db), current: User = Depends(get_current_user)):
    """Total unread messages across all conversations the user is in."""
    res = await db.execute(
        select(ConversationMember).where(ConversationMember.user_id == current.id)
    )
    members = res.scalars().all()
    total = 0
    for m in members:
        c = await db.execute(
            select(func.count(Message.id)).where(
                and_(Message.conversation_id == m.conversation_id,
                     Message.id > m.last_read_message_id,
                     Message.sender_id != current.id)
            )
        )
        total += c.scalar() or 0
    return {"total": total}


@router.post("/conversations/dm", response_model=ConversationOut)
async def create_or_open_dm(data: CreateDmIn, db: AsyncSession = Depends(get_db), current: User = Depends(get_current_user)):
    """Find existing DM between current user and target, or create one."""
    if data.user_id == current.id:
        raise HTTPException(400, "O'zingiz bilan chatlasha olmaysiz")
    target = await db.get(User, data.user_id)
    if not target or target.pending:
        raise HTTPException(404, "Foydalanuvchi topilmadi")

    # Find DM containing both users
    sub_me = select(ConversationMember.conversation_id).where(ConversationMember.user_id == current.id)
    sub_target = select(ConversationMember.conversation_id).where(ConversationMember.user_id == target.id)
    res = await db.execute(
        select(Conversation).where(
            and_(Conversation.type == "dm",
                 Conversation.id.in_(sub_me),
                 Conversation.id.in_(sub_target))
        ).limit(1)
    )
    conv = res.scalar_one_or_none()
    if not conv:
        conv = Conversation(type="dm", name="", avatar_seed="", created_by=current.id)
        db.add(conv)
        await db.commit()
        await db.refresh(conv)
        db.add(ConversationMember(conversation_id=conv.id, user_id=current.id))
        db.add(ConversationMember(conversation_id=conv.id, user_id=target.id))
        await db.commit()

    return await _serialize_conv(db, conv, current.id)


@router.post("/conversations/group", response_model=ConversationOut)
async def create_group(data: CreateGroupIn, db: AsyncSession = Depends(get_db), current: User = Depends(get_current_user)):
    name = (data.name or "").strip()
    if not name:
        raise HTTPException(400, "Guruh nomini kiriting")
    member_ids = set(data.member_ids or [])
    member_ids.add(current.id)
    if len(member_ids) < 2:
        raise HTTPException(400, "Kamida 1 kishini qo'shing")

    # Validate users
    res = await db.execute(select(User).where(User.id.in_(member_ids)))
    users = res.scalars().all()
    valid_ids = {u.id for u in users if not u.pending}
    if current.id not in valid_ids or len(valid_ids) < 2:
        raise HTTPException(400, "Noto'g'ri foydalanuvchilar")

    conv = Conversation(type="group", name=name, avatar_seed=f"group{uuid.uuid4().hex[:8]}",
                        created_by=current.id, last_message_at=datetime.utcnow())
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    for uid in valid_ids:
        db.add(ConversationMember(
            conversation_id=conv.id, user_id=uid,
            is_admin=(uid == current.id),
        ))
    await db.commit()
    return await _serialize_conv(db, conv, current.id)


@router.get("/conversations/{conv_id}/messages", response_model=List[MessageOut])
async def list_messages(
    conv_id: int,
    before_id: Optional[int] = None,
    after_id: Optional[int] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(get_current_user),
):
    mem = await _user_in_conversation(db, conv_id, current.id)
    if not mem:
        raise HTTPException(403, "Bu chatga kirish huquqingiz yo'q")
    q = select(Message).where(Message.conversation_id == conv_id)
    if before_id:
        q = q.where(Message.id < before_id)
    if after_id:
        q = q.where(Message.id > after_id)
    q = q.order_by(desc(Message.id)).limit(min(limit, 200))
    res = await db.execute(q)
    msgs = list(res.scalars().all())
    msgs.reverse()  # chronological
    # For sender's messages we compute read_by_all per sender (own messages only matter for UI)
    out = []
    cache = {}
    for m in msgs:
        if m.sender_id == current.id:
            if m.sender_id not in cache:
                cache[m.sender_id] = await _min_other_read_id(db, conv_id, m.sender_id)
            out.append(await _serialize_message(db, m, cache[m.sender_id]))
        else:
            out.append(await _serialize_message(db, m, 0))
    return out


@router.post("/conversations/{conv_id}/messages", response_model=MessageOut)
async def send_message(
    conv_id: int, data: SendMessageIn,
    db: AsyncSession = Depends(get_db), current: User = Depends(get_current_user),
):
    mem = await _user_in_conversation(db, conv_id, current.id)
    if not mem:
        raise HTTPException(403, "Bu chatga kirish huquqingiz yo'q")
    if not (data.text or "").strip() and not data.attachment_url:
        raise HTTPException(400, "Xabar bo'sh bo'la olmaydi")

    msg = Message(
        conversation_id=conv_id, sender_id=current.id,
        text=(data.text or "").strip(), reply_to_id=data.reply_to_id,
        attachment_url=data.attachment_url or "",
        attachment_type=data.attachment_type or "",
        attachment_name=data.attachment_name or "",
    )
    db.add(msg)

    # Update conversation timestamp
    conv = await db.get(Conversation, conv_id)
    if conv:
        conv.last_message_at = datetime.utcnow()

    await db.commit()
    await db.refresh(msg)
    # Mark own message as read for sender
    mem.last_read_message_id = msg.id
    await db.commit()
    return await _serialize_message(db, msg)


@router.put("/messages/{msg_id}", response_model=MessageOut)
async def edit_message(
    msg_id: int, data: EditMessageIn,
    db: AsyncSession = Depends(get_db), current: User = Depends(get_current_user),
):
    msg = await db.get(Message, msg_id)
    if not msg:
        raise HTTPException(404, "Xabar topilmadi")
    if msg.sender_id != current.id:
        raise HTTPException(403, "Faqat o'z xabaringizni tahrirlaysiz")
    if msg.deleted:
        raise HTTPException(400, "O'chirilgan xabarni tahrirlab bo'lmaydi")
    text = (data.text or "").strip()
    if not text:
        raise HTTPException(400, "Bo'sh xabar")
    msg.text = text
    msg.edited = True
    await db.commit()
    await db.refresh(msg)
    return await _serialize_message(db, msg)


@router.delete("/messages/{msg_id}")
async def delete_message(
    msg_id: int,
    db: AsyncSession = Depends(get_db), current: User = Depends(get_current_user),
):
    msg = await db.get(Message, msg_id)
    if not msg:
        raise HTTPException(404, "Xabar topilmadi")
    if msg.sender_id != current.id and current.role != "admin":
        raise HTTPException(403, "Faqat o'z xabaringizni o'chirasiz")
    msg.deleted = True
    msg.text = ""
    msg.attachment_url = ""
    await db.commit()
    return {"ok": True}


@router.post("/conversations/{conv_id}/read")
async def mark_read(
    conv_id: int,
    db: AsyncSession = Depends(get_db), current: User = Depends(get_current_user),
):
    mem = await _user_in_conversation(db, conv_id, current.id)
    if not mem:
        raise HTTPException(403, "Bu chatga kirish huquqingiz yo'q")
    res = await db.execute(
        select(func.max(Message.id)).where(Message.conversation_id == conv_id)
    )
    last_id = res.scalar() or 0
    mem.last_read_message_id = last_id
    await db.commit()
    return {"ok": True, "last_read_message_id": last_id}


@router.post("/conversations/{conv_id}/members")
async def add_members(
    conv_id: int, data: AddMembersIn,
    db: AsyncSession = Depends(get_db), current: User = Depends(get_current_user),
):
    conv = await db.get(Conversation, conv_id)
    if not conv:
        raise HTTPException(404, "Chat topilmadi")
    if conv.type != "group":
        raise HTTPException(400, "Faqat guruhga a'zo qo'shish mumkin")
    mem = await _user_in_conversation(db, conv_id, current.id)
    if not mem or (not mem.is_admin and current.role != "admin"):
        raise HTTPException(403, "Faqat guruh admini a'zo qo'sha oladi")

    added = 0
    for uid in data.user_ids:
        u = await db.get(User, uid)
        if not u or u.pending:
            continue
        existing = await _user_in_conversation(db, conv_id, uid)
        if existing:
            continue
        db.add(ConversationMember(conversation_id=conv_id, user_id=uid))
        added += 1
    await db.commit()
    return {"ok": True, "added": added}


@router.delete("/conversations/{conv_id}/members/{user_id}")
async def remove_member(
    conv_id: int, user_id: int,
    db: AsyncSession = Depends(get_db), current: User = Depends(get_current_user),
):
    conv = await db.get(Conversation, conv_id)
    if not conv:
        raise HTTPException(404, "Chat topilmadi")
    mem = await _user_in_conversation(db, conv_id, current.id)
    if not mem:
        raise HTTPException(403, "Sizning chatingiz emas")
    # Self-leave allowed; otherwise need admin
    if user_id != current.id and not mem.is_admin and current.role != "admin":
        raise HTTPException(403, "Faqat guruh admini a'zoni chiqaradi")
    target_mem = await _user_in_conversation(db, conv_id, user_id)
    if not target_mem:
        raise HTTPException(404, "A'zo topilmadi")
    await db.delete(target_mem)
    await db.commit()
    return {"ok": True}


@router.delete("/conversations/{conv_id}")
async def delete_conversation(
    conv_id: int,
    db: AsyncSession = Depends(get_db), current: User = Depends(get_current_user),
):
    conv = await db.get(Conversation, conv_id)
    if not conv:
        raise HTTPException(404, "Chat topilmadi")
    if current.role != "admin" and conv.created_by != current.id:
        raise HTTPException(403, "Faqat admin yoki yaratuvchi o'chiradi")
    await db.delete(conv)
    await db.commit()
    return {"ok": True}


# ===== Attachments =====

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current: User = Depends(get_current_user),
):
    """Upload an attachment. Returns URL + metadata."""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if len(ext) > 10:
        ext = ""
    fname = f"{uuid.uuid4().hex}{ext}"
    fpath = CHAT_UPLOAD_DIR / fname
    content = await file.read()
    if len(content) > 20 * 1024 * 1024:  # 20 MB
        raise HTTPException(400, "Fayl 20 MB dan katta")
    with open(fpath, "wb") as f:
        f.write(content)

    image_exts = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
    audio_exts = {".webm", ".ogg", ".mp3", ".m4a", ".wav", ".oga"}
    if ext in image_exts:
        atype = "image"
    elif ext in audio_exts:
        atype = "audio"
    else:
        atype = "file"
    return {
        "url": f"/api/chat/attachments/{fname}",
        "type": atype,
        "name": file.filename or fname,
        "size": len(content),
    }


@router.get("/attachments/{fname}")
async def get_attachment(fname: str):
    """Serve uploaded attachments. NOTE: no auth required because:
    1. <img> tags in browsers cannot send Authorization headers
    2. Filenames are UUIDs (unguessable) — effectively unlisted
    Used for avatars, chat images, voice notes, etc."""
    # basic path safety
    if "/" in fname or "\\" in fname or ".." in fname:
        raise HTTPException(400, "Noto'g'ri fayl nomi")
    fpath = CHAT_UPLOAD_DIR / fname
    if not fpath.exists():
        raise HTTPException(404, "Fayl topilmadi")
    # Cache attachments in browser — they never change
    return FileResponse(str(fpath), headers={"Cache-Control": "public, max-age=86400"})


@router.get("/users", response_model=List[UserMini])
async def list_chat_users(db: AsyncSession = Depends(get_db), current: User = Depends(get_current_user)):
    """List all users available for chat (excluding pending and self)."""
    res = await db.execute(
        select(User).where(and_(User.pending == False, User.active == True, User.id != current.id))
        .order_by(User.role, User.full_name)
    )
    return res.scalars().all()
