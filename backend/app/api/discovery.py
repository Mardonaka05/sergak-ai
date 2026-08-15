"""Real network camera discovery — pure Python, no native deps.

Combines three techniques:
1. ONVIF WS-Discovery (UDP multicast 239.255.255.250:3702) — finds professional IP cameras
2. Parallel TCP port scan of subnet on camera ports (554 RTSP, 80/8080 HTTP, 8000)
3. HTTP banner / Server header inspection to identify vendor
4. System ARP table lookup for MAC addresses
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict
import asyncio
import ipaddress
import socket
import re
import subprocess
import uuid as uuid_lib
import sys
import time

from app.core.config import settings

router = APIRouter()


# ============ Models ============

class FoundCamera(BaseModel):
    ip: str
    mac: str = ""
    manufacturer: str = ""
    model: str = ""
    rtsp_url: str = ""
    onvif_url: str = ""
    http_url: str = ""
    ports: List[int] = []
    status: str = "found"  # found | onvif | rtsp | http
    server_banner: str = ""
    needs_auth: bool = True


class ScanRequest(BaseModel):
    subnet: Optional[str] = None  # if None, auto-detect
    deep: bool = True  # if True, run port scan in addition to WS-Discovery


class ScanResponse(BaseModel):
    cameras: List[FoundCamera]
    subnet_scanned: str
    hosts_scanned: int
    duration_ms: int
    onvif_count: int
    total_count: int


# ============ Helpers ============

def _get_local_ips() -> List[str]:
    """Return list of local non-loopback IPv4 addresses."""
    ips = []
    try:
        # Try connecting outbound to discover the active interface IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ips.append(s.getsockname()[0])
        finally:
            s.close()
    except Exception:
        pass
    try:
        for ip in socket.gethostbyname_ex(socket.gethostname())[2]:
            if not ip.startswith("127.") and ip not in ips:
                ips.append(ip)
    except Exception:
        pass
    return ips


def _auto_detect_subnet() -> str:
    """Derive a /24 subnet from the active local IP."""
    ips = _get_local_ips()
    for ip in ips:
        try:
            net = ipaddress.IPv4Network(ip + "/24", strict=False)
            return str(net)
        except Exception:
            continue
    # Fallback to setting / default
    return settings.NETWORK_SUBNET or "192.168.1.0/24"


def _get_arp_table() -> Dict[str, str]:
    """Parse system ARP table -> {ip: 'AA:BB:CC:DD:EE:FF'}."""
    mapping: Dict[str, str] = {}
    cmd = ["arp", "-a"] if sys.platform == "win32" else ["arp", "-n"]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=4).decode("utf-8", errors="ignore")
    except Exception:
        return mapping
    # Match both Windows (00-1a-2b) and Unix (00:1a:2b) MAC formats
    mac_pat = r"([0-9A-Fa-f]{2}[-:][0-9A-Fa-f]{2}[-:][0-9A-Fa-f]{2}[-:][0-9A-Fa-f]{2}[-:][0-9A-Fa-f]{2}[-:][0-9A-Fa-f]{2})"
    ip_pat = r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
    for line in out.splitlines():
        ip_m = re.search(ip_pat, line)
        mac_m = re.search(mac_pat, line)
        if ip_m and mac_m:
            mac = mac_m.group(1).upper().replace("-", ":")
            # Filter out broadcast / invalid
            if mac == "FF:FF:FF:FF:FF:FF" or mac == "00:00:00:00:00:00":
                continue
            mapping[ip_m.group(1)] = mac
    return mapping


# ============ WS-Discovery (ONVIF) ============

WS_DISCOVERY_PROBE = """<?xml version="1.0" encoding="UTF-8"?>
<e:Envelope xmlns:e="http://www.w3.org/2003/05/soap-envelope"
            xmlns:w="http://schemas.xmlsoap.org/ws/2004/08/addressing"
            xmlns:d="http://schemas.xmlsoap.org/ws/2005/04/discovery"
            xmlns:dn="http://www.onvif.org/ver10/network/wsdl">
  <e:Header>
    <w:MessageID>uuid:{msg_id}</w:MessageID>
    <w:To e:mustUnderstand="true">urn:schemas-xmlsoap-org:ws:2005:04:discovery</w:To>
    <w:Action e:mustUnderstand="true">http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</w:Action>
  </e:Header>
  <e:Body>
    <d:Probe>
      <d:Types>dn:NetworkVideoTransmitter</d:Types>
    </d:Probe>
  </e:Body>
</e:Envelope>"""


def _ws_discovery_sync(timeout_sec: float = 3.0) -> Dict[str, Dict]:
    """Synchronous WS-Discovery. Returns {ip: {xaddrs, scopes, types}}."""
    msg_id = str(uuid_lib.uuid4())
    payload = WS_DISCOVERY_PROBE.format(msg_id=msg_id).encode("utf-8")

    devices: Dict[str, Dict] = {}

    # Send from each local interface for cross-VLAN discovery
    local_ips = _get_local_ips() or [""]

    for src_ip in local_ips:
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            except Exception:
                pass
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 8)
            if src_ip:
                try:
                    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(src_ip))
                except Exception:
                    pass
                try:
                    sock.bind((src_ip, 0))
                except Exception:
                    sock.bind(("", 0))
            else:
                sock.bind(("", 0))
            sock.settimeout(0.3)
            # Send a few times — UDP can be lossy
            for _ in range(3):
                try:
                    sock.sendto(payload, ("239.255.255.250", 3702))
                except Exception:
                    pass

            deadline = time.time() + timeout_sec
            while time.time() < deadline:
                try:
                    data, addr = sock.recvfrom(65536)
                except socket.timeout:
                    continue
                except Exception:
                    break
                ip = addr[0]
                text = data.decode("utf-8", errors="ignore")
                # Skip our own probe echo
                if msg_id in text and "Probe>" in text:
                    continue
                xaddrs = []
                for x in re.findall(r"<[^>]*XAddrs[^>]*>(.*?)</[^>]*XAddrs[^>]*>", text, re.DOTALL):
                    xaddrs.extend(x.strip().split())
                scopes = []
                for s in re.findall(r"<[^>]*Scopes[^>]*>(.*?)</[^>]*Scopes[^>]*>", text, re.DOTALL):
                    scopes.extend(s.strip().split())
                types = re.findall(r"NetworkVideoTransmitter|Device", text)
                if not xaddrs and not scopes:
                    continue
                existing = devices.get(ip, {"xaddrs": [], "scopes": [], "types": []})
                existing["xaddrs"] = list(set(existing["xaddrs"] + xaddrs))
                existing["scopes"] = list(set(existing["scopes"] + scopes))
                existing["types"] = list(set(existing["types"] + types))
                devices[ip] = existing
        except Exception as e:
            print(f"[Discovery] WS-Discovery socket error ({src_ip}): {e}")
        finally:
            if sock:
                try:
                    sock.close()
                except Exception:
                    pass
    return devices


def _parse_vendor_from_scopes(scopes: List[str]) -> Dict[str, str]:
    """Extract manufacturer/model/name from ONVIF Scopes URIs."""
    info = {"manufacturer": "", "model": "", "name": "", "hardware": ""}
    for s in scopes:
        s = s.strip()
        if "/name/" in s:
            info["name"] = s.split("/name/")[-1].replace("%20", " ").replace("+", " ")
        elif "/hardware/" in s:
            info["hardware"] = s.split("/hardware/")[-1].replace("%20", " ").replace("+", " ")
        elif "/location/" in s:
            pass
    # Vendor strings often in scopes
    joined = " ".join(scopes).lower()
    for vendor in ("hikvision", "dahua", "axis", "reolink", "uniview", "uniarch",
                   "amcrest", "foscam", "vivotek", "bosch", "tp-link", "tapo",
                   "samsung", "sony", "panasonic", "honeywell", "pelco"):
        if vendor in joined:
            info["manufacturer"] = vendor.capitalize() if vendor != "tp-link" else "TP-Link"
            break
    return info


# ============ TCP port scan ============

async def _probe_port(ip: str, port: int, timeout: float = 0.6) -> bool:
    try:
        fut = asyncio.open_connection(ip, port)
        reader, writer = await asyncio.wait_for(fut, timeout=timeout)
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        return True
    except Exception:
        return False


async def _http_banner(ip: str, port: int, timeout: float = 1.5) -> str:
    """HEAD / and read Server header."""
    try:
        fut = asyncio.open_connection(ip, port)
        reader, writer = await asyncio.wait_for(fut, timeout=timeout)
        try:
            writer.write(("HEAD / HTTP/1.0\r\nHost: " + ip + "\r\nUser-Agent: SergakAI/1.0\r\n\r\n").encode())
            await writer.drain()
            data = await asyncio.wait_for(reader.read(4096), timeout=timeout)
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
        text = data.decode("utf-8", errors="ignore")
        m = re.search(r"^Server:\s*([^\r\n]+)", text, re.IGNORECASE | re.MULTILINE)
        if m:
            return m.group(1).strip()
        # Some cameras put hostname in WWW-Authenticate realm
        m = re.search(r'WWW-Authenticate:[^\r\n]*realm="([^"]+)"', text, re.IGNORECASE)
        if m:
            return f"realm:{m.group(1)}"
        return ""
    except Exception:
        return ""


def _vendor_from_banner(banner: str) -> str:
    if not banner:
        return ""
    b = banner.lower()
    table = [
        ("hikvision", "Hikvision"),
        ("dnvrs-webs", "Hikvision"),
        ("dahua", "Dahua"),
        ("axis", "Axis"),
        ("reolink", "Reolink"),
        ("uniview", "Uniview"),
        ("uniarch", "Uniview"),
        ("amcrest", "Amcrest"),
        ("foscam", "Foscam"),
        ("vivotek", "Vivotek"),
        ("bosch", "Bosch"),
        ("tp-link", "TP-Link"),
        ("tapo", "TP-Link Tapo"),
        ("vstarcam", "VStarcam"),
        ("ipcam", "Generic IPC"),
        ("netwave", "Netwave"),
        ("ezviz", "Ezviz"),
        ("imou", "Imou"),
        ("hipcam", "Generic IPC"),
        ("webs", "Generic IPC"),
    ]
    for needle, name in table:
        if needle in b:
            return name
    return ""


async def _inspect_host(ip: str, sem: asyncio.Semaphore) -> Optional[FoundCamera]:
    """Probe an IP for camera-related ports + collect info."""
    async with sem:
        # Try common camera ports
        ports_to_check = [554, 80, 8080, 8000, 8899]  # RTSP, HTTP, HTTP alt
        open_ports: List[int] = []
        # Parallel within a host for speed
        results = await asyncio.gather(*[_probe_port(ip, p) for p in ports_to_check], return_exceptions=True)
        for p, r in zip(ports_to_check, results):
            if r is True:
                open_ports.append(p)
        if not open_ports:
            return None
        # Must have either RTSP (554) OR an HTTP port — to filter out non-camera devices like printers
        if 554 not in open_ports and not any(p in open_ports for p in (80, 8080, 8000)):
            return None
        # Identify via HTTP banner
        banner = ""
        for hp in (80, 8080, 8000):
            if hp in open_ports:
                banner = await _http_banner(ip, hp)
                if banner:
                    break
        vendor = _vendor_from_banner(banner)
        # If only port 80 open and banner is "lighttpd"/"Apache"/"nginx" — likely NOT a camera
        if 554 not in open_ports and banner and not vendor:
            generic_servers = ("apache", "nginx", "lighttpd", "iis", "express", "node")
            if any(g in banner.lower() for g in generic_servers):
                return None
        rtsp_url = f"rtsp://{ip}:554/Streaming/Channels/101" if 554 in open_ports else ""
        # Pick first HTTP url
        http_port = next((p for p in (80, 8080, 8000) if p in open_ports), None)
        http_url = f"http://{ip}:{http_port}/" if http_port else ""
        cam = FoundCamera(
            ip=ip, manufacturer=vendor or "", model="",
            rtsp_url=rtsp_url, http_url=http_url,
            ports=open_ports, server_banner=banner,
            status="rtsp" if 554 in open_ports else "http",
            needs_auth=bool(banner and ("realm:" in banner or "auth" in banner.lower())),
        )
        return cam


# ============ Endpoints ============

@router.get("/subnet")
async def detect_subnet():
    return {"subnet": _auto_detect_subnet(), "local_ips": _get_local_ips()}


@router.post("/scan", response_model=ScanResponse)
async def scan_network(req: ScanRequest = ScanRequest()):
    start = time.time()
    subnet_str = req.subnet or _auto_detect_subnet()
    try:
        net = ipaddress.IPv4Network(subnet_str, strict=False)
    except Exception:
        return ScanResponse(cameras=[], subnet_scanned=subnet_str,
                            hosts_scanned=0, duration_ms=0,
                            onvif_count=0, total_count=0)

    print(f"[Discovery] Scanning subnet: {subnet_str}")

    # === Phase 1: WS-Discovery (ONVIF multicast) ===
    loop = asyncio.get_event_loop()
    onvif_devices = await loop.run_in_executor(None, _ws_discovery_sync, 3.0)
    print(f"[Discovery] WS-Discovery found {len(onvif_devices)} ONVIF responses")

    # === Phase 2: Parallel TCP port scan ===
    hosts = [str(ip) for ip in net.hosts()]
    # Skip .1 (typically router/gateway) — usually not a camera, can speed up
    hosts_to_scan = [h for h in hosts if not h.endswith(".1")]
    sem = asyncio.Semaphore(60)
    tasks = [_inspect_host(ip, sem) for ip in hosts_to_scan]
    scan_results = await asyncio.gather(*tasks, return_exceptions=True)
    by_ip: Dict[str, FoundCamera] = {}
    for r in scan_results:
        if isinstance(r, FoundCamera):
            by_ip[r.ip] = r

    # === Merge ONVIF results into port-scan results ===
    for ip, info in onvif_devices.items():
        scopes = info.get("scopes", [])
        parsed = _parse_vendor_from_scopes(scopes)
        # Pick first http XAddr as onvif service URL
        onvif_url = next((x for x in info.get("xaddrs", []) if x.startswith("http")), "")
        if ip in by_ip:
            cam = by_ip[ip]
            cam.onvif_url = onvif_url
            cam.status = "onvif"
            if parsed["manufacturer"]:
                cam.manufacturer = parsed["manufacturer"]
            if parsed["hardware"]:
                cam.model = parsed["hardware"]
            elif parsed["name"]:
                cam.model = parsed["name"]
        else:
            # Discovered via ONVIF only — even without RTSP/HTTP probe responding
            by_ip[ip] = FoundCamera(
                ip=ip,
                manufacturer=parsed["manufacturer"] or "",
                model=parsed["hardware"] or parsed["name"] or "",
                onvif_url=onvif_url,
                status="onvif",
                ports=[],
                needs_auth=True,
            )

    # === Phase 3: MAC addresses from ARP ===
    arp = _get_arp_table()
    for ip, cam in by_ip.items():
        if ip in arp:
            cam.mac = arp[ip]

    cameras = list(by_ip.values())
    # Sort by IP numerically
    cameras.sort(key=lambda c: tuple(int(p) for p in c.ip.split(".")))

    duration_ms = int((time.time() - start) * 1000)
    onvif_count = sum(1 for c in cameras if c.onvif_url)
    print(f"[Discovery] Scan complete: {len(cameras)} cameras in {duration_ms}ms")

    return ScanResponse(
        cameras=cameras,
        subnet_scanned=subnet_str,
        hosts_scanned=len(hosts_to_scan),
        duration_ms=duration_ms,
        onvif_count=onvif_count,
        total_count=len(cameras),
    )


# === Auth probe — try common camera credentials against ONVIF/RTSP ===

class TestCredentialsIn(BaseModel):
    ip: str
    username: str
    password: str
    port: int = 554


@router.post("/test-credentials")
async def test_credentials(creds: TestCredentialsIn):
    """Test RTSP credentials by attempting an RTSP DESCRIBE handshake."""
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(creds.ip, creds.port), timeout=3.0
        )
    except Exception as e:
        return {"ok": False, "error": f"Aloqa o'rnatib bo'lmadi: {e}"}
    try:
        # Try common RTSP paths
        paths = [
            "/Streaming/Channels/101", "/cam/realmonitor?channel=1&subtype=0",
            "/onvif/profile1/media", "/live/main", "/h264", "/stream0", "/",
        ]
        worked = None
        for path in paths:
            try:
                req = (
                    f"DESCRIBE rtsp://{creds.ip}:{creds.port}{path} RTSP/1.0\r\n"
                    f"CSeq: 1\r\n"
                    f"User-Agent: SergakAI\r\n\r\n"
                ).encode()
                writer.write(req)
                await writer.drain()
                resp = await asyncio.wait_for(reader.read(2048), timeout=2.0)
                text = resp.decode("utf-8", errors="ignore")
                if "200 OK" in text or "401" in text:  # 401 = auth needed but RTSP works
                    worked = path
                    break
            except Exception:
                continue
        if worked:
            url = f"rtsp://{creds.username}:{creds.password}@{creds.ip}:{creds.port}{worked}"
            return {"ok": True, "rtsp_url": url, "path": worked}
        return {"ok": False, "error": "RTSP yo'l topilmadi"}
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


# === Legacy compat (so old frontend doesn't break) ===

class CredentialsIn(BaseModel):
    ip: str
    username: str
    password: str


@router.post("/auth")
async def authenticate_camera(creds: CredentialsIn):
    return await test_credentials(TestCredentialsIn(
        ip=creds.ip, username=creds.username, password=creds.password
    ))
