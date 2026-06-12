import sys
import subprocess

def _install(pkg):
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", pkg, "-q",
             "--break-system-packages"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False

for _pkg, _imp in [("PyQt6", "PyQt6"), ("requests", "requests"), ("Pillow", "PIL")]:
    try:
        __import__(_imp)
    except ImportError:
        if not _install(_pkg):
            print(f"ModuleNotFoundError: {_imp}")
            sys.exit(1)

import io
import re
import time
import socket
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton,
    QScrollArea, QFrame,
    QSizePolicy, QGraphicsOpacityEffect,
    QLineEdit, QTextEdit,
    QStackedWidget,
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal,
    QPropertyAnimation, QEasingCurve,
    QSize, QTimer, QPoint,
    QAbstractAnimation, pyqtProperty,
)
from PyQt6.QtGui import (
    QColor, QPainter, QPixmap, QImage, QFont,
    QPen, QBrush, QIcon, QFontMetrics,
    QPalette, QCursor,
)
from PIL import Image, ImageDraw, ImageFont as PILFont

P = {
    "bg":       "#0e0f11",
    "sidebar":  "#111214",
    "panel":    "#16171a",
    "card":     "#1a1b20",
    "card_sel": "#252734",
    "card_hov": "#1d1e25",
    "border":   "#2a2c35",
    "accent":   "#5865f2",
    "accent2":  "#4752c4",
    "danger":   "#ed4245",
    "danger2":  "#b83234",
    "success":  "#57f287",
    "warn":     "#faa61a",
    "muted":    "#6b7280",
    "sub":      "#9ca3af",
    "text":     "#e2e4e9",
    "white":    "#ffffff",
    "inp":      "#13141a",
    "tag":      "#1f2028",
    "log_bg":   "#0a0b0d",
}

AV_COLS = ["#5865f2", "#ed4245", "#faa61a", "#57f287",
           "#eb459e", "#3ba55c", "#9b59b6", "#e67e22"]

BASE             = "https://discord.com/api/v9"
CDN              = "https://cdn.discordapp.com"
DISCORD_ICON_URL = (
    "https://assets-global.prod.discord.com"
    "/assets/847541504914fd33810e70a0ea73177e.ico"
)

def _hdrs(tok: str) -> dict:
    return {
        "Authorization": tok,
        "Content-Type":  "application/json",
        "User-Agent":    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

def _pil_to_qpixmap(img: Image.Image) -> QPixmap:
    buf = io.BytesIO()
    img.save(buf, "PNG")
    buf.seek(0)
    return QPixmap.fromImage(QImage.fromData(buf.read()))

def _aa_circle_pil(img: Image.Image, size: int) -> QPixmap:
    S    = size * 4
    img  = img.resize((S, S), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, S - 1, S - 1), fill=255)
    out  = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    out.paste(img, mask=mask)
    return _pil_to_qpixmap(out.resize((size, size), Image.LANCZOS))

def _initials_pixmap(name: str, size: int) -> QPixmap:
    col = AV_COLS[sum(ord(c) for c in name) % len(AV_COLS)]
    S   = size * 4
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    d.ellipse((0, 0, S - 1, S - 1), fill=col)
    letter = name[0].upper() if name else "?"
    fnt    = None
    for face in ("segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"):
        try:
            fnt = PILFont.truetype(face, int(S * .42))
            break
        except Exception:
            pass
    if fnt:
        bb = d.textbbox((0, 0), letter, font=fnt)
        tw, th = bb[2] - bb[0], bb[3] - bb[1]
        d.text(((S - tw) / 2 - bb[0], (S - th) / 2 - bb[1]),
               letter, fill="#fff", font=fnt)
    else:
        d.text((S // 2 - 10, S // 2 - 14), letter, fill="#fff")
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, S - 1, S - 1), fill=255)
    out  = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    out.paste(img, mask=mask)
    return _pil_to_qpixmap(out.resize((size, size), Image.LANCZOS))

def _fetch_url_pixmap(url: str, size: int) -> QPixmap | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            data = r.read()
        return _aa_circle_pil(Image.open(io.BytesIO(data)).convert("RGBA"), size)
    except Exception:
        return None

class NetCheckWorker(QThread):
    result = pyqtSignal(bool)

    def run(self):
        for host, port in [("8.8.8.8", 53), ("1.1.1.1", 53), ("9.9.9.9", 53)]:
            try:
                s = socket.create_connection((host, port), timeout=3)
                s.close()
                self.result.emit(True)
                return
            except OSError:
                pass
        self.result.emit(False)

class TokenValidateWorker(QThread):
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)

    def __init__(self, token: str):
        super().__init__()
        self.token = token.strip()

    def run(self):
        if not self.token:
            self.failure.emit("Please enter a token.")
            return
        try:
            r = requests.get(f"{BASE}/users/@me",
                             headers=_hdrs(self.token), timeout=8)
            if r.status_code == 200:
                info  = r.json()
                uid   = info.get("id", "")
                uname = info.get("username", "Unknown")
                avid  = info.get("avatar", "")
                av_url = (
                    f"{CDN}/avatars/{uid}/{avid}"
                    f".{'gif' if avid.startswith('a_') else 'png'}?size=256"
                    if avid else ""
                )
                self.success.emit({
                    "id":            uid,
                    "username":      uname,
                    "global_name":   info.get("global_name") or uname,
                    "discriminator": info.get("discriminator", "0"),
                    "avatar_url":    av_url,
                })
            elif r.status_code == 401:
                self.failure.emit("Invalid token — authentication failed.")
            elif r.status_code == 429:
                self.failure.emit("Rate limited. Please wait a moment and try again.")
            else:
                self.failure.emit(f"Discord returned status {r.status_code}.")
        except requests.exceptions.ConnectionError:
            self.failure.emit("No internet connection.")
        except requests.exceptions.Timeout:
            self.failure.emit("Request timed out. Check your connection.")
        except Exception as ex:
            self.failure.emit(f"Unexpected error: {ex}")

class ParallelAvatarLoader(QThread):
    avatar_ready = pyqtSignal(int, object)
    all_done     = pyqtSignal()
    BATCH_SIZE   = 8

    def __init__(self, dms: list, size: int = 36):
        super().__init__()
        self.dms   = dms
        self.size  = size
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        def _fetch_one(args):
            idx, dm = args
            if self._stop:
                return idx, None
            url = dm.get("avatar_url", "")
            px  = _fetch_url_pixmap(url, self.size) if url else None
            return idx, px or _initials_pixmap(dm["name"], self.size)

        with ThreadPoolExecutor(max_workers=self.BATCH_SIZE) as pool:
            futures = {pool.submit(_fetch_one, (i, dm)): i
                       for i, dm in enumerate(self.dms)}
            for future in futures:
                if self._stop:
                    break
                try:
                    idx, px = future.result()
                    if px is not None:
                        self.avatar_ready.emit(idx, px)
                except Exception:
                    pass
        self.all_done.emit()

class DMLoader(QThread):
    done  = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, token: str):
        super().__init__()
        self.token = token

    def run(self):
        if not self.token:
            self.error.emit("No token available.")
            self.done.emit([])
            return
        try:
            r = requests.get(f"{BASE}/users/@me/channels",
                             headers=_hdrs(self.token), timeout=10)
            if r.status_code != 200:
                self.error.emit(f"API error {r.status_code} loading channels.")
                self.done.emit([])
                return
            dms = []
            for ch in r.json():
                if ch.get("type") != 1:
                    continue
                recips = ch.get("recipients", [])
                if not recips:
                    continue
                u    = recips[0]
                uid2 = u.get("id", "")
                avid = u.get("avatar", "")
                av_url = (
                    f"{CDN}/avatars/{uid2}/{avid}"
                    f".{'gif' if avid.startswith('a_') else 'png'}?size=80"
                    if avid and uid2 else ""
                )
                dms.append({
                    "id":         ch["id"],
                    "name":       u.get("username", "Unknown"),
                    "avatar_url": av_url,
                })
            self.done.emit(dms)
        except Exception as ex:
            self.error.emit(f"Exception in DMLoader: {ex}")
            self.done.emit([])

class PurgeWorker(QThread):
    log     = pyqtSignal(str, str)
    deleted = pyqtSignal(int)
    done    = pyqtSignal(int)

    def __init__(self, token: str, account_id: str, channels: list, delay: float):
        super().__init__()
        self.token    = token
        self.aid      = account_id
        self.channels = channels
        self.delay    = delay
        self._stop    = False

    def stop(self):
        self._stop = True

    def run(self):
        if not self.token:
            self.done.emit(0)
            return
        try:
            me_id = requests.get(
                f"{BASE}/users/@me", headers=_hdrs(self.token), timeout=6
            ).json()["id"]
        except Exception:
            self.done.emit(0)
            return

        total = 0
        for ch_id, ch_name in self.channels:
            if self._stop:
                break
            self.log.emit(f"━━  Purging DM with {ch_name}…", "inf")
            before = None
            while not self._stop:
                params = {"limit": 100}
                if before:
                    params["before"] = before
                try:
                    r = requests.get(
                        f"{BASE}/channels/{ch_id}/messages",
                        headers=_hdrs(self.token), params=params, timeout=10)
                except Exception:
                    break
                if r.status_code == 429:
                    wait = r.json().get("retry_after", 2)
                    self.log.emit(f"⚠  Rate limited {wait:.1f}s", "wrn")
                    time.sleep(wait)
                    continue
                if r.status_code != 200:
                    self.log.emit(f"✗  Fetch failed ({r.status_code})", "err")
                    break
                msgs = r.json()
                if not msgs:
                    self.log.emit(f"✓  {ch_name} — done.", "ok")
                    break
                mine   = [m for m in msgs if m["author"]["id"] == me_id]
                before = msgs[-1]["id"]
                if not mine:
                    if len(msgs) < 100:
                        self.log.emit(f"✓  {ch_name} — start.", "ok")
                        break
                    continue
                for msg in mine:
                    if self._stop:
                        break
                    try:
                        d = requests.delete(
                            f"{BASE}/channels/{ch_id}/messages/{msg['id']}",
                            headers=_hdrs(self.token), timeout=10)
                    except Exception:
                        continue
                    if d.status_code == 204:
                        total += 1
                        self.log.emit(
                            f"🗑  [{total}]  "
                            f"{(msg.get('content') or '[attachment]')[:60]}", "ok")
                        self.deleted.emit(total)
                    elif d.status_code == 429:
                        wait = d.json().get("retry_after", 2)
                        self.log.emit(f"⚠  Rate limited {wait:.1f}s", "wrn")
                        time.sleep(wait)
                    elif d.status_code == 404:
                        self.log.emit("⚠  Already gone.", "dim")
                    time.sleep(self.delay)
        self.done.emit(total)

class AvatarLabel(QLabel):
    def __init__(self, size: int = 40, parent=None):
        super().__init__(parent)
        self._sz  = size
        self._pix = None
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def set_pixmap(self, px: QPixmap):
        if px:
            self._pix = px.scaled(
                self._sz, self._sz,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation)
        else:
            self._pix = None
        self.update()

    def paintEvent(self, _):
        if not self._pix:
            return
        sz  = self._sz
        sz2 = sz * 2
        mask = QPixmap(sz2, sz2)
        mask.fill(Qt.GlobalColor.transparent)
        mp = QPainter(mask)
        mp.setRenderHint(QPainter.RenderHint.Antialiasing)
        mp.setBrush(QBrush(Qt.GlobalColor.white))
        mp.setPen(Qt.PenStyle.NoPen)
        mp.drawEllipse(0, 0, sz2, sz2)
        mp.end()
        src = self._pix.scaled(
            sz2, sz2,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation)
        if src.width() != sz2 or src.height() != sz2:
            x = (src.width()  - sz2) // 2
            y = (src.height() - sz2) // 2
            src = src.copy(x, y, sz2, sz2)
        mp2 = QPainter(mask)
        mp2.setRenderHint(QPainter.RenderHint.Antialiasing)
        mp2.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        mp2.drawPixmap(0, 0, src)
        mp2.end()
        final = mask.scaled(
            sz, sz,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.drawPixmap(0, 0, final)
        p.end()

class AnimatedBtn(QPushButton):
    def __init__(self, text: str, bg: str, bg_h: str,
                 fg: str = "#ffffff", radius: int = 9, h: int = 36,
                 parent=None):
        super().__init__(text, parent)
        self._bg  = QColor(bg)
        self._bgh = QColor(bg_h)
        self._fg  = fg
        self._r   = radius
        self._cur = QColor(bg)
        self.setFixedHeight(h)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFont(QFont("Segoe UI", 10))
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._anim = QPropertyAnimation(self, b"_anim_color", self)
        self._anim.setDuration(140)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def _get_col(self): return self._cur
    def _set_col(self, c): self._cur = c; self.update()
    _anim_color = pyqtProperty(QColor, _get_col, _set_col)

    def enterEvent(self, e):
        if self.isEnabled(): self._fade(self._bgh)
    def leaveEvent(self, e):
        if self.isEnabled(): self._fade(self._bg)

    def _fade(self, target: QColor):
        self._anim.stop()
        self._anim.setStartValue(self._cur)
        self._anim.setEndValue(target)
        self._anim.start()

    def setEnabled(self, v: bool):
        super().setEnabled(v)
        self._cur = self._bg if v else QColor(P["tag"])
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        col = self._cur if self.isEnabled() else QColor(P["tag"])
        p.setBrush(QBrush(col))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(self.rect(), self._r, self._r)
        p.setPen(QColor(P["muted"] if not self.isEnabled() else self._fg))
        p.setFont(self.font())
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())
        p.end()

    def sizeHint(self):
        fm = QFontMetrics(self.font())
        return QSize(fm.horizontalAdvance(self.text()) + 36, self.height())

class SmoothScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._anim = QPropertyAnimation(self.verticalScrollBar(), b"value")
        self._anim.setDuration(300)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def wheelEvent(self, e):
        delta   = e.angleDelta().y()
        current = self.verticalScrollBar().value()
        target  = max(self.verticalScrollBar().minimum(),
                      min(self.verticalScrollBar().maximum(),
                          current - int(delta * 0.8)))
        self._anim.stop()
        self._anim.setStartValue(current)
        self._anim.setEndValue(target)
        self._anim.start()
        e.accept()

class DMCard(QWidget):
    clicked = pyqtSignal(object)

    def __init__(self, dm: dict, px: QPixmap = None, parent=None):
        super().__init__(parent)
        self.dm       = dm
        self.checked  = False
        self._hovered = False
        self._col     = QColor(P["card"])
        self.setFixedHeight(60)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self._anim = QPropertyAnimation(self, b"_bg_color")
        self._anim.setDuration(130)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 0, 12, 0)
        lay.setSpacing(10)

        self._chk_lbl = QLabel()
        self._chk_lbl.setFixedSize(20, 20)
        self._chk_lbl.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        lay.addWidget(self._chk_lbl)

        self._av = AvatarLabel(36)
        lay.addWidget(self._av)

        txt = QWidget()
        txt.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        tl  = QVBoxLayout(txt)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.setSpacing(1)
        self._name = QLabel(dm["name"])
        self._name.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        self._name.setStyleSheet(f"color: {P['text']};")
        self._sub  = QLabel("Direct Message")
        self._sub.setFont(QFont("Segoe UI", 8))
        self._sub.setStyleSheet(f"color: {P['muted']};")
        tl.addWidget(self._name)
        tl.addWidget(self._sub)
        lay.addWidget(txt, 1)

        self._draw_chk(False)
        if px is not None:
            self._av.set_pixmap(px)

    def set_avatar(self, px: QPixmap):
        self._av.set_pixmap(px)

    def _get_bg(self): return self._col
    def _set_bg(self, c): self._col = c; self.update()
    _bg_color = pyqtProperty(QColor, _get_bg, _set_bg)

    def _target_color(self):
        if self.checked:  return QColor(P["card_sel"])
        if self._hovered: return QColor(P["card_hov"])
        return QColor(P["card"])

    def _animate_to(self, col: QColor):
        self._anim.stop()
        self._anim.setStartValue(self._col)
        self._anim.setEndValue(col)
        self._anim.start()

    def _draw_chk(self, checked: bool):
        sz = 20
        px = QPixmap(sz, sz)
        px.fill(Qt.GlobalColor.transparent)
        p  = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if checked:
            p.setBrush(QBrush(QColor(P["accent"])))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(0, 0, sz, sz, 6, 6)
            pen = QPen(QColor("#fff"), 2.2)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            p.setPen(pen)
            p.drawLine(5, 10, 8, 14)
            p.drawLine(8, 14, 15, 6)
        else:
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.setPen(QPen(QColor(P["border"]), 1.5))
            p.drawRoundedRect(1, 1, sz - 2, sz - 2, 5, 5)
        p.end()
        self._chk_lbl.setPixmap(px)

    def set_checked(self, v: bool):
        self.checked = v
        self._draw_chk(v)
        self._name.setStyleSheet(
            f"color: {P['white'] if v else P['text']};")
        self._animate_to(self._target_color())

    def enterEvent(self, e):
        self._hovered = True
        if not self.checked: self._animate_to(QColor(P["card_hov"]))
    def leaveEvent(self, e):
        self._hovered = False
        if not self.checked: self._animate_to(QColor(P["card"]))
    def mousePressEvent(self, _):
        self.clicked.emit(self)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(self._col))
        p.setPen(QPen(QColor(P["accent"] if self.checked else P["border"]), 1))
        p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 10, 10)
        p.end()
        super().paintEvent(_)

class SearchBox(QWidget):
    textChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 0, 10, 0)
        lay.setSpacing(6)

        icon = QLabel("🔍")
        icon.setFont(QFont("Segoe UI", 10))
        icon.setFixedSize(20, 20)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet(f"color: {P['muted']}; background: transparent;")
        lay.addWidget(icon)

        self._e = QLineEdit()
        self._e.setPlaceholderText("Search conversations…")
        self._e.setStyleSheet(f"""
            QLineEdit {{
                background: transparent; border: none;
                color: {P['text']}; font: 10pt 'Segoe UI';
            }}
        """)
        self._e.textChanged.connect(self.textChanged)
        lay.addWidget(self._e, 1)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(QColor(P["inp"])))
        p.setPen(QPen(QColor(P["border"]), 1))
        p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 8, 8)
        p.end()
        super().paintEvent(_)

class LogView(QTextEdit):
    TAGS = {
        "ok":  P["success"],
        "err": P["danger"],
        "inf": P["accent"],
        "wrn": P["warn"],
        "dim": P["muted"],
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 9))
        self.setStyleSheet(f"""
            QTextEdit {{
                background: {P['log_bg']}; color: {P['sub']};
                border: none; border-radius: 10px; padding: 10px;
            }}
            QScrollBar:vertical {{
                background: {P['log_bg']}; width: 4px; border-radius: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {P['border']}; border-radius: 2px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

    def append_log(self, msg: str, tag: str = "inf"):
        col = self.TAGS.get(tag, P["sub"])
        self.append(f'<span style="color:{col};">{msg}</span>')
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

class SecureTokenInput(QLineEdit):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEchoMode(QLineEdit.EchoMode.Password)

    def keyPressEvent(self, event):
        if (event.modifiers() == Qt.KeyboardModifier.ControlModifier
                and event.key() in (Qt.Key.Key_C, Qt.Key.Key_X)):
            event.ignore()
            return
        super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        event.ignore()

class AccountInfoWidget(QWidget):
    _FETCH_SIZE   = 256
    _DISPLAY_SIZE = 40

    def __init__(self, account: dict, parent=None):
        super().__init__(parent)
        self.account  = account
        self._radius  = 12
        self.setFixedHeight(68)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(12)

        self._av = AvatarLabel(self._DISPLAY_SIZE)
        lay.addWidget(self._av)

        info_col = QWidget()
        info_col.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        ic = QVBoxLayout(info_col)
        ic.setContentsMargins(0, 0, 0, 0)
        ic.setSpacing(0)

        self._name_lbl = QLabel(
            account.get("global_name") or account.get("username", ""))
        name_font = QFont()
        name_font.setWeight(QFont.Weight.DemiBold)
        name_font.setPointSize(10)
        for face in ("Segoe UI Symbol", "Arial Unicode MS", "Noto Sans", "Segoe UI"):
            name_font.setFamily(face)
            if QFontMetrics(name_font).horizontalAdvance("𝔾") > 0:
                break
        self._name_lbl.setFont(name_font)
        self._name_lbl.setFixedHeight(16)
        self._name_lbl.setStyleSheet(
            f"color: {P['white']}; background: transparent;")
        ic.addWidget(self._name_lbl)

        uname   = account.get("username", "")
        disc    = account.get("discriminator", "0")
        tag_str = f"@{uname}" if disc == "0" else f"{uname}#{disc}"
        self._tag_lbl = QLabel(tag_str)
        self._tag_lbl.setFont(QFont("Segoe UI", 8))
        self._tag_lbl.setFixedHeight(13)
        self._tag_lbl.setStyleSheet(
            f"color: {P['muted']}; background: transparent;")
        ic.addWidget(self._tag_lbl)

        lay.addWidget(info_col, 1)
        QTimer.singleShot(0, self._load_avatar)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(QColor(P["card"])))
        p.setPen(QPen(QColor(P["border"]), 1))
        p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1),
                          self._radius, self._radius)
        p.end()
        super().paintEvent(_)

    def _load_avatar(self):
        raw_url = self.account.get("avatar_url", "")
        url     = re.sub(r"[?&]size=\d+", f"?size={self._FETCH_SIZE}", raw_url)
        disp    = self._DISPLAY_SIZE

        if url:
            class _Loader(QThread):
                done = pyqtSignal(object)
                def __init__(self, u, sz):
                    super().__init__()
                    self._u = u; self._sz = sz
                def run(self_):
                    self_.done.emit(_fetch_url_pixmap(self_._u, self_._sz))

            self._av_thread = _Loader(url, disp)
            self._av_thread.done.connect(
                lambda px: self._av.set_pixmap(px) if px else None)
            self._av_thread.start()
        else:
            self._av.set_pixmap(
                _initials_pixmap(self.account.get("username", "?"), disp))

class LoginScreen(QWidget):
    login_success = pyqtSignal(dict, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {P['bg']};")
        self._worker = None

        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QWidget()
        card.setFixedWidth(420)
        card.setStyleSheet(f"QWidget {{ background: {P['panel']}; border-radius: 16px; }}")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(36, 36, 36, 36)
        cl.setSpacing(0)

        logo = QLabel("💬")
        logo.setFont(QFont("Segoe UI", 28))
        logo.setStyleSheet("background: transparent;")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.addWidget(logo)
        cl.addSpacing(12)

        title = QLabel("Discord DM Purger")
        title.setFont(QFont("Segoe UI", 17, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {P['white']}; background: transparent;")
        cl.addWidget(title)
        cl.addSpacing(4)

        sub = QLabel("Enter your Discord token to continue")
        sub.setFont(QFont("Segoe UI", 10))
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(f"color: {P['muted']}; background: transparent;")
        cl.addWidget(sub)
        cl.addSpacing(28)

        tok_lbl = QLabel("USER TOKEN")
        tok_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        tok_lbl.setStyleSheet(
            f"color: {P['muted']}; letter-spacing: 1px; background: transparent;")
        cl.addWidget(tok_lbl)
        cl.addSpacing(6)

        self._inp = SecureTokenInput()
        self._inp.setPlaceholderText("Paste your token here…")
        self._inp.setFixedHeight(44)
        self._inp.setFont(QFont("Segoe UI", 10))
        self._inp.setStyleSheet(f"""
            QLineEdit {{
                background: {P['inp']};
                border: 1.5px solid {P['border']};
                border-radius: 8px;
                color: {P['text']};
                padding: 0 14px;
            }}
            QLineEdit:focus {{ border: 1.5px solid {P['accent']}; }}
        """)
        self._inp.returnPressed.connect(self._attempt_login)
        cl.addWidget(self._inp)
        cl.addSpacing(20)

        self._err_lbl = QLabel("")
        self._err_lbl.setFont(QFont("Segoe UI", 9))
        self._err_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._err_lbl.setWordWrap(True)
        self._err_lbl.setStyleSheet(
            f"color: {P['danger']}; background: transparent;")
        self._err_lbl.setVisible(False)
        cl.addWidget(self._err_lbl)

        self._login_btn = AnimatedBtn(
            "Validate & Continue", bg=P["accent"], bg_h=P["accent2"],
            h=44, radius=10)
        self._login_btn.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._login_btn.clicked.connect(self._attempt_login)
        cl.addSpacing(8)
        cl.addWidget(self._login_btn)

        self._status_lbl = QLabel("")
        self._status_lbl.setFont(QFont("Segoe UI", 9))
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_lbl.setStyleSheet(
            f"color: {P['muted']}; background: transparent;")
        cl.addSpacing(10)
        cl.addWidget(self._status_lbl)

        outer.addWidget(card, 0, Qt.AlignmentFlag.AlignCenter)

    def _attempt_login(self):
        token = self._inp.text().strip()
        if not token:
            self._show_error("Please paste your token first.")
            return
        self._set_loading(True)
        self._worker = TokenValidateWorker(token)
        self._worker.success.connect(lambda acc: self.login_success.emit(acc, token))
        self._worker.failure.connect(self._on_failure)
        self._worker.start()

    def _on_failure(self, msg: str):
        self._set_loading(False)
        self._show_error(msg)

    def _show_error(self, msg: str):
        self._err_lbl.setText(f"✗  {msg}")
        self._err_lbl.setVisible(True)
        orig = self._inp.pos()
        anim = QPropertyAnimation(self._inp, b"pos", self._inp)
        anim.setDuration(300)
        anim.setEasingCurve(QEasingCurve.Type.OutElastic)
        anim.setKeyValueAt(0,   orig)
        anim.setKeyValueAt(0.2, orig + QPoint(-6, 0))
        anim.setKeyValueAt(0.4, orig + QPoint(6, 0))
        anim.setKeyValueAt(0.6, orig + QPoint(-4, 0))
        anim.setKeyValueAt(0.8, orig + QPoint(4, 0))
        anim.setEndValue(orig)
        anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def _set_loading(self, loading: bool):
        self._login_btn.setEnabled(not loading)
        self._inp.setEnabled(not loading)
        self._status_lbl.setText("Validating token…" if loading else "")
        if loading:
            self._err_lbl.setVisible(False)

class MainWindow(QMainWindow):
    _sig_log = pyqtSignal(str, str)
    _sig_del = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Discord DM Purger")
        self.resize(980, 700)
        self.setMinimumSize(840, 560)

        self._active_account: dict | None = None
        self._active_token:   str         = ""
        self._dm_cards:       list        = []
        self._purge_worker:   PurgeWorker | None = None
        self._all_selected:   bool        = False

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._login_screen = LoginScreen()
        self._login_screen.login_success.connect(self._on_login_success)
        self._stack.addWidget(self._login_screen)

        self._main_page: QWidget | None = None

        self._net_timer = QTimer(self)
        self._net_timer.timeout.connect(self._check_net)

        self._load_app_icon()

    def _load_app_icon(self):
        class _IconWorker(QThread):
            loaded = pyqtSignal(QPixmap)
            def run(self_):
                try:
                    req = urllib.request.Request(
                        DISCORD_ICON_URL, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=5) as r:
                        data = r.read()
                    img = Image.open(io.BytesIO(data)).convert("RGBA")
                    self_.loaded.emit(_pil_to_qpixmap(img.resize((64, 64), Image.LANCZOS)))
                except Exception:
                    pass

        w = _IconWorker(self)
        w.loaded.connect(self._apply_icon, Qt.ConnectionType.QueuedConnection)
        w.start()
        self._icon_thread = w

    def _apply_icon(self, px: QPixmap):
        icon = QIcon(px)
        self.setWindowIcon(icon)
        QApplication.instance().setWindowIcon(icon)

    def _on_login_success(self, account: dict, token: str):
        self._active_account = account
        self._active_token   = token
        self._main_page      = self._build_main_page(account)
        self._stack.addWidget(self._main_page)

        self._sig_log.connect(lambda m, t: self._log.append_log(m, t))
        self._sig_del.connect(lambda n: (
            self._del_lbl.setText(f"Deleted: {n}"),
            self._stat_lbl.setText(f"Deleting…  {n} gone"),
        ))

        self._fade_transition()
        QTimer.singleShot(500, self._check_net)
        QTimer.singleShot(500, self._load_dms)
        self._net_timer.start(15000)

    def _fade_transition(self):
        eff_out  = QGraphicsOpacityEffect(self._login_screen)
        self._login_screen.setGraphicsEffect(eff_out)
        anim_out = QPropertyAnimation(eff_out, b"opacity", self)
        anim_out.setDuration(300)
        anim_out.setStartValue(1.0)
        anim_out.setEndValue(0.0)
        anim_out.setEasingCurve(QEasingCurve.Type.OutCubic)

        def _switch():
            self._stack.setCurrentWidget(self._main_page)
            eff_in  = QGraphicsOpacityEffect(self._main_page)
            self._main_page.setGraphicsEffect(eff_in)
            anim_in = QPropertyAnimation(eff_in, b"opacity", self)
            anim_in.setDuration(400)
            anim_in.setStartValue(0.0)
            anim_in.setEndValue(1.0)
            anim_in.setEasingCurve(QEasingCurve.Type.OutCubic)
            anim_in.finished.connect(lambda: self._main_page.setGraphicsEffect(None))
            anim_in.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
            self._anim_in = anim_in

        anim_out.finished.connect(_switch)
        anim_out.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
        self._anim_out = anim_out

    def _build_main_page(self, account: dict) -> QWidget:
        root = QWidget()
        root.setStyleSheet(f"background: {P['bg']};")
        rl = QVBoxLayout(root)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)

        top = QWidget()
        top.setFixedHeight(52)
        top.setStyleSheet(f"background: {P['sidebar']};")
        tl = QHBoxLayout(top)
        tl.setContentsMargins(18, 0, 18, 0)
        tl.setSpacing(10)

        title = QLabel("Discord DM Purger")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {P['white']};")
        tl.addWidget(title)
        tl.addStretch()

        self._net_dot = QLabel("●")
        self._net_dot.setFont(QFont("Segoe UI", 9))
        self._net_dot.setStyleSheet(f"color: {P['muted']};")
        tl.addWidget(self._net_dot)

        self._net_lbl = QLabel("Checking…")
        self._net_lbl.setFont(QFont("Segoe UI", 9))
        self._net_lbl.setStyleSheet(f"color: {P['muted']};")
        tl.addWidget(self._net_lbl)

        rl.addWidget(top)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {P['border']};")
        rl.addWidget(sep)

        body = QWidget()
        bl   = QHBoxLayout(body)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(0)
        rl.addWidget(body, 1)

        sb = QWidget()
        sb.setFixedWidth(300)
        sb.setStyleSheet(f"background: {P['sidebar']};")
        sl = QVBoxLayout(sb)
        sl.setContentsMargins(14, 14, 14, 14)
        sl.setSpacing(0)

        acct_lbl = QLabel("ACCOUNT")
        acct_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        acct_lbl.setStyleSheet(
            f"color: {P['muted']}; letter-spacing: 1px; background: transparent;")
        sl.addWidget(acct_lbl)
        sl.addSpacing(8)

        self._acct_info = AccountInfoWidget(account)
        sl.addWidget(self._acct_info)
        sl.addSpacing(16)

        sep2 = QFrame()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet(f"background: {P['border']};")
        sl.addWidget(sep2)
        sl.addSpacing(10)

        conv_hdr = QWidget()
        conv_hdr.setStyleSheet("background: transparent;")
        chl = QHBoxLayout(conv_hdr)
        chl.setContentsMargins(0, 0, 0, 0)
        chl.setSpacing(0)

        self._conv_lbl = QLabel("CONVERSATIONS")
        self._conv_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        self._conv_lbl.setStyleSheet(
            f"color: {P['muted']}; letter-spacing: 1px; background: transparent;")
        chl.addWidget(self._conv_lbl)
        chl.addStretch()

        self._selall_btn = QPushButton("Select all")
        self._selall_btn.setFont(QFont("Segoe UI", 8))
        self._selall_btn.setStyleSheet(f"""
            QPushButton {{ color:{P['accent']}; background:transparent; border:none; padding:0; }}
            QPushButton:hover {{ color:{P['accent2']}; }}
            QPushButton:disabled {{ color:{P['muted']}; }}
        """)
        self._selall_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._selall_btn.setEnabled(False)
        self._selall_btn.clicked.connect(self._toggle_select_all)
        chl.addWidget(self._selall_btn)
        sl.addWidget(conv_hdr)
        sl.addSpacing(6)

        self._search = SearchBox()
        self._search.textChanged.connect(self._filter_cards)
        sl.addWidget(self._search)
        sl.addSpacing(8)

        self._scroll = SmoothScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{ background: transparent; width: 3px; }}
            QScrollBar::handle:vertical {{
                background: {P['border']}; border-radius: 1px; min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        self._cards_w = QWidget()
        self._cards_w.setStyleSheet("background: transparent;")
        self._cards_l = QVBoxLayout(self._cards_w)
        self._cards_l.setContentsMargins(0, 0, 4, 0)
        self._cards_l.setSpacing(4)
        self._cards_l.addStretch()
        self._scroll.setWidget(self._cards_w)
        sl.addWidget(self._scroll, 1)

        bl.addWidget(sb)

        div = QFrame()
        div.setFixedWidth(1)
        div.setStyleSheet(f"background: {P['border']};")
        bl.addWidget(div)

        rp = QWidget()
        rp.setStyleSheet(f"background: {P['bg']};")
        rpl = QVBoxLayout(rp)
        rpl.setContentsMargins(20, 16, 20, 16)
        rpl.setSpacing(10)

        info = QWidget()
        info.setFixedHeight(52)
        info.setStyleSheet(f"background: {P['panel']}; border-radius: 10px;")
        il = QHBoxLayout(info)
        il.setContentsMargins(14, 0, 14, 0)
        il.setSpacing(10)

        self._info_av = AvatarLabel(34)
        il.addWidget(self._info_av)

        self._info_name = QLabel("")
        self._info_name.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        self._info_name.setStyleSheet(
            f"color: {P['sub']}; background: transparent;")
        il.addWidget(self._info_name, 1)

        self._info_badge = QLabel("")
        self._info_badge.setFont(QFont("Segoe UI", 8))
        self._info_badge.setStyleSheet(
            f"color: {P['muted']}; background: transparent;")
        il.addWidget(self._info_badge)

        rpl.addWidget(info)

        ctrl = QWidget()
        ctrl.setStyleSheet(f"background: {P['panel']}; border-radius: 10px;")
        ctl = QHBoxLayout(ctrl)
        ctl.setContentsMargins(16, 10, 16, 10)
        ctl.setSpacing(10)

        dl = QLabel("DELAY")
        dl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        dl.setStyleSheet(
            f"color: {P['muted']}; letter-spacing: 1px; background: transparent;")
        ctl.addWidget(dl)

        self._delay_val = 0.8
        delay_wrap = QWidget()
        delay_wrap.setStyleSheet("background: transparent;")
        dw = QHBoxLayout(delay_wrap)
        dw.setContentsMargins(0, 0, 0, 0)
        dw.setSpacing(0)

        self._delay_minus = AnimatedBtn("−", bg=P["tag"], bg_h=P["border"], h=32)
        self._delay_minus.setFixedWidth(30)
        self._delay_minus.clicked.connect(self._delay_dec)
        dw.addWidget(self._delay_minus)

        self._delay_lbl = QLabel(f"{self._delay_val:.1f} s")
        self._delay_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._delay_lbl.setFixedWidth(54)
        self._delay_lbl.setStyleSheet(f"""
            color: {P['text']}; font: 10pt 'Segoe UI';
            background: {P['inp']};
            border-top: 1px solid {P['border']};
            border-bottom: 1px solid {P['border']};
            padding: 4px 0;
        """)
        dw.addWidget(self._delay_lbl)

        self._delay_plus = AnimatedBtn("+", bg=P["tag"], bg_h=P["border"], h=32)
        self._delay_plus.setFixedWidth(30)
        self._delay_plus.clicked.connect(self._delay_inc)
        dw.addWidget(self._delay_plus)

        ctl.addWidget(delay_wrap)
        ctl.addStretch()

        self._start_btn = AnimatedBtn("▶  Start Purge",
                                      bg=P["accent"], bg_h=P["accent2"])
        self._start_btn.setEnabled(False)
        self._start_btn.clicked.connect(self._start_purge)
        ctl.addWidget(self._start_btn)

        self._stop_btn = AnimatedBtn("⏹  Stop",
                                     bg=P["danger"], bg_h=P["danger2"])
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._stop_purge)
        ctl.addWidget(self._stop_btn)

        rpl.addWidget(ctrl)

        log_hdr = QWidget()
        log_hdr.setStyleSheet("background: transparent;")
        lhl = QHBoxLayout(log_hdr)
        lhl.setContentsMargins(2, 0, 2, 0)

        lt = QLabel("ACTIVITY LOG")
        lt.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        lt.setStyleSheet(f"color: {P['muted']}; letter-spacing: 1px;")
        lhl.addWidget(lt)
        lhl.addStretch()

        self._del_lbl = QLabel("")
        self._del_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        self._del_lbl.setStyleSheet(f"color: {P['success']};")
        lhl.addWidget(self._del_lbl)

        rpl.addWidget(log_hdr)

        self._log = LogView()
        rpl.addWidget(self._log, 1)

        self._stat_lbl = QLabel("Loading conversations…")
        self._stat_lbl.setFont(QFont("Segoe UI", 8))
        self._stat_lbl.setStyleSheet(f"color: {P['muted']};")
        rpl.addWidget(self._stat_lbl)

        bl.addWidget(rp, 1)
        return root

    def _check_net(self):
        w = NetCheckWorker(self)
        w.result.connect(self._on_net)
        w.start()
        self._net_worker = w

    def _on_net(self, ok: bool):
        colour = P["success"] if ok else P["danger"]
        text   = "Connected" if ok else "No internet"
        self._net_dot.setStyleSheet(f"color: {colour};")
        self._net_lbl.setStyleSheet(f"color: {colour};")
        self._net_lbl.setText(text)

    def _load_dms(self):
        self._log.append_log(
            f"✓  Logged in as {self._active_account.get('username', '')}.", "ok")
        self._log.append_log("Loading DMs…", "inf")
        self._conv_lbl.setText("CONVERSATIONS  (loading…)")
        self._selall_btn.setEnabled(False)
        self._clear_cards()
        w = DMLoader(self._active_token)
        w.done.connect(self._on_dms_loaded)
        w.error.connect(lambda msg: self._log.append_log(f"✗  {msg}", "err"))
        w.start()
        self._dm_loader = w

    def _on_dms_loaded(self, dms: list):
        self._clear_cards()
        if not dms:
            self._log.append_log("No DMs found.", "wrn")
            self._conv_lbl.setText("CONVERSATIONS  (0)")
            self._stat_lbl.setText("No conversations found.")
            return

        for dm in dms:
            card = DMCard(dm, _initials_pixmap(dm["name"], 36))
            card.clicked.connect(self._on_card_clicked)
            self._cards_l.insertWidget(self._cards_l.count() - 1, card)
            self._dm_cards.append(card)

        self._conv_lbl.setText(f"CONVERSATIONS  ({len(dms)})")
        self._selall_btn.setEnabled(True)
        self._stat_lbl.setText("Ready.")
        self._log.append_log(f"✓  {len(dms)} conversations — loading avatars…", "ok")

        if hasattr(self, "_av_loader") and self._av_loader.isRunning():
            self._av_loader.stop()

        loader = ParallelAvatarLoader(dms, size=36)
        loader.avatar_ready.connect(self._on_avatar_ready)
        loader.all_done.connect(
            lambda: self._log.append_log("✓  All avatars loaded.", "dim"))
        loader.start()
        self._av_loader = loader

    def _on_avatar_ready(self, idx: int, px):
        if 0 <= idx < len(self._dm_cards):
            self._dm_cards[idx].set_avatar(px)

    def _on_card_clicked(self, card: DMCard):
        card.set_checked(not card.checked)
        self._refresh_selection()

    def _refresh_selection(self):
        sel = [c for c in self._dm_cards if c.checked]
        if not sel:
            self._start_btn.setEnabled(False)
            self._info_name.setText("")
            self._info_badge.setText("")
            self._info_av._pix = None
            self._info_av.update()
            return
        self._start_btn.setEnabled(True)
        if len(sel) == 1:
            px = sel[0].dm.get("_px36") or sel[0]._av._pix
            if px:
                self._info_av.set_pixmap(px)
            self._info_name.setText(sel[0].dm["name"])
            self._info_name.setStyleSheet(
                f"color: {P['white']}; background: transparent;")
            self._info_badge.setText("")
        else:
            self._info_av._pix = None
            self._info_av.update()
            self._info_name.setText(f"{len(sel)} DMs selected")
            self._info_name.setStyleSheet(
                f"color: {P['white']}; background: transparent;")
            self._info_badge.setText("")

    def _toggle_select_all(self):
        self._all_selected = not self._all_selected
        self._selall_btn.setText(
            "Deselect all" if self._all_selected else "Select all")
        for c in self._dm_cards:
            if c.isVisible():
                c.set_checked(self._all_selected)
        self._refresh_selection()

    def _filter_cards(self, q: str):
        q = q.lower()
        for c in self._dm_cards:
            c.setVisible(not q or q in c.dm["name"].lower())

    def _clear_cards(self):
        for c in self._dm_cards:
            self._cards_l.removeWidget(c)
            c.deleteLater()
        self._dm_cards.clear()
        self._start_btn.setEnabled(False)
        self._info_name.setText("")
        self._info_badge.setText("")

    def _delay_dec(self):
        self._delay_val = max(0.3, round(self._delay_val - 0.1, 1))
        self._delay_lbl.setText(f"{self._delay_val:.1f} s")

    def _delay_inc(self):
        self._delay_val = min(10.0, round(self._delay_val + 0.1, 1))
        self._delay_lbl.setText(f"{self._delay_val:.1f} s")

    def _start_purge(self):
        if not self._active_account:
            return
        targets = [(c.dm["id"], c.dm["name"])
                   for c in self._dm_cards if c.checked]
        if not targets:
            return
        self._lock_ui(True)
        self._del_lbl.setText("")
        w = PurgeWorker(self._active_token, self._active_account["id"],
                        targets, self._delay_val)
        w.log.connect(lambda m, t: self._sig_log.emit(m, t))
        w.deleted.connect(lambda n: self._sig_del.emit(n))
        w.done.connect(self._on_purge_done)
        w.start()
        self._purge_worker = w

    def _stop_purge(self):
        if self._purge_worker:
            self._purge_worker.stop()
            self._log.append_log("⏹  Stop requested…", "wrn")

    def _on_purge_done(self, total: int):
        self._lock_ui(False)
        self._log.append_log(f"✅  Done — {total} message(s) deleted.", "ok")
        self._stat_lbl.setText(f"Done — {total} deleted.")
        self._del_lbl.setText(f"Deleted: {total}")

    def _lock_ui(self, lock: bool):
        for w in (self._start_btn, self._selall_btn, self._search._e,
                  self._delay_minus, self._delay_plus):
            w.setEnabled(not lock)
        self._stop_btn.setEnabled(lock)
        for c in self._dm_cards:
            c.setEnabled(not lock)
        opacity = 0.35 if lock else 1.0
        for w in (self._selall_btn, self._search, self._scroll):
            eff  = QGraphicsOpacityEffect(w)
            w.setGraphicsEffect(eff)
            anim = QPropertyAnimation(eff, b"opacity", w)
            anim.setDuration(200)
            anim.setStartValue(1.0)
            anim.setEndValue(opacity)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    pal = app.palette()
    pal.setColor(QPalette.ColorRole.Window,     QColor(P["bg"]))
    pal.setColor(QPalette.ColorRole.WindowText, QColor(P["text"]))
    pal.setColor(QPalette.ColorRole.Base,       QColor(P["inp"]))
    pal.setColor(QPalette.ColorRole.Text,       QColor(P["text"]))
    app.setPalette(pal)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
