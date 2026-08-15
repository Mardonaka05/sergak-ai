"""
NVR ulanish — IP + login/parol → NVR'dagi BARCHA kameralar.

Qo'llab-quvvatlanadi:
  - Hikvision ISAPI (eng keng tarqalgan)
  - Dahua HTTP API
  - ONVIF (universal)

Foydalanish:
  POST /api/discovery/nvr/connect
    body: {ip, username, password, port}
  → returns: {brand, model, channels: [{id, name, rtsp_url, ...}]}
"""
import asyncio
import re
import socket
import xml.etree.ElementTree as ET
from typing import List, Optional, Dict
from urllib.parse import quote

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

try:
    import httpx
    HAS_HTTPX = True
except Exception:
    HAS_HTTPX = False


router = APIRouter()


# ============ Models ============

class NVRConnectIn(BaseModel):
    ip: str
    username: str
    password: str
    port: int = 80          # HTTP port (Hikvision/Dahua: 80, ba'zilarida 8000)
    rtsp_port: int = 554    # RTSP port


class NVRChannel(BaseModel):
    id: int                 # kanal raqami (1, 2, 3...)
    name: str = ""          # kanal nomi
    rtsp_url: str           # to'liq RTSP URL (login/parol bilan)
    rtsp_url_safe: str = "" # rtsp:// usz/*** parol yashirilgan
    resolution: str = ""    # masalan "1920x1080"
    enabled: bool = True
    online: bool = True
    codec: str = ""         # H264, H265, MJPEG
    sub_stream_url: str = ""  # past sifatli (sub) stream
    snapshot_url: str = ""    # JPEG snapshot URL


class NVRConnectOut(BaseModel):
    ok: bool
    brand: str = ""         # Hikvision, Dahua, ONVIF
    model: str = ""         # NVR model nomi
    firmware: str = ""
    nvr_ip: str
    channel_count: int
    channels: List[NVRChannel]
    method: str = ""        # qaysi protokol orqali topildi


# ============ Helpers ============

def _safe_rtsp(ip: str, port: int, path: str, username: str, password: str) -> str:
    """Login/parol bilan RTSP URL yaratish."""
    user = quote(username, safe='')
    pwd = quote(password, safe='')
    return f"rtsp://{user}:{pwd}@{ip}:{port}{path}"


def _safe_rtsp_masked(ip: str, port: int, path: str, username: str) -> str:
    """Parol yashirilgan ko'rinish (UI uchun)."""
    return f"rtsp://{username}:***@{ip}:{port}{path}"


# ============ Hikvision ISAPI ============

async def _hikvision_connect(data: NVRConnectIn) -> Optional[NVRConnectOut]:
    """Hikvision NVR/DVR/IPC dan kanallar ro'yxatini olish."""
    if not HAS_HTTPX:
        return None

    base = f"http://{data.ip}:{data.port}"
    auth = httpx.DigestAuth(data.username, data.password)

    async with httpx.AsyncClient(timeout=8.0, auth=auth) as client:
        # 1) Device info — modelni va brendi tekshirish
        try:
            r = await client.get(f"{base}/ISAPI/System/deviceInfo")
        except Exception:
            return None
        if r.status_code == 401:
            raise HTTPException(401, "Login yoki parol noto'g'ri (Hikvision)")
        if r.status_code != 200:
            return None

        # Parse device info
        model = ""
        firmware = ""
        device_name = ""
        try:
            root = ET.fromstring(r.text)
            ns = {"x": _xmlns(root)}
            def gx(tag):
                el = root.find(f"x:{tag}", ns) if ns["x"] else root.find(tag)
                return el.text if el is not None and el.text else ""
            model = gx("model")
            firmware = gx("firmwareVersion")
            device_name = gx("deviceName")
        except Exception:
            pass

        # Hikvision ekanligini tasdiqlash
        if not model and "hikvision" not in r.text.lower():
            return None

        # 2) Kanallar (NVR uchun) — InputProxy/channels
        channels: List[NVRChannel] = []
        try:
            r2 = await client.get(f"{base}/ISAPI/ContentMgmt/InputProxy/channels")
            if r2.status_code == 200:
                channels = _parse_hikvision_input_proxy(r2.text, data)
        except Exception:
            pass

        # 3) Agar InputProxy bo'sh bo'lsa (IP kamera — NVR emas) — Streaming/channels
        if not channels:
            try:
                r3 = await client.get(f"{base}/ISAPI/Streaming/channels")
                if r3.status_code == 200:
                    channels = _parse_hikvision_streaming(r3.text, data)
            except Exception:
                pass

        # 4) Hech narsa topilmasa, default 101..3201 kanallar yaratish
        if not channels:
            # NVR'da odatda 1..32 kanal. Lekin biz bilmaymiz, shuning uchun
            # 1..16 ni default qilamiz (admin keyin tahrirlaydi)
            for ch in range(1, 17):
                channels.append(NVRChannel(
                    id=ch,
                    name=f"Kanal {ch}",
                    rtsp_url=_safe_rtsp(data.ip, data.rtsp_port,
                                         f"/Streaming/Channels/{ch}01",
                                         data.username, data.password),
                    rtsp_url_safe=_safe_rtsp_masked(data.ip, data.rtsp_port,
                                                     f"/Streaming/Channels/{ch}01",
                                                     data.username),
                    sub_stream_url=_safe_rtsp(data.ip, data.rtsp_port,
                                                f"/Streaming/Channels/{ch}02",
                                                data.username, data.password),
                    snapshot_url=f"http://{data.ip}:{data.port}/ISAPI/Streaming/channels/{ch}01/picture",
                ))

        return NVRConnectOut(
            ok=True,
            brand="Hikvision",
            model=model or device_name or "Hikvision NVR",
            firmware=firmware,
            nvr_ip=data.ip,
            channel_count=len(channels),
            channels=channels,
            method="Hikvision ISAPI",
        )


def _xmlns(elem) -> str:
    """XML namespace URI ni olish (Hikvision XML default ns'ga ega)."""
    if elem.tag.startswith("{"):
        return elem.tag[1:elem.tag.index("}")]
    return ""


def _parse_hikvision_input_proxy(xml_text: str, data: NVRConnectIn) -> List[NVRChannel]:
    """NVR'ning InputProxy javobini parse qilish."""
    channels: List[NVRChannel] = []
    try:
        root = ET.fromstring(xml_text)
        ns_uri = _xmlns(root)
        ns = {"x": ns_uri} if ns_uri else {}

        def find_all(parent, tag):
            return parent.findall(f"x:{tag}", ns) if ns_uri else parent.findall(tag)

        def find_text(parent, tag):
            el = parent.find(f"x:{tag}", ns) if ns_uri else parent.find(tag)
            return el.text.strip() if el is not None and el.text else ""

        for ch in find_all(root, "InputProxyChannel"):
            chan_id_str = find_text(ch, "id")
            try:
                chan_id = int(chan_id_str)
            except Exception:
                continue
            name = find_text(ch, "name") or f"Kanal {chan_id}"
            online = find_text(ch, "online") != "false"
            # rtspPort
            stream_path = f"/Streaming/Channels/{chan_id}01"
            sub_path = f"/Streaming/Channels/{chan_id}02"
            channels.append(NVRChannel(
                id=chan_id,
                name=name,
                online=online,
                rtsp_url=_safe_rtsp(data.ip, data.rtsp_port, stream_path,
                                     data.username, data.password),
                rtsp_url_safe=_safe_rtsp_masked(data.ip, data.rtsp_port, stream_path,
                                                 data.username),
                sub_stream_url=_safe_rtsp(data.ip, data.rtsp_port, sub_path,
                                            data.username, data.password),
                snapshot_url=f"http://{data.ip}:{data.port}/ISAPI/Streaming/channels/{chan_id}01/picture",
            ))
    except Exception as e:
        print(f"[NVR] Hikvision InputProxy parse xato: {e}")
    return channels


def _parse_hikvision_streaming(xml_text: str, data: NVRConnectIn) -> List[NVRChannel]:
    """IPC (NVR emas) uchun /Streaming/channels javobini parse."""
    channels: List[NVRChannel] = []
    try:
        root = ET.fromstring(xml_text)
        ns_uri = _xmlns(root)
        ns = {"x": ns_uri} if ns_uri else {}

        def find_all(parent, tag):
            return parent.findall(f"x:{tag}", ns) if ns_uri else parent.findall(tag)

        def find_text(parent, tag):
            el = parent.find(f"x:{tag}", ns) if ns_uri else parent.find(tag)
            return el.text.strip() if el is not None and el.text else ""

        for sc in find_all(root, "StreamingChannel"):
            sc_id_str = find_text(sc, "id")
            try:
                sc_id = int(sc_id_str)
            except Exception:
                continue
            # NVR streaming: 101=ch1 main, 102=ch1 sub
            chan_id = sc_id // 100
            sub = sc_id % 100  # 1=main, 2=sub
            if sub != 1:
                continue
            name = find_text(sc, "channelName") or f"Kanal {chan_id}"
            stream_path = f"/Streaming/Channels/{chan_id}01"
            sub_path = f"/Streaming/Channels/{chan_id}02"
            channels.append(NVRChannel(
                id=chan_id, name=name,
                rtsp_url=_safe_rtsp(data.ip, data.rtsp_port, stream_path,
                                     data.username, data.password),
                rtsp_url_safe=_safe_rtsp_masked(data.ip, data.rtsp_port, stream_path,
                                                 data.username),
                sub_stream_url=_safe_rtsp(data.ip, data.rtsp_port, sub_path,
                                            data.username, data.password),
                snapshot_url=f"http://{data.ip}:{data.port}/ISAPI/Streaming/channels/{chan_id}01/picture",
            ))
    except Exception as e:
        print(f"[NVR] Hikvision Streaming parse xato: {e}")
    return channels


# ============ Dahua HTTP API ============

async def _dahua_connect(data: NVRConnectIn) -> Optional[NVRConnectOut]:
    """Dahua NVR/DVR/IPC kanallarini olish."""
    if not HAS_HTTPX:
        return None

    base = f"http://{data.ip}:{data.port}"
    auth = httpx.DigestAuth(data.username, data.password)

    async with httpx.AsyncClient(timeout=8.0, auth=auth) as client:
        # 1) Brendi tasdiqlash (machine name)
        try:
            r = await client.get(f"{base}/cgi-bin/magicBox.cgi?action=getDeviceType")
        except Exception:
            return None
        if r.status_code == 401:
            raise HTTPException(401, "Login yoki parol noto'g'ri (Dahua)")
        if r.status_code != 200 or "type=" not in r.text:
            return None

        model = ""
        m = re.search(r"type=(.+)", r.text)
        if m:
            model = m.group(1).strip()

        firmware = ""
        try:
            r2 = await client.get(f"{base}/cgi-bin/magicBox.cgi?action=getSoftwareVersion")
            if r2.status_code == 200:
                fm = re.search(r"version=(.+)", r2.text)
                if fm: firmware = fm.group(1).strip()
        except Exception:
            pass

        # 2) Kanallar soni
        max_channels = 16  # default
        try:
            r3 = await client.get(f"{base}/cgi-bin/magicBox.cgi?action=getProductDefinition&name=MaxRemoteInputChannels")
            if r3.status_code == 200:
                mm = re.search(r"=(\d+)", r3.text)
                if mm: max_channels = int(mm.group(1))
        except Exception:
            pass

        # 3) Har bir kanal uchun nom va RTSP URL
        channels: List[NVRChannel] = []
        try:
            r4 = await client.get(f"{base}/cgi-bin/configManager.cgi?action=getConfig&name=ChannelTitle")
            if r4.status_code == 200:
                # table.ChannelTitle[0].Name=Kanal1
                names_map: Dict[int, str] = {}
                for line in r4.text.splitlines():
                    m = re.match(r"table\.ChannelTitle\[(\d+)\]\.Name=(.+)", line.strip())
                    if m:
                        names_map[int(m.group(1))] = m.group(2)
                for idx in range(max_channels):
                    name = names_map.get(idx, f"Kanal {idx + 1}")
                    # Dahua RTSP: rtsp://user:pass@ip:554/cam/realmonitor?channel=1&subtype=0
                    main_path = f"/cam/realmonitor?channel={idx + 1}&subtype=0"
                    sub_path = f"/cam/realmonitor?channel={idx + 1}&subtype=1"
                    channels.append(NVRChannel(
                        id=idx + 1, name=name,
                        rtsp_url=_safe_rtsp(data.ip, data.rtsp_port, main_path,
                                             data.username, data.password),
                        rtsp_url_safe=_safe_rtsp_masked(data.ip, data.rtsp_port, main_path,
                                                         data.username),
                        sub_stream_url=_safe_rtsp(data.ip, data.rtsp_port, sub_path,
                                                    data.username, data.password),
                        snapshot_url=f"http://{data.ip}:{data.port}/cgi-bin/snapshot.cgi?channel={idx + 1}",
                    ))
        except Exception as e:
            print(f"[NVR] Dahua ChannelTitle parse xato: {e}")

        # Fallback: hech narsa parse bo'lmasa ham, default kanallar
        if not channels:
            for idx in range(max_channels):
                main_path = f"/cam/realmonitor?channel={idx + 1}&subtype=0"
                channels.append(NVRChannel(
                    id=idx + 1, name=f"Kanal {idx + 1}",
                    rtsp_url=_safe_rtsp(data.ip, data.rtsp_port, main_path,
                                         data.username, data.password),
                    rtsp_url_safe=_safe_rtsp_masked(data.ip, data.rtsp_port, main_path,
                                                     data.username),
                    snapshot_url=f"http://{data.ip}:{data.port}/cgi-bin/snapshot.cgi?channel={idx + 1}",
                ))

        return NVRConnectOut(
            ok=True, brand="Dahua", model=model or "Dahua NVR",
            firmware=firmware, nvr_ip=data.ip,
            channel_count=len(channels), channels=channels,
            method="Dahua HTTP API",
        )


# ============ ONVIF (Universal) ============

async def _onvif_connect(data: NVRConnectIn) -> Optional[NVRConnectOut]:
    """ONVIF orqali GetProfiles → har bir profil uchun RTSP URL."""
    if not HAS_HTTPX:
        return None

    # ONVIF Media service eng keng tarqalgan portlar
    onvif_ports = [80, 8000, 8080, data.port] if data.port not in (80, 8000, 8080) else [data.port, 8000, 80, 8080]
    onvif_ports = list(dict.fromkeys(onvif_ports))  # dedupe, preserve order

    for port in onvif_ports:
        base = f"http://{data.ip}:{port}"
        # GetProfiles SOAP request (Media v1 / v2)
        body = _onvif_soap_envelope(
            data.username, data.password,
            "<GetProfiles xmlns='http://www.onvif.org/ver10/media/wsdl'/>"
        )
        async with httpx.AsyncClient(timeout=6.0) as client:
            for path in ("/onvif/media_service", "/onvif/Media", "/onvif/services", "/onvif/device_service"):
                try:
                    r = await client.post(
                        f"{base}{path}",
                        content=body,
                        headers={"Content-Type": 'application/soap+xml; charset=utf-8'},
                    )
                    if r.status_code == 401:
                        continue
                    if r.status_code != 200 or "Profile" not in r.text:
                        continue
                    profiles = _onvif_parse_profiles(r.text)
                    if not profiles:
                        continue
                    channels = []
                    for i, prof in enumerate(profiles, 1):
                        # GetStreamUri foydalanmasdan oddiy RTSP yo'l
                        path_part = f"/onvif-media/media.amp?profile={prof['token']}&sessiontimeout=60&streamtype=unicast"
                        channels.append(NVRChannel(
                            id=i, name=prof.get("name", f"Profile {i}"),
                            rtsp_url=_safe_rtsp(data.ip, data.rtsp_port, path_part,
                                                 data.username, data.password),
                            rtsp_url_safe=_safe_rtsp_masked(data.ip, data.rtsp_port, path_part,
                                                             data.username),
                        ))
                    return NVRConnectOut(
                        ok=True, brand="ONVIF", model="Generic ONVIF",
                        nvr_ip=data.ip,
                        channel_count=len(channels), channels=channels,
                        method=f"ONVIF Media ({path})",
                    )
                except Exception:
                    continue
    return None


def _onvif_soap_envelope(username: str, password: str, body: str) -> bytes:
    """Oddiy SOAP envelope WS-Security header bilan."""
    # NOTE: bu PASSWORD ni clear-text qilib yuboradi. Production'da
    # WS-UsernameToken Digest implement qilish kerak (PSDIGEST). Hozircha
    # ko'p NVR oddiy auth qabul qiladi.
    envelope = f"""<?xml version="1.0" encoding="UTF-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope">
  <s:Header>
    <wsse:Security xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
      <wsse:UsernameToken>
        <wsse:Username>{username}</wsse:Username>
        <wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">{password}</wsse:Password>
      </wsse:UsernameToken>
    </wsse:Security>
  </s:Header>
  <s:Body>{body}</s:Body>
</s:Envelope>"""
    return envelope.encode("utf-8")


def _onvif_parse_profiles(xml_text: str) -> List[Dict]:
    """ONVIF GetProfilesResponse'dan profile token va name'lari."""
    profiles = []
    try:
        # Namespace'larsiz oddiy regex bilan parse (XML namespace mashaqalı)
        for m in re.finditer(r'<[^:>]*:?Profiles[^>]*token="([^"]+)"[^>]*>(.*?)</[^:>]*:?Profiles>',
                              xml_text, re.DOTALL):
            token = m.group(1)
            inner = m.group(2)
            name_m = re.search(r'<[^:>]*:?Name>([^<]+)</[^:>]*:?Name>', inner)
            name = name_m.group(1) if name_m else token
            profiles.append({"token": token, "name": name})
    except Exception:
        pass
    return profiles


# ============ Endpoint ============

@router.post("/nvr/connect", response_model=NVRConnectOut)
async def nvr_connect(data: NVRConnectIn):
    """NVR ga ulanib BARCHA kameralarni qaytarish.

    Avtomatik aniqlaydi: Hikvision / Dahua / ONVIF
    """
    if not HAS_HTTPX:
        raise HTTPException(500, "httpx kutubxonasi o'rnatilmagan. pip install httpx")

    # Avval IP+port mavjudligini tekshirish
    if not _is_host_reachable(data.ip, data.port):
        raise HTTPException(400, f"NVR'ga ulana olmaymiz: {data.ip}:{data.port}. "
                                  f"IP manzil to'g'rimi? NVR yoqilganmi?")

    # Tartib bilan urinish
    last_error = None
    for method_name, fn in (("Hikvision", _hikvision_connect),
                              ("Dahua", _dahua_connect),
                              ("ONVIF", _onvif_connect)):
        try:
            result = await fn(data)
            if result and result.channels:
                print(f"[NVR] Muvaffaqiyat: {method_name} — {len(result.channels)} kanal")
                return result
        except HTTPException:
            raise
        except Exception as e:
            last_error = f"{method_name}: {e}"
            print(f"[NVR] {method_name} xato: {e}")
            continue

    raise HTTPException(
        404,
        f"NVR turi aniqlanmadi. Tekshirib ko'ring: "
        f"IP={data.ip}, port={data.port}. "
        f"NVR Hikvision/Dahua/ONVIF qo'llab-quvvatlaydi. "
        f"Xato: {last_error or 'noma''lum'}"
    )


def _is_host_reachable(ip: str, port: int, timeout: float = 2.0) -> bool:
    """Tezkor TCP probe."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        try:
            s.connect((ip, port))
            return True
        finally:
            s.close()
    except Exception:
        return False


# ============ Bulk import (NVR'dagi kameralarni Sergak AI'ga qo'shish) ============

class NVRBulkImportIn(BaseModel):
    department_id: Optional[int] = None
    channels: List[Dict]  # NVRChannel format
    nvr_ip: str = ""
    prefix: str = "Kanal"  # nom prefix
    default_modules: Optional[List[str]] = None  # default: hamma .pt'li modullar


@router.post("/nvr/import")
async def nvr_bulk_import(data: NVRBulkImportIn):
    """Tanlangan NVR kanallarini DB'ga qo'shish + barcha modullarni avtomatik yoqish."""
    from app.core.database import AsyncSessionLocal
    from app.models.camera import Camera
    from app.models.module import Module
    from sqlalchemy import select
    from pathlib import Path

    async with AsyncSessionLocal() as db:
        # Avtomatik: bor bo'lgan barcha .pt'li modullarni topish
        if data.default_modules is None:
            modules = (await db.execute(select(Module).where(Module.enabled == True))).scalars().all()  # noqa
            auto_modules = [m.key for m in modules
                            if m.model_path and Path(m.model_path).exists()]
            # Agar hech qaysisi yo'q bo'lsa, kamida helmet ni yoqamiz
            if not auto_modules:
                auto_modules = ["helmet"]
        else:
            auto_modules = data.default_modules

        added = 0
        skipped = 0
        for ch in data.channels:
            rtsp = ch.get("rtsp_url") or ""
            if not rtsp:
                skipped += 1
                continue
            name = ch.get("name") or f"{data.prefix} {ch.get('id', '?')}"
            cam = Camera(
                name=name,
                location=f"NVR {data.nvr_ip} · CH{ch.get('id', '?')}",
                rtsp_url=rtsp,
                ip=data.nvr_ip,
                department_id=data.department_id,
                modules_enabled=auto_modules.copy(),
                online=ch.get("online", True),
                confidence_threshold=0.65,
                cooldown_sec=60,
            )
            db.add(cam)
            added += 1
        await db.commit()

    return {
        "ok": True,
        "added": added,
        "skipped": skipped,
        "modules_enabled": auto_modules,
        "message": f"{added} ta kamera qo'shildi, har biriga {len(auto_modules)} ta modul yoqildi"
    }
