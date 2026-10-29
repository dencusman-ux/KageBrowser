import sys
import os
import re
import json
import datetime
import subprocess

from PyQt6.QtGui import (
    QIcon, QFont, QKeySequence, QShortcut, QPixmap, QPainter, QFontMetrics, QAction,
    QPainterPath, QColor, QPen
)
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QProgressBar, QLabel, QToolBar,
    QFrame, QTabBar, QSizePolicy, QStackedWidget, QToolButton, QScrollArea,
    QFileDialog, QMenu, QGraphicsOpacityEffect
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEngineProfile, QWebEnginePage, QWebEngineSettings, QWebEngineUrlRequestInterceptor,
    QWebEngineDownloadRequest
)
from PyQt6.QtCore import (
    QUrl, Qt, QSize, QEvent, QByteArray, pyqtSignal, QPoint,
    QPropertyAnimation, QEasingCurve, QVariantAnimation, QTimer, QRectF
)


def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)


def format_size(bytes_val):
    if bytes_val <= 0:
        return '0 Б'
    if bytes_val < 1024:
        return f'{bytes_val} Б'
    elif bytes_val < 1048576:
        return f'{bytes_val / 1024:.1f} КБ'
    elif bytes_val < 1073741824:
        return f'{bytes_val / 1048576:.1f} МБ'
    return f'{bytes_val / 1073741824:.2f} ГБ'


CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.kagebrowser', 'config.json')


def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {'download_dir': os.path.join(os.path.expanduser('~'), 'Downloads')}


def save_config(cfg):
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


SVG_PATHS = {
    'back': "<line x1='19' y1='12' x2='5' y2='12'/><polyline points='12 19 5 12 12 5'/>",
    'forward': "<line x1='5' y1='12' x2='19' y2='12'/><polyline points='12 5 19 12 12 19'/>",
    'reload': "<path d='M23 4v6h-6'/><path d='M20.49 15a9 9 0 1 1-2.12-9.36L23 10'/>",
    'stop': "<line x1='18' y1='6' x2='6' y2='18'/><line x1='6' y1='6' x2='18' y2='18'/>",
    'plus': "<line x1='12' y1='5' x2='12' y2='19'/><line x1='5' y1='12' x2='19' y2='12'/>",
    'close': "<line x1='18' y1='6' x2='6' y2='18'/><line x1='6' y1='6' x2='18' y2='18'/>",
    'search': "<circle cx='11' cy='11' r='7'/><line x1='21' y1='21' x2='16.65' y2='16.65'/>",
    'globe': "<circle cx='12' cy='12' r='10'/><line x1='2' y1='12' x2='22' y2='12'/><ellipse cx='12' cy='12' rx='4.5' ry='10'/>",
    'chevron_up': "<polyline points='18 15 12 9 6 15'/>",
    'chevron_down': "<polyline points='6 9 12 15 18 9'/>",
    'download': "<path d='M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4'/><polyline points='7 10 12 15 17 10'/><line x1='12' y1='15' x2='12' y2='3'/>",
    'folder': "<path d='M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z'/>",
    'file_open': "<path d='M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6'/><polyline points='15 3 21 3 21 9'/><line x1='10' y1='14' x2='21' y2='3'/>",
    'edit': "<path d='M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7'/><path d='M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z'/>",
    'copy': "<rect x='9' y='9' width='13' height='13' rx='2' ry='2'/><path d='M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1'/>",
    'trash': "<polyline points='3 6 5 6 21 6'/><path d='M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2'/>"
}


def get_svg_icon(name, color='#d4d4d4', disabled_color='#383838', render_size=96, stroke_width='2.2'):
    def make_pix(c):
        s = f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='{c}' stroke-width='{stroke_width}' stroke-linecap='round' stroke-linejoin='round'>{SVG_PATHS[name]}</svg>"
        r = QSvgRenderer(QByteArray(s.encode('utf-8')))
        p = QPixmap(render_size, render_size)
        p.fill(Qt.GlobalColor.transparent)
        ptr = QPainter(p)
        ptr.setRenderHint(QPainter.RenderHint.Antialiasing)
        r.render(ptr)
        ptr.end()
        return p

    icon = QIcon()
    icon.addPixmap(make_pix(color), QIcon.Mode.Normal)
    icon.addPixmap(make_pix(disabled_color), QIcon.Mode.Disabled)
    return icon


RU_TRANSLATIONS = {
    'Back': 'Назад',
    'Forward': 'Вперёд',
    'Reload': 'Перезагрузить',
    'Stop': 'Остановить',
    'Save page': 'Сохранить страницу',
    'Save page as...': 'Сохранить страницу как...',
    'Open link in new tab': 'Открыть ссылку в новой вкладке',
    'Open link in new window': 'Открыть ссылку в новом окне',
    'Save link': 'Сохранить ссылку',
    'Save link as...': 'Сохранить ссылку как...',
    'Copy link address': 'Копировать адрес ссылки',
    'Copy link text': 'Копировать текст ссылки',
    'Open image in new tab': 'Открыть изображение в новой вкладке',
    'Save image': 'Сохранить изображение',
    'Save image as...': 'Сохранить изображение как...',
    'Copy image': 'Копировать изображение',
    'Copy image address': 'Копировать адрес изображения',
    'Open media in new tab': 'Открыть медиа в новой вкладке',
    'Save media': 'Сохранить медиа',
    'Save media as...': 'Сохранить медиа как...',
    'Copy media address': 'Копировать адрес медиа',
    'Toggle media play/pause': 'Воспроизведение / Пауза',
    'Toggle media mute': 'Включить / отключить звук',
    'Toggle media loop': 'Зациклить',
    'Toggle media controls': 'Элементы управления',
    'Cut': 'Вырезать',
    'Copy': 'Копировать',
    'Paste': 'Вставить',
    'Paste and match style': 'Вставить без форматирования',
    'Select all': 'Выделить всё',
    'Undo': 'Отменить',
    'Redo': 'Повторить',
    'Inspect': 'Просмотреть код',
    'Inspect element': 'Исследовать элемент',
    'View page source': 'Исходный код страницы',
    'View source': 'Исходный код',
    'Search for': 'Искать в интернете',
    'Print': 'Печать...',
    'Print...': 'Печать...',
    'Exit full screen': 'Выйти из полноэкранного режима'
}


SEARCH_ENGINE = 'https://duckduckgo.com/?q='

KAGESEC_HOME = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Новая вкладка</title>
<style>
*{box-sizing:border-box}body{background:radial-gradient(circle at 50% 38%,#141414 0%,#000000 100%);color:#fff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:100vh;margin:0;overflow:hidden}
.main-wrapper{text-align:center;width:760px;max-width:94vw;display:flex;flex-direction:column;align-items:center}
.logo{font-size:56px;font-weight:700;letter-spacing:-1.5px;margin-bottom:28px;text-shadow:0 2px 16px rgba(255,255,255,0.12)}
.search-wrapper{position:relative;width:100%;margin-bottom:20px}
.search-box{width:100%;height:48px;background:#111;border:1px solid #282828;border-radius:24px;color:#fff;padding:0 50px 0 24px;outline:none;font-size:14px;font-family:inherit;transition:all .25s ease;box-shadow:0 4px 20px rgba(0,0,0,0.5)}
.search-box:focus{border-color:#555;background:#181818;box-shadow:0 0 0 3px rgba(255,255,255,0.08),0 6px 24px rgba(0,0,0,0.7)}
.search-box::placeholder{color:#555}
.search-submit-btn{position:absolute;right:8px;top:50%;transform:translateY(-50%) scale(0.8);opacity:0;pointer-events:none;background:#252525;border:1px solid #383838;border-radius:50%;width:32px;height:32px;display:flex;align-items:center;justify-content:center;cursor:pointer;transition:all .2s ease}
.search-submit-btn.visible{opacity:1;pointer-events:auto;transform:translateY(-50%) scale(1)}
.search-submit-btn:hover{background:#333;border-color:#555}
.engines{display:flex;justify-content:center;gap:8px;margin-bottom:36px;flex-wrap:wrap}
.engine-btn{background:#101010;border:1px solid #222;color:#777;padding:6px 14px;border-radius:20px;cursor:pointer;font-size:11px;font-weight:500;transition:all .2s ease;text-transform:uppercase;letter-spacing:0.5px}
.engine-btn:hover{border-color:#444;color:#ddd;background:#1a1a1a;transform:translateY(-1px)}
.engine-btn.active{border-color:#666;color:#fff;background:#222;box-shadow:0 2px 10px rgba(0,0,0,0.5)}
.shortcuts{display:flex;justify-content:center;gap:20px;width:100%;flex-wrap:wrap;align-items:flex-start}
.shortcut-item{position:relative;display:flex;flex-direction:column;align-items:center;width:76px;transition:transform .25s ease}
.shortcut-item:hover{transform:translateY(-4px)}
.shortcut{text-decoration:none;color:#777;display:flex;flex-direction:column;align-items:center;gap:10px;padding:12px 6px;border-radius:18px;transition:background-color .25s ease;width:76px;cursor:pointer}
.shortcut-item:hover .shortcut{background:rgba(255,255,255,0.04)}
.shortcut-item:hover .icon{border-color:#555;color:#fff;background:#1a1a1a;box-shadow:0 8px 22px rgba(0,0,0,0.6)}
.shortcut-item:hover .name{color:#fff}
.icon{width:50px;height:50px;border:1px solid #222;border-radius:18px;display:flex;align-items:center;justify-content:center;font-size:15px;background:#0e0e0e;transition:all .25s ease;font-weight:600;color:#888;box-shadow:0 4px 14px rgba(0,0,0,0.3)}
.name{font-size:11px;text-transform:uppercase;letter-spacing:0.8px;font-weight:500;transition:color .2s ease;text-align:center;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:70px}
.action-btn{position:absolute;width:18px;height:18px;border-radius:50%;background:#181818;border:1px solid #323232;color:#888;display:flex;align-items:center;justify-content:center;cursor:pointer;transition:opacity .2s ease,transform .15s ease,background .15s ease;padding:0;box-shadow:0 2px 8px rgba(0,0,0,0.6);opacity:0;pointer-events:none;z-index:10}
.shortcut-item:hover .action-btn{opacity:1;pointer-events:auto}
.action-btn:hover{background:#2a2a2a;color:#fff;border-color:#555;transform:scale(1.15)}
.action-btn.delete-btn:hover{background:#8b1e1e;border-color:#c42b1c;color:#fff}
.action-btn svg{width:10px;height:10px}
.action-btn.edit-btn{top:2px;left:2px}
.action-btn.delete-btn{top:2px;right:2px}
.shortcut-item.add-item{opacity:0.4;transition:opacity .25s ease,transform .25s ease}
.shortcut-item.add-item:hover{opacity:1;transform:translateY(-4px)}
.add-icon{border:1px solid #222;background:#0e0e0e;color:#777}
.shortcut-item.add-item:hover .add-icon{border-color:#555;color:#fff;background:#1a1a1a}
.modal-overlay{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.75);backdrop-filter:blur(6px);align-items:center;justify-content:center;z-index:200}
.modal-overlay.active{display:flex}
.modal-content{background:#111;border:1px solid #282828;border-radius:18px;padding:24px 28px;width:360px;box-shadow:0 16px 48px rgba(0,0,0,0.9);display:flex;flex-direction:column;gap:14px;animation:modalPop .2s ease}
@keyframes modalPop{from{opacity:0;transform:scale(0.95)}to{opacity:1;transform:scale(1)}}
.modal-title{font-size:16px;font-weight:700;color:#fff;letter-spacing:-0.2px}
.modal-field{display:flex;flex-direction:column;gap:6px;text-align:left}
.modal-field label{font-size:11px;font-weight:600;color:#888;text-transform:uppercase;letter-spacing:0.6px}
.modal-field input{height:38px;background:#181818;border:1px solid #2c2c2c;border-radius:10px;color:#fff;padding:0 12px;font-size:13px;font-family:inherit;outline:none;transition:border-color .2s ease}
.modal-field input:focus{border-color:#555;background:#1e1e1e}
.modal-buttons{display:flex;justify-content:flex-end;gap:10px;margin-top:6px}
.modal-btn{padding:8px 18px;border-radius:10px;font-size:12px;font-weight:600;cursor:pointer;border:none;transition:all .15s ease}
.btn-cancel{background:#1c1c1c;color:#888;border:1px solid #2c2c2c}
.btn-cancel:hover{background:#262626;color:#ccc;border-color:#444}
.btn-save{background:#0088cc;color:#fff}
.btn-save:hover{background:#0099e6;box-shadow:0 0 12px rgba(0,136,204,0.3)}
.footer-brand{position:absolute;bottom:20px;right:24px;font-size:11px;color:#444;letter-spacing:0.8px}
.support-btn{position:absolute;bottom:20px;left:24px;font-size:10px;color:#666;text-decoration:none;border:1px solid #222;border-radius:14px;padding:6px 12px;transition:all .25s ease;letter-spacing:0.8px;font-weight:600;background:#0d0d0d}
.support-btn:hover{color:#0088cc;border-color:#0088cc;background:#050d14;box-shadow:0 0 12px rgba(0,136,204,0.2);transform:translateY(-1px)}
</style></head>
<body>
<div class="main-wrapper"><div class="logo">KageBrowser</div>
<form id="searchForm" action="https://duckduckgo.com/" method="get" style="width:100%"><div class="search-wrapper">
<input id="searchInput" name="q" class="search-box" type="text" placeholder="Поиск в DuckDuckGo или введите URL..." autofocus oninput="checkSearchInput()">
<button type="submit" id="searchSubmitBtn" class="search-submit-btn" title="Искать"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#d4d4d4" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg></button>
</div><div class="engines">
<div class="engine-btn active" onclick="setEngine('ddg',event)">DuckDuckGo</div><div class="engine-btn" onclick="setEngine('google',event)">Google</div><div class="engine-btn" onclick="setEngine('reddit',event)">Reddit</div><div class="engine-btn" onclick="setEngine('github',event)">GitHub</div><div class="engine-btn" onclick="setEngine('yt',event)">YouTube</div>
</div></form>
<div class="shortcuts" id="shortcutsContainer"></div>
</div>
<div id="shortcutModal" class="modal-overlay">
<div class="modal-content">
<div class="modal-title" id="modalTitle">Добавить ярлык</div>
<div class="modal-field"><label>Название</label><input type="text" id="shortcutNameInput" placeholder="Например: Google" autocomplete="off"></div>
<div class="modal-field"><label>Ссылка (URL)</label><input type="text" id="shortcutUrlInput" placeholder="https://..." autocomplete="off"></div>
<div class="modal-field"><label>Иконка (1-3 буквы)</label><input type="text" id="shortcutIconInput" placeholder="Автоматически" maxlength="4" autocomplete="off"></div>
<div class="modal-buttons">
<button type="button" class="modal-btn btn-cancel" onclick="closeModal()">Отмена</button>
<button type="button" class="modal-btn btn-save" onclick="saveShortcut()">Сохранить</button>
</div>
</div>
</div>
<a href="https://donatello.to/KageSec" class="support-btn">ПОДДЕРЖАТЬ НАС</a>
<div class="footer-brand">®KageSec productions</div>
<script>
function checkSearchInput(){const i=document.getElementById('searchInput'),b=document.getElementById('searchSubmitBtn');i.value.trim().length>0?b.classList.add('visible'):b.classList.remove('visible')}
function setEngine(t,e){const f=document.getElementById('searchForm'),i=document.getElementById('searchInput');document.querySelectorAll('.engine-btn').forEach(b=>b.classList.remove('active'));e.target.classList.add('active');i.name='q';if(t==='ddg'){f.action='https://duckduckgo.com/';i.placeholder='Поиск в DuckDuckGo или введите URL...'}else if(t==='google'){f.action='https://google.com/search';i.placeholder='Поиск в Google или введите URL...'}else if(t==='reddit'){f.action='https://www.reddit.com/search/';i.placeholder='Поиск по Reddit...'}else if(t==='github'){f.action='https://github.com/search';i.placeholder='Поиск по GitHub...'}else if(t==='yt'){f.action='https://youtube.com/results';i.name='search_query';i.placeholder='Поиск по YouTube...'}}
const DEFAULT_SHORTCUTS = [
    { name: 'GitHub', url: 'https://github.com', icon: 'GIT' },
    { name: 'YouTube', url: 'https://youtube.com', icon: 'YT' },
    { name: 'Reddit', url: 'https://reddit.com', icon: 'RD' },
    { name: 'ChatGPT', url: 'https://chatgpt.com', icon: 'AI' },
    { name: 'My IP', url: 'https://2ip.ru', icon: 'IP' }
];
function loadShortcuts() {
    try {
        const s = localStorage.getItem('kage_shortcuts');
        if (s) {
            const p = JSON.parse(s);
            if (Array.isArray(p) && p.length > 0) return p;
        }
    } catch(e) {}
    return DEFAULT_SHORTCUTS.slice();
}
let shortcuts = loadShortcuts();
let editIdx = -1;
function getInitials(name) {
    if (!name) return 'URL';
    const parts = name.trim().split(' ').filter(Boolean);
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return name.substring(0, 2).toUpperCase();
}
function renderShortcuts() {
    const c = document.getElementById('shortcutsContainer');
    c.innerHTML = '';
    shortcuts.forEach((s, i) => {
        const item = document.createElement('div');
        item.className = 'shortcut-item';
        item.innerHTML = `<a href="${s.url}" class="shortcut"><div class="icon">${s.icon || getInitials(s.name)}</div><div class="name">${s.name}</div></a><button type="button" class="action-btn edit-btn" title="Изменить" onclick="openEdit(${i}, event)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg></button><button type="button" class="action-btn delete-btn" title="Удалить" onclick="delShortcut(${i}, event)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>`;
        c.appendChild(item);
    });
    const add = document.createElement('div');
    add.className = 'shortcut-item add-item';
    add.innerHTML = `<div class="shortcut" onclick="openAdd()"><div class="icon add-icon"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg></div><div class="name">Добавить</div></div>`;
    c.appendChild(add);
}
function openAdd() {
    editIdx = -1;
    document.getElementById('modalTitle').textContent = 'Добавить ярлык';
    document.getElementById('shortcutNameInput').value = '';
    document.getElementById('shortcutUrlInput').value = '';
    document.getElementById('shortcutIconInput').value = '';
    document.getElementById('shortcutModal').classList.add('active');
    setTimeout(() => document.getElementById('shortcutNameInput').focus(), 50);
}
function openEdit(i, e) {
    if (e) { e.preventDefault(); e.stopPropagation(); }
    editIdx = i;
    const s = shortcuts[i];
    document.getElementById('modalTitle').textContent = 'Редактировать ярлык';
    document.getElementById('shortcutNameInput').value = s.name || '';
    document.getElementById('shortcutUrlInput').value = s.url || '';
    document.getElementById('shortcutIconInput').value = s.icon || '';
    document.getElementById('shortcutModal').classList.add('active');
    setTimeout(() => document.getElementById('shortcutNameInput').focus(), 50);
}
function closeModal() {
    document.getElementById('shortcutModal').classList.remove('active');
}
function delShortcut(i, e) {
    if (e) { e.preventDefault(); e.stopPropagation(); }
    shortcuts.splice(i, 1);
    localStorage.setItem('kage_shortcuts', JSON.stringify(shortcuts));
    renderShortcuts();
}
function saveShortcut() {
    let name = document.getElementById('shortcutNameInput').value.trim();
    let url = document.getElementById('shortcutUrlInput').value.trim();
    let icon = document.getElementById('shortcutIconInput').value.trim().toUpperCase();
    if (!name && !url) { closeModal(); return; }
    if (!name) name = url.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0];
    if (!url) url = 'https://' + name;
    if (!url.startsWith('http://') && !url.startsWith('https://')) url = 'https://' + url;
    if (!icon) icon = getInitials(name);
    if (editIdx === -1) {
        shortcuts.push({ name: name, url: url, icon: icon });
    } else {
        shortcuts[editIdx] = { name: name, url: url, icon: icon };
    }
    localStorage.setItem('kage_shortcuts', JSON.stringify(shortcuts));
    closeModal();
    renderShortcuts();
}
document.getElementById('shortcutModal').addEventListener('click', function(e) {
    if (e.target === this) closeModal();
});
window.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeModal();
});
['shortcutNameInput', 'shortcutUrlInput', 'shortcutIconInput'].forEach(id => {
    document.getElementById(id).addEventListener('keydown', function(e) {
        if (e.key === 'Enter') saveShortcut();
    });
});
renderShortcuts();
</script></body></html>"""

HOME_HTML_DIR = os.path.join(os.path.expanduser('~'), '.kagebrowser')
os.makedirs(HOME_HTML_DIR, exist_ok=True)
HOME_HTML_PATH = os.path.join(HOME_HTML_DIR, 'start.html')
with open(HOME_HTML_PATH, 'w', encoding='utf-8') as _f:
    _f.write(KAGESEC_HOME)
HOME_URL = QUrl.fromLocalFile(HOME_HTML_PATH)

KAGE_WINDOWS = []
SHARED_PROFILE = None


def get_shared_profile():
    global SHARED_PROFILE
    if SHARED_PROFILE is None:
        SHARED_PROFILE = QWebEngineProfile.defaultProfile()
        SHARED_PROFILE.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
        SHARED_PROFILE.setUrlRequestInterceptor(AdBlockInterceptor())
        SHARED_PROFILE.setHttpUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
    return SHARED_PROFILE


class KageStyle:
    @staticmethod
    def get_style():
        return """
            QMainWindow { background-color: #000000; }
            QTabBar { background: #080808; qproperty-drawBase: 0; }
            QTabBar::tab {
                background: #0e0e0e; color: #777777; padding: 0px 10px 0px 12px;
                border: 1px solid #1c1c1c; border-top: none; border-top-left-radius: 0px;
                border-top-right-radius: 0px; border-bottom-left-radius: 9px;
                border-bottom-right-radius: 9px; margin: 0px 2px 0px 0px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 13px; min-height: 36px; max-height: 36px; min-width: 0px;
            }
            QTabBar::tab:first { border-left: none; border-bottom-left-radius: 0px; margin-left: 0px; }
            QTabBar::tab:last { border-right: none; border-bottom-right-radius: 0px; margin-right: 0px; }
            QTabBar::tab:only-one { border-left: none; border-right: none; border-radius: 0px; margin: 0px; }
            QTabBar::tab:hover { background: #181818; color: #cccccc; border-color: #282828; }
            QTabBar::tab:selected { background: #141414; color: #ffffff; border: 1px solid #2e2e2e; border-top: none; }
            QPushButton#TabCloseBtn {
                background-color: transparent; border: none; border-radius: 12px;
                width: 24px; height: 24px; min-width: 24px; max-width: 24px;
                min-height: 24px; max-height: 24px; margin: 0px 6px 0px 4px; padding: 0px;
            }
            QPushButton#TabCloseBtn:hover { background-color: #2c2c2c; }
            QPushButton#TabCloseBtn:pressed { background-color: #c42b1c; }
            QTabBar QToolButton { background-color: #121212; border: 1px solid #262626; border-radius: 4px; margin: 2px; }
            QTabBar QToolButton:hover { background-color: #1e1e1e; border-color: #3e3e3e; }
            QToolBar { background-color: #0d0d0d; border-bottom: 1px solid #1c1c1c; padding: 4px 8px; spacing: 6px; }
            QPushButton#NavBtn {
                background-color: transparent; border: none; border-radius: 17px;
                width: 34px; height: 34px; min-width: 34px; max-width: 34px;
                min-height: 34px; max-height: 34px; padding: 0px; margin: 0px;
            }
            QPushButton#NavBtn:hover { background-color: #222222; }
            QPushButton#NavBtn:pressed { background-color: #303030; }
            QPushButton#NavBtn:disabled { background-color: transparent; border: none; }
            QLineEdit#AddressBar {
                background-color: #141414; border: 1px solid #282828; border-radius: 17px;
                padding: 0px 42px 0px 18px; color: #e0e0e0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 13px; min-height: 34px; max-height: 34px; selection-background-color: #333333;
            }
            QLineEdit#AddressBar:hover { background-color: #181818; border-color: #3c3c3c; }
            QLineEdit#AddressBar:focus { background-color: #1c1c1c; border: 1px solid #555555; color: #ffffff; }
            QPushButton#AddressBarSearchBtn {
                background-color: #222222; border: 1px solid #363636; border-radius: 13px;
                padding: 0px; margin: 0px;
            }
            QPushButton#AddressBarSearchBtn:hover {
                background-color: #303030; border-color: #505050;
            }
            QPushButton#AddressBarSearchBtn:pressed {
                background-color: #404040; border-color: #666666;
            }
            QProgressBar#LoadingBar { border: none; background: transparent; height: 2px; max-height: 2px; text-align: center; }
            QProgressBar#LoadingBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0088cc, stop:1 #2ecc71); border-radius: 1px; }
            QFrame#DownloadsPopup { background-color: #0e0e0e; border: 1px solid #242424; border-radius: 12px; }
            QWidget#DownloadsHeader { border-bottom: 1px solid #1a1a1a; }
            QFrame#DownloadItem { background-color: #131313; border: 1px solid #202020; border-radius: 8px; }
            QFrame#DownloadItem:hover { background-color: #171717; border-color: #2c2c2c; }
            QPushButton#DownloadActionBtn {
                background-color: #1a1a1a; color: #d0d0d0; border: 1px solid #2d2d2d; border-radius: 6px;
                padding: 4px 10px; font-size: 11px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }
            QPushButton#DownloadActionBtn:hover { background-color: #262626; border-color: #444444; color: #ffffff; }
            QScrollBar:vertical { background: transparent; width: 6px; margin: 0px; }
            QScrollBar::handle:vertical { background: #282828; min-height: 20px; border-radius: 3px; }
            QScrollBar::handle:vertical:hover { background: #444444; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
            QMenu {
                background-color: #111111; border: 1px solid #252525; border-radius: 9px; padding: 5px 3px;
            }
            QMenu::item {
                background-color: transparent; color: #dedede; padding: 6px 20px 6px 26px; border-radius: 5px;
                font-size: 12px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 1px 2px;
            }
            QMenu::item:selected { background-color: #222222; color: #ffffff; }
            QMenu::item:disabled { color: #4e4e4e; background-color: transparent; }
            QMenu::separator { height: 1px; background-color: #1c1c1c; margin: 4px 6px; }
            QMenu::icon { padding-left: 4px; }
            QFrame#ZoomToast {
                background-color: rgba(18, 18, 18, 225);
                border: 1px solid #333333;
                border-radius: 12px;
            }
        """


class DownloadItemWidget(QFrame):
    def __init__(self, download, file_path, parent=None):
        super().__init__(parent)
        self.download = download
        self.file_path = file_path
        self.setObjectName('DownloadItem')

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(8)

        self.icon_label = QLabel()
        self.icon_label.setPixmap(get_svg_icon('download', color='#0088cc').pixmap(16, 16))
        self.icon_label.setFixedSize(16, 16)
        top_layout.addWidget(self.icon_label)

        file_name = os.path.basename(file_path)
        fm = QFontMetrics(QFont('-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto', 12))
        self.name_label = QLabel(fm.elidedText(file_name, Qt.TextElideMode.ElideMiddle, 280))
        self.name_label.setStyleSheet('color: #ffffff; font-weight: 600; font-size: 12px;')
        self.name_label.setToolTip(file_name)
        top_layout.addWidget(self.name_label, 1)
        layout.addLayout(top_layout)

        self.status_label = QLabel('Подготовка к загрузке...')
        self.status_label.setStyleSheet('color: #888888; font-size: 11px;')
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("QProgressBar{background-color:#222;border:none;border-radius:1px}QProgressBar::chunk{background-color:#0088cc;border-radius:1px}")
        layout.addWidget(self.progress_bar)

        self.btn_layout = QHBoxLayout()
        self.btn_layout.setContentsMargins(0, 2, 0, 0)
        self.btn_layout.setSpacing(8)

        self.btn_open = QPushButton('Открыть')
        self.btn_open.setObjectName('DownloadActionBtn')
        self.btn_open.setIcon(get_svg_icon('file_open', color='#cccccc'))
        self.btn_open.setIconSize(QSize(12, 12))
        self.btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open.clicked.connect(self._open_file)
        self.btn_open.hide()
        self.btn_layout.addWidget(self.btn_open)

        self.btn_show_folder = QPushButton('В папке')
        self.btn_show_folder.setObjectName('DownloadActionBtn')
        self.btn_show_folder.setIcon(get_svg_icon('folder', color='#cccccc'))
        self.btn_show_folder.setIconSize(QSize(12, 12))
        self.btn_show_folder.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_show_folder.clicked.connect(self._show_in_folder)
        self.btn_show_folder.hide()
        self.btn_layout.addWidget(self.btn_show_folder)
        self.btn_layout.addStretch()
        layout.addLayout(self.btn_layout)

        if download:
            try:
                download.receivedBytesChanged.connect(self._update_progress)
                download.totalBytesChanged.connect(self._update_progress)
                download.stateChanged.connect(self._on_state_changed)
                download.isFinishedChanged.connect(self._update_finished)
                self._update_progress()
            except Exception:
                pass

    def _update_progress(self):
        try:
            if not self.download:
                return
            rec, tot = self.download.receivedBytes(), self.download.totalBytes()
            if tot > 0:
                pct = int((rec / tot) * 100)
                self.progress_bar.setValue(pct)
                self.status_label.setText(f'{format_size(rec)} / {format_size(tot)} • {pct}%')
            else:
                self.status_label.setText(f'{format_size(rec)} загружено')
        except Exception:
            pass

    def _on_state_changed(self, state):
        try:
            if state == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
                self._set_completed()
            elif state == QWebEngineDownloadRequest.DownloadState.DownloadCancelled:
                self.status_label.setText('Загрузка отменена')
                self.progress_bar.hide()
                self.icon_label.setPixmap(get_svg_icon('download', color='#888888').pixmap(16, 16))
            elif state == QWebEngineDownloadRequest.DownloadState.DownloadInterrupted:
                self.status_label.setText('Ошибка загрузки')
                self.progress_bar.hide()
                self.icon_label.setPixmap(get_svg_icon('download', color='#e74c3c').pixmap(16, 16))
        except Exception:
            pass

    def _update_finished(self):
        try:
            if self.download and self.download.isFinished() and self.download.state() == QWebEngineDownloadRequest.DownloadState.DownloadCompleted:
                self._set_completed()
        except Exception:
            pass

    def _set_completed(self):
        try:
            self.progress_bar.hide()
            tot = 0
            if self.download:
                try:
                    tot = self.download.totalBytes()
                except Exception:
                    pass
            if tot <= 0 and os.path.exists(self.file_path):
                tot = os.path.getsize(self.file_path)
            self.status_label.setText(f'Завершено • {format_size(tot)}')
            self.icon_label.setPixmap(get_svg_icon('download', color='#2ecc71').pixmap(16, 16))
            self.btn_open.show()
            self.btn_show_folder.show()
        except Exception:
            pass

    def _open_file(self):
        if os.path.exists(self.file_path):
            try:
                os.startfile(self.file_path)
            except Exception:
                pass

    def _show_in_folder(self):
        if os.path.exists(self.file_path):
            try:
                subprocess.Popen(['explorer', f'/select,{os.path.normpath(self.file_path)}'])
            except Exception:
                try:
                    os.startfile(os.path.dirname(os.path.normpath(self.file_path)))
                except Exception:
                    pass


class KageDownloadsPopup(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setObjectName('DownloadsPopup')
        self.setFixedWidth(380)
        self.setFixedHeight(520)
        self._last_close_time = 0
        self.main_window = parent

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.fade_anim = QPropertyAnimation(self.opacity_effect, b'opacity')
        self.fade_anim.setDuration(160)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.pos_anim = QPropertyAnimation(self, b'pos')
        self.pos_anim.setDuration(160)
        self.pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        cfg = load_config()
        self.download_dir = cfg.get('download_dir', os.path.join(os.path.expanduser('~'), 'Downloads'))
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir, exist_ok=True)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        header = QWidget()
        header.setObjectName('DownloadsHeader')
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 8)
        h_layout.setSpacing(6)

        title = QLabel('Загрузки')
        title.setStyleSheet('color: #ffffff; font-weight: 700; font-size: 15px;')
        h_layout.addWidget(title)
        h_layout.addStretch()

        lbl_path_caption = QLabel('Папка:')
        lbl_path_caption.setStyleSheet('color: #777777; font-size: 11px;')
        h_layout.addWidget(lbl_path_caption)

        self.btn_change_path = QPushButton()
        self.btn_change_path.setObjectName('DownloadActionBtn')
        self.btn_change_path.setIcon(get_svg_icon('edit', color='#aaaaaa'))
        self.btn_change_path.setIconSize(QSize(12, 12))
        self.btn_change_path.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_change_path.clicked.connect(self._change_download_dir)
        h_layout.addWidget(self.btn_change_path)

        btn_folder = QPushButton()
        btn_folder.setObjectName('NavBtn')
        btn_folder.setIcon(get_svg_icon('folder', color='#888888'))
        btn_folder.setIconSize(QSize(16, 16))
        btn_folder.setFixedSize(28, 28)
        btn_folder.setToolTip('Открыть текущую папку загрузок')
        btn_folder.clicked.connect(self._open_downloads_folder)
        h_layout.addWidget(btn_folder)
        main_layout.addWidget(header)

        self._update_path_ui()

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setStyleSheet('border: none; background: transparent;')

        self.container = QWidget()
        self.items_layout = QVBoxLayout(self.container)
        self.items_layout.setContentsMargins(0, 0, 4, 0)
        self.items_layout.setSpacing(8)

        self.empty_widget = QWidget()
        empty_layout = QVBoxLayout(self.empty_widget)
        empty_layout.setContentsMargins(0, 90, 0, 90)
        empty_layout.setSpacing(10)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        empty_icon = QLabel()
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_icon.setPixmap(get_svg_icon('download', color='#333333', render_size=64).pixmap(40, 40))
        empty_layout.addWidget(empty_icon)

        empty_label = QLabel('Нет недавних загрузок')
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_label.setStyleSheet('color: #777777; font-size: 13px; font-weight: 500;')
        empty_layout.addWidget(empty_label)

        empty_sub = QLabel('Файлы сохраняются в выбранную папку')
        empty_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_sub.setStyleSheet('color: #444444; font-size: 11px;')
        empty_layout.addWidget(empty_sub)

        self.items_layout.addWidget(self.empty_widget)
        self.items_layout.addStretch()
        self.scroll.setWidget(self.container)
        main_layout.addWidget(self.scroll)

    def hideEvent(self, event):
        self._last_close_time = datetime.datetime.now().timestamp()
        super().hideEvent(event)

    def _update_path_ui(self):
        folder_name = os.path.basename(self.download_dir) or self.download_dir
        if len(folder_name) > 16:
            folder_name = folder_name[:14] + '...'
        self.btn_change_path.setText(f' {folder_name}')
        self.btn_change_path.setToolTip(f'Папка загрузки: {self.download_dir}\nНажмите, чтобы изменить')

    def _change_download_dir(self):
        self.hide()
        parent_win = self.main_window or self.parent() or self
        new_dir = QFileDialog.getExistingDirectory(parent_win, 'Выберите папку для загрузок', self.download_dir)
        if new_dir:
            self.download_dir = os.path.normpath(new_dir)
            save_config({'download_dir': self.download_dir})
            self._update_path_ui()
        if parent_win and hasattr(parent_win, 'btn_downloads'):
            self.show_below(parent_win.btn_downloads)

    def _open_downloads_folder(self):
        if os.path.exists(self.download_dir):
            try:
                os.startfile(self.download_dir)
            except Exception:
                pass

    def add_download(self, download, file_path):
        if self.empty_widget.isVisible():
            self.empty_widget.hide()
        item = DownloadItemWidget(download, file_path, self)
        self.items_layout.insertWidget(0, item)
        eff = QGraphicsOpacityEffect(item)
        item.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b'opacity')
        anim.setDuration(180)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        item._fade_anim = anim

    def show_below(self, target_btn):
        btn_pos = target_btn.mapToGlobal(QPoint(0, 0))
        px = btn_pos.x() + target_btn.width() - self.width()
        py = btn_pos.y() + target_btn.height() + 6
        screen = target_btn.screen() or QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            if px + self.width() > geo.right() - 8:
                px = geo.right() - self.width() - 8
            if px < geo.left() + 8:
                px = geo.left() + 8
            if py + self.height() > geo.bottom() - 8:
                py = btn_pos.y() - self.height() - 6

        self.move(px, py - 6)
        self.show()
        self.raise_()

        self.fade_anim.stop()
        self.fade_anim.setStartValue(0.0)
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()

        self.pos_anim.stop()
        self.pos_anim.setStartValue(QPoint(px, py - 6))
        self.pos_anim.setEndValue(QPoint(px, py))
        self.pos_anim.start()

    def hide_animated(self):
        self.fade_anim.stop()
        self.fade_anim.setStartValue(self.opacity_effect.opacity())
        self.fade_anim.setEndValue(0.0)
        try:
            self.fade_anim.finished.disconnect()
        except Exception:
            pass
        self.fade_anim.finished.connect(self.hide)
        self.fade_anim.start()


class KageZoomToast(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('ZoomToast')
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(98, 50)
        self.text = '100%'

        self.eff = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.eff)
        self.eff.setOpacity(0.0)

        self.pos_anim = QPropertyAnimation(self, b'pos')
        self.pos_anim.setDuration(200)
        self.pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.fade_anim = QPropertyAnimation(self.eff, b'opacity')
        self.fade_anim.setDuration(200)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide_animated)
        self.hide()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        w = float(self.width())
        h = float(self.height())
        taper = 8.5

        path = QPainterPath()
        path.moveTo(w, 0.5)
        path.lineTo(0.5, taper)
        path.lineTo(0.5, h - taper)
        path.lineTo(w, h - 0.5)
        path.closeSubpath()

        p.fillPath(path, QColor(10, 10, 10, 180))
        pen = QPen(QColor(90, 90, 90, 190), 1.0)
        p.strokePath(path, pen)

        max_w = w - 24
        max_h = h - (taper * 2) + 2
        f_size = 17
        while f_size > 8:
            font = QFont('-apple-system, BlinkMacSystemFont, Segoe UI, Roboto', f_size, QFont.Weight.Black)
            fm = QFontMetrics(font)
            if fm.horizontalAdvance(self.text) <= max_w and fm.height() <= max_h:
                break
            f_size -= 1
        font = QFont('-apple-system, BlinkMacSystemFont, Segoe UI, Roboto', f_size, QFont.Weight.Black)

        p.setPen(QColor(255, 255, 255))
        p.setFont(font)
        text_rect = QRectF(2, 0, w - 14, h)
        p.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, self.text)
        p.end()

    def show_zoom(self, factor, target_y):
        pct = int(round(factor * 100))
        self.text = f'{pct}%'
        self.update()

        parent_w = self.parent().width() if self.parent() else 600
        target_x = parent_w - 84
        start_x = parent_w

        if not self.isVisible():
            self.move(start_x, target_y)
            self.eff.setOpacity(0.0)
            self.show()
            self.raise_()

        self.pos_anim.stop()
        self.pos_anim.setStartValue(self.pos())
        self.pos_anim.setEndValue(QPoint(target_x, target_y))
        self.pos_anim.start()

        self.fade_anim.stop()
        self.fade_anim.setStartValue(self.eff.opacity())
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()

        self.timer.start(1400)

    def hide_animated(self):
        parent_w = self.parent().width() if self.parent() else 600
        self.pos_anim.stop()
        self.pos_anim.setStartValue(self.pos())
        self.pos_anim.setEndValue(QPoint(parent_w, self.pos().y()))
        self.pos_anim.start()

        self.fade_anim.stop()
        self.fade_anim.setStartValue(self.eff.opacity())
        self.fade_anim.setEndValue(0.0)

        def on_done():
            if self.eff.opacity() == 0.0:
                self.hide()
        try:
            self.fade_anim.finished.disconnect()
        except Exception:
            pass
        self.fade_anim.finished.connect(on_done)
        self.fade_anim.start()


class ChromeTabBar(QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDrawBase(False)
        self.setExpanding(False)
        self.setUsesScrollButtons(True)
        self.setElideMode(Qt.TextElideMode.ElideRight)
        self._anim_tab = -1
        self._anim_mode = None
        self._anim_progress = 1.0
        self._start_w = 0
        self._anim = None
        self._on_close_done = None

    def tabSizeHint(self, index):
        avail = max(100, self.width())
        cnt = max(1, self.count())
        if self._anim_tab >= 0 and self._anim_tab < cnt and cnt > 1:
            if self._anim_mode == 'add':
                target_w = max(100, avail // cnt)
                w_anim = max(0, int(target_w * self._anim_progress))
            else:
                w_anim = max(0, int(self._start_w * (1.0 - self._anim_progress)))
            rem_w = max(100 * (cnt - 1), avail - w_anim)
            base_other = rem_w // (cnt - 1)
            rem = rem_w % (cnt - 1)
            other_idx = index if index < self._anim_tab else index - 1
            w_other = base_other + (1 if other_idx < rem else 0)
            return QSize(w_anim if index == self._anim_tab else w_other, 36)
        base = avail // cnt
        rem = avail % cnt
        w = base + (1 if index < rem else 0)
        return QSize(max(100, w), 36)

    def minimumTabSizeHint(self, index):
        return self.tabSizeHint(index)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.count() > 0 and self._anim_tab == -1:
            self.setTabText(0, self.tabText(0))

    def animate_add_tab(self, idx):
        if self.count() <= 1:
            return
        if self._anim and self._anim.state() == QVariantAnimation.State.Running:
            self._anim.stop()
            if self._on_close_done:
                cb = self._on_close_done
                self._on_close_done = None
                cb()
        self._anim_tab = idx
        self._anim_mode = 'add'
        self._anim_progress = 0.0
        btn = self.tabButton(idx, QTabBar.ButtonPosition.RightSide)
        if btn:
            btn.hide()
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(160)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        def on_step(v):
            self._anim_progress = v
            if self.count() > 0:
                self.setTabText(0, self.tabText(0))
        def on_done():
            self._anim_tab = -1
            self._anim_mode = None
            self._anim_progress = 1.0
            if btn:
                btn.show()
            if self.count() > 0:
                self.setTabText(0, self.tabText(0))
        self._anim.valueChanged.connect(on_step)
        self._anim.finished.connect(on_done)
        self._anim.start()

    def animate_close_tab(self, idx, callback):
        if self.count() <= 1:
            callback(idx)
            return
        if self._anim and self._anim.state() == QVariantAnimation.State.Running:
            self._anim.stop()
            if self._on_close_done:
                cb = self._on_close_done
                self._on_close_done = None
                cb()
        if idx < 0 or idx >= self.count():
            return
        self._anim_tab = idx
        self._anim_mode = 'close'
        self._start_w = self.tabRect(idx).width()
        self._anim_progress = 0.0
        btn = self.tabButton(idx, QTabBar.ButtonPosition.RightSide)
        if btn:
            btn.hide()
        def do_finish():
            self._anim_tab = -1
            self._anim_mode = None
            self._anim_progress = 1.0
            self._on_close_done = None
            callback(idx)
            if self.count() > 0:
                self.setTabText(0, self.tabText(0))
        self._on_close_done = do_finish
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(140)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        def on_step(v):
            self._anim_progress = v
            ref_idx = 0 if idx != 0 else 1
            if ref_idx < self.count():
                self.setTabText(ref_idx, self.tabText(ref_idx))
        self._anim.valueChanged.connect(on_step)
        self._anim.finished.connect(do_finish)
        self._anim.start()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            idx = self.tabAt(event.position().toPoint())
            if idx != -1:
                self.tabCloseRequested.emit(idx)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.AltModifier:
            event.ignore()
            return
        delta = event.angleDelta().y() or event.angleDelta().x()
        if delta == 0:
            event.accept()
            return
        btns = [b for b in self.findChildren(QToolButton) if b.objectName() != 'TabCloseBtn']
        if len(btns) >= 2:
            left_btn = min(btns, key=lambda b: b.pos().x())
            right_btn = max(btns, key=lambda b: b.pos().x())
            if delta > 0 and left_btn.isEnabled():
                left_btn.click()
            elif delta < 0 and right_btn.isEnabled():
                right_btn.click()
        event.accept()

    def contextMenuEvent(self, event):
        idx = self.tabAt(event.pos())
        if idx != -1:
            menu = QMenu(self)
            a_new = menu.addAction(get_svg_icon('plus', color='#d8d8d8', render_size=48), 'Новая вкладка')
            a_reload = menu.addAction(get_svg_icon('reload', color='#d8d8d8', render_size=48), 'Перезагрузить')
            a_dup = menu.addAction(get_svg_icon('copy', color='#d8d8d8', render_size=48), 'Дублировать вкладку')
            menu.addSeparator()
            a_close = menu.addAction(get_svg_icon('close', color='#d8d8d8', render_size=48), 'Закрыть вкладку')
            a_close_others = menu.addAction('Закрыть другие вкладки')
            a_close_right = menu.addAction('Закрыть вкладки справа')

            main_win = self.window()
            a_new.triggered.connect(lambda: main_win.add_new_tab(HOME_URL, 'Новая вкладка'))
            a_reload.triggered.connect(main_win._reload_or_stop_page)
            a_dup.triggered.connect(lambda: self._duplicate_tab(idx))
            a_close.triggered.connect(lambda: self.tabCloseRequested.emit(idx))
            a_close_others.triggered.connect(lambda: self._close_other_tabs(idx))
            a_close_right.triggered.connect(lambda: self._close_tabs_to_right(idx))
            menu.exec(event.globalPos())
            event.accept()
        else:
            super().contextMenuEvent(event)

    def _duplicate_tab(self, idx):
        main_win = self.window()
        w = main_win.tabs.widget(idx)
        if w:
            main_win.add_new_tab(w.url(), main_win.tabs.tabBar().tabText(idx).strip())

    def _close_other_tabs(self, keep_idx):
        main_win = self.window()
        for i in range(self.count() - 1, -1, -1):
            if i != keep_idx:
                main_win.close_tab(i)

    def _close_tabs_to_right(self, from_idx):
        main_win = self.window()
        for i in range(self.count() - 1, from_idx, -1):
            main_win.close_tab(i)


class KageTabWidget(QWidget):
    currentChanged = pyqtSignal(int)
    tabCloseRequested = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tab_container = QWidget()
        self.tab_container.setMinimumHeight(0)
        self.tab_container.setMaximumHeight(36)
        tc_layout = QVBoxLayout(self.tab_container)
        tc_layout.setContentsMargins(0, 0, 0, 0)
        tc_layout.setSpacing(0)
        tc_layout.setAlignment(Qt.AlignmentFlag.AlignBottom)

        self.tab_bar = ChromeTabBar(self)
        self.tab_bar.setDocumentMode(True)
        self.tab_bar.setTabsClosable(True)
        self.tab_bar.setIconSize(QSize(16, 16))
        self.tab_bar.tabCloseRequested.connect(self.tabCloseRequested.emit)
        self.tab_bar.currentChanged.connect(self._on_tab_bar_current_changed)
        tc_layout.addWidget(self.tab_bar)

        layout.addWidget(self.tab_container)

        self.tab_anim = QPropertyAnimation(self.tab_container, b'maximumHeight')
        self.tab_anim.setDuration(110)
        self.tab_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.tab_anim.finished.connect(self._on_tab_anim_finished)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)

    def _on_tab_bar_current_changed(self, idx):
        if idx != -1 and idx < self.stack.count():
            self.stack.setCurrentIndex(idx)
        self.currentChanged.emit(idx)

    def toggle_tabs_visibility(self):
        if self.tab_container.isVisible() and self.tab_container.maximumHeight() > 0:
            self.tab_anim.stop()
            self.tab_anim.setEasingCurve(QEasingCurve.Type.InQuad)
            self.tab_anim.setStartValue(self.tab_container.height())
            self.tab_anim.setEndValue(0)
            self.tab_anim.start()
            return False
        else:
            self.tab_container.show()
            self.tab_anim.stop()
            self.tab_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.tab_anim.setStartValue(self.tab_container.height())
            self.tab_anim.setEndValue(36)
            self.tab_anim.start()
            return True

    def _on_tab_anim_finished(self):
        if self.tab_container.maximumHeight() == 0:
            self.tab_container.hide()

    def ensure_tabs_visible(self):
        if not self.tab_container.isVisible() or self.tab_container.maximumHeight() == 0:
            self.tab_container.show()
            self.tab_anim.stop()
            self.tab_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.tab_anim.setStartValue(self.tab_container.height())
            self.tab_anim.setEndValue(36)
            self.tab_anim.start()

    def addTab(self, widget, icon, label, close_btn=None):
        idx = self.tab_bar.addTab(icon, label)
        self.stack.addWidget(widget)
        if close_btn:
            self.tab_bar.setTabButton(idx, QTabBar.ButtonPosition.RightSide, close_btn)
        if self.tab_bar.count() > 1:
            self.tab_bar.animate_add_tab(idx)
        return idx

    def removeTab(self, idx):
        self.tab_bar.removeTab(idx)
        w = self.stack.widget(idx)
        if w:
            self.stack.removeWidget(w)

    def count(self):
        return self.tab_bar.count()

    def currentIndex(self):
        return self.tab_bar.currentIndex()

    def setCurrentIndex(self, idx):
        self.tab_bar.setCurrentIndex(idx)
        self.stack.setCurrentIndex(idx)

    def currentWidget(self):
        return self.stack.currentWidget()

    def widget(self, idx):
        return self.stack.widget(idx)

    def indexOf(self, widget):
        return self.stack.indexOf(widget)

    def setTabText(self, idx, text):
        self.tab_bar.setTabText(idx, text)

    def setTabIcon(self, idx, icon):
        self.tab_bar.setTabIcon(idx, icon)

    def tabBar(self):
        return self.tab_bar


class KageWebPage(QWebEnginePage):
    def createWindow(self, window_type):
        try:
            parent_view = self.parent()
            main_win = parent_view.window() if parent_view else None
            if window_type == QWebEnginePage.WebWindowType.WebBrowserWindow:
                new_win = KageBrowser(empty_tab=True)
                new_win.show()
                return new_win.tabs.currentWidget().page()
            elif main_win and hasattr(main_win, 'add_new_tab'):
                browser = main_win.add_new_tab(qurl=None)
                return browser.page()
            return super().createWindow(window_type)
        except Exception:
            return None


class KageWebView(QWebEngineView):
    def __init__(self, profile, parent=None):
        super().__init__(parent)
        self.setPage(KageWebPage(profile, self))
        self.page().fullScreenRequested.connect(self.handle_fullscreen)
        s = self.settings()
        for attr in (
            QWebEngineSettings.WebAttribute.FullScreenSupportEnabled,
            QWebEngineSettings.WebAttribute.PluginsEnabled,
            QWebEngineSettings.WebAttribute.Accelerated2dCanvasEnabled,
            QWebEngineSettings.WebAttribute.WebGLEnabled,
            QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled,
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls,
            QWebEngineSettings.WebAttribute.LocalStorageEnabled,
            QWebEngineSettings.WebAttribute.AllowRunningInsecureContent
        ):
            s.setAttribute(attr, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture, False)

    def event(self, e):
        if self.focusProxy() and not getattr(self, '_fp_installed', False):
            self.focusProxy().installEventFilter(self)
            self._fp_installed = True
        return super().event(e)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Escape:
            main_win = self.window()
            if getattr(main_win, '_is_html5_fullscreen', False):
                self.triggerPageAction(QWebEnginePage.WebAction.ExitFullScreen)
                self.page().runJavaScript('if(document.fullscreenElement) document.exitFullscreen();')
                return True
        if event.type() == QEvent.Type.Wheel:
            mods = event.modifiers() | QApplication.keyboardModifiers()
            if mods & Qt.KeyboardModifier.AltModifier:
                main_win = self.window()
                delta = event.angleDelta().y() or event.angleDelta().x()
                if delta > 0:
                    main_win._prev_tab()
                elif delta < 0:
                    main_win._next_tab()
                return True
            elif mods & Qt.KeyboardModifier.ControlModifier:
                main_win = self.window()
                delta = event.angleDelta().y() or event.angleDelta().x()
                if delta > 0:
                    main_win._zoom_in()
                elif delta < 0:
                    main_win._zoom_out()
                return True
        return super().eventFilter(obj, event)

    def wheelEvent(self, event):
        mods = event.modifiers() | QApplication.keyboardModifiers()
        if mods & Qt.KeyboardModifier.AltModifier:
            main_win = self.window()
            delta = event.angleDelta().y() or event.angleDelta().x()
            if delta > 0:
                main_win._prev_tab()
            elif delta < 0:
                main_win._next_tab()
            event.accept()
            return
        elif mods & Qt.KeyboardModifier.ControlModifier:
            main_win = self.window()
            delta = event.angleDelta().y() or event.angleDelta().x()
            if delta > 0:
                main_win._zoom_in()
            elif delta < 0:
                main_win._zoom_out()
            event.accept()
            return
        super().wheelEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() in (Qt.MouseButton.BackButton, Qt.MouseButton.XButton1):
            self.triggerPageAction(QWebEnginePage.WebAction.Back)
            event.accept()
            return
        elif event.button() in (Qt.MouseButton.ForwardButton, Qt.MouseButton.XButton2):
            self.triggerPageAction(QWebEnginePage.WebAction.Forward)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def contextMenuEvent(self, event):
        try:
            menu = self.createStandardContextMenu()
            if menu:
                for a in menu.actions():
                    self._translate_action(a)
                menu.exec(event.globalPos())
                event.accept()
            else:
                super().contextMenuEvent(event)
        except Exception:
            super().contextMenuEvent(event)

    def _translate_action(self, action):
        try:
            if action.isSeparator():
                return
            text = action.text()
            clean = text.replace('&', '').strip()
            if clean in RU_TRANSLATIONS:
                action.setText(RU_TRANSLATIONS[clean])
            elif clean.startswith('Search ') and ' for ' in clean:
                query = clean.split(' for ', 1)[-1]
                action.setText(f'Искать {query} в интернете')
            else:
                for en, ru in RU_TRANSLATIONS.items():
                    if en.lower() == clean.lower():
                        action.setText(ru)
                        break

            clean_ru = action.text()
            if clean_ru == 'Назад':
                action.setIcon(get_svg_icon('back', color='#d8d8d8', disabled_color='#444444', render_size=48))
            elif clean_ru == 'Вперёд':
                action.setIcon(get_svg_icon('forward', color='#d8d8d8', disabled_color='#444444', render_size=48))
            elif clean_ru == 'Перезагрузить':
                action.setIcon(get_svg_icon('reload', color='#d8d8d8', render_size=48))
            elif 'новой вкладке' in clean_ru:
                action.setIcon(get_svg_icon('plus', color='#d8d8d8', render_size=48))
            elif 'Копировать' in clean_ru:
                action.setIcon(get_svg_icon('copy', color='#d8d8d8', render_size=48))
            elif 'Сохранить' in clean_ru:
                action.setIcon(get_svg_icon('download', color='#d8d8d8', render_size=48))

            if action.menu():
                for sub_a in action.menu().actions():
                    self._translate_action(sub_a)
        except Exception:
            pass

    def handle_fullscreen(self, request):
        main_win = self.window()
        if request.toggleOn():
            main_win._is_html5_fullscreen = True
            main_win._pre_video_fullscreen = main_win.isFullScreen()
            main_win._pre_video_maximized = main_win.isMaximized()
            main_win._pre_video_tabs_visible = main_win.tabs.tab_container.isVisible()
            main_win.showFullScreen()
            main_win.toolbar.hide()
            main_win.progress_bar.hide()
            main_win.tabs.tab_container.hide()
        else:
            main_win._is_html5_fullscreen = False
            if getattr(main_win, '_pre_video_fullscreen', False):
                main_win.showFullScreen()
            elif getattr(main_win, '_pre_video_maximized', False):
                main_win.showMaximized()
            else:
                main_win.showNormal()
            main_win.toolbar.show()
            main_win.progress_bar.show()
            if getattr(main_win, '_pre_video_tabs_visible', True):
                main_win.tabs.tab_container.show()
        request.accept()


class AdBlockInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self):
        super().__init__()
        self.whitelist = {'dark.video', 'donatello.to', 'youtube.com', 'github.com', 'google.com'}
        self.ad_hosts = {
            'pixel.facebook.com', 'google-analytics.com', 'static.doubleclick.net',
            'metrics.icloud.com', 'googleads.g.doubleclick.net', 'adservice.google.com',
            'app-measurement.com', 'analytics.google.com', 'ad.doubleclick.net',
            'connect.facebook.net'
        }

    def interceptRequest(self, info):
        host = info.requestUrl().host().lower()
        for allowed in self.whitelist:
            if host == allowed or host.endswith('.' + allowed):
                return
        if host in self.ad_hosts:
            info.block(True)


class KageBrowser(QMainWindow):
    def __init__(self, empty_tab=False):
        super().__init__()
        KAGE_WINDOWS.append(self)
        self.setWindowTitle('KageBrowser 4.6')
        self.resize(1366, 768)
        icon_path = get_resource_path('kagebrowser_logo.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.profile = get_shared_profile()
        self.downloads_popup = KageDownloadsPopup(self)
        self.zoom_toast = KageZoomToast(self)
        if not getattr(self.profile, '_dl_connected', False):
            self.profile.downloadRequested.connect(KageBrowser.global_handle_download)
            self.profile._dl_connected = True

        self.setup_ui()
        self.setup_shortcuts()
        self.setStyleSheet(KageStyle.get_style())
        if empty_tab:
            self.add_new_tab(None, 'Новая вкладка')
        else:
            self.add_new_tab(HOME_URL, 'Новая вкладка')
        self._sync_nav_actions()
        QApplication.instance().installEventFilter(self)

    @classmethod
    def global_handle_download(cls, download):
        target_win = QApplication.activeWindow()
        if not isinstance(target_win, KageBrowser) and KAGE_WINDOWS:
            target_win = KAGE_WINDOWS[-1]
        if isinstance(target_win, KageBrowser):
            target_win.handle_download_requested(download)

    def closeEvent(self, event):
        if self in KAGE_WINDOWS:
            KAGE_WINDOWS.remove(self)
        super().closeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'zoom_toast') and self.zoom_toast.isVisible():
            self.zoom_toast.move(self.width() - 84, self.toolbar.geometry().bottom() + 38)

    def _create_btn(self, icon_name, tooltip, slot=None, icon_size=20):
        btn = QPushButton()
        btn.setObjectName('NavBtn')
        btn.setIcon(get_svg_icon(icon_name, color='#d8d8d8', disabled_color='#383838'))
        btn.setIconSize(QSize(icon_size, icon_size))
        btn.setFixedSize(34, 34)
        btn.setToolTip(tooltip)
        if slot:
            btn.clicked.connect(slot)
        return btn

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Escape:
            if getattr(self, '_is_html5_fullscreen', False):
                current = self.tabs.currentWidget()
                if current:
                    current.triggerPageAction(QWebEnginePage.WebAction.ExitFullScreen)
                    current.page().runJavaScript('if(document.fullscreenElement) document.exitFullscreen();')
                    return True
        if obj == self.url_bar and event.type() == QEvent.Type.Resize:
            if hasattr(self, 'btn_search') and self.btn_search.isVisible():
                x = self.url_bar.width() - 34
                y = (self.url_bar.height() - 26) // 2
                self.btn_search.move(x, y)
        if event.type() == QEvent.Type.Wheel:
            mods = event.modifiers() | QApplication.keyboardModifiers()
            if mods & Qt.KeyboardModifier.AltModifier:
                delta = event.angleDelta().y() or event.angleDelta().x()
                if delta > 0:
                    self._prev_tab()
                elif delta < 0:
                    self._next_tab()
                return True
            elif mods & Qt.KeyboardModifier.ControlModifier:
                delta = event.angleDelta().y() or event.angleDelta().x()
                if delta > 0:
                    self._zoom_in()
                elif delta < 0:
                    self._zoom_out()
                return True
        return super().eventFilter(obj, event)

    def setup_ui(self):
        self.central = QWidget()
        self.setCentralWidget(self.central)
        layout = QVBoxLayout(self.central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)

        self.btn_back = self._create_btn('back', 'Назад (Alt+Left / Кнопка 4 мыши)', self._go_back)
        self.btn_forward = self._create_btn('forward', 'Вперёд (Alt+Right / Кнопка 5 мыши)', self._go_forward)
        self.btn_reload = self._create_btn('reload', 'Перезагрузить (Ctrl+R / F5)', self._reload_or_stop_page)
        for b in (self.btn_back, self.btn_forward, self.btn_reload):
            self.toolbar.addWidget(b)

        self.url_bar = QLineEdit()
        self.url_bar.setObjectName('AddressBar')
        self.url_bar.setFixedHeight(34)
        self.url_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.url_bar.setPlaceholderText('Поиск или адрес...')
        self.url_bar.returnPressed.connect(self.navigate)
        self.url_bar.textEdited.connect(self._on_url_text_edited)
        self.url_bar.installEventFilter(self)
        self.toolbar.addWidget(self.url_bar)

        self.btn_search = QPushButton(self.url_bar)
        self.btn_search.setObjectName('AddressBarSearchBtn')
        self.btn_search.setFixedSize(26, 26)
        self.btn_search.setIcon(get_svg_icon('search', color='#d8d8d8', render_size=64))
        self.btn_search.setIconSize(QSize(14, 14))
        self.btn_search.setToolTip('Найти / Перейти (Enter)')
        self.btn_search.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_search.clicked.connect(self.navigate)

        self.search_opacity = QGraphicsOpacityEffect(self.btn_search)
        self.btn_search.setGraphicsEffect(self.search_opacity)
        self.search_fade_anim = QPropertyAnimation(self.search_opacity, b'opacity')
        self.search_fade_anim.setDuration(180)
        self.search_fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.search_pos_anim = QPropertyAnimation(self.btn_search, b'pos')
        self.search_pos_anim.setDuration(180)
        self.search_pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.search_opacity.setOpacity(0.0)
        self.btn_search.hide()

        self.btn_add = self._create_btn('plus', 'Новая вкладка (Ctrl+T)', lambda: self.add_new_tab(HOME_URL, 'Новая вкладка'), 18)
        self.btn_downloads = self._create_btn('download', 'Загрузки (Ctrl+J)', self.toggle_downloads_popup, 18)
        self.btn_toggle_tabs = self._create_btn('chevron_up', 'Скрыть/показать вкладки (Ctrl+Shift+T)', self.toggle_tabs_visibility, 18)

        for b in (self.btn_add, self.btn_downloads, self.btn_toggle_tabs):
            self.toolbar.addWidget(b)

        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName('LoadingBar')
        self.progress_bar.setFixedHeight(2)
        self.progress_bar.setTextVisible(False)
        self.progress_opacity = QGraphicsOpacityEffect(self.progress_bar)
        self.progress_bar.setGraphicsEffect(self.progress_opacity)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        self.progress_val_anim = QPropertyAnimation(self.progress_bar, b'value')
        self.progress_val_anim.setDuration(120)
        self.progress_val_anim.setEasingCurve(QEasingCurve.Type.OutQuad)

        self.progress_fade_anim = QPropertyAnimation(self.progress_opacity, b'opacity')
        self.progress_fade_anim.setDuration(180)
        self.progress_fade_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.progress_fade_anim.finished.connect(self._on_progress_fade_finished)

        self.tabs = KageTabWidget()
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tabs)

    def _on_url_text_edited(self, text):
        if bool(text.strip()):
            self._show_search_btn_animated()
        else:
            self._hide_search_btn_animated()

    def _show_search_btn_animated(self):
        target_x = self.url_bar.width() - 34
        target_y = (self.url_bar.height() - 26) // 2
        if not self.btn_search.isVisible():
            self.btn_search.move(target_x + 6, target_y)
            self.btn_search.show()
        self.search_fade_anim.stop()
        self.search_fade_anim.setStartValue(self.search_opacity.opacity())
        self.search_fade_anim.setEndValue(1.0)
        self.search_fade_anim.start()

        self.search_pos_anim.stop()
        self.search_pos_anim.setStartValue(self.btn_search.pos())
        self.search_pos_anim.setEndValue(QPoint(target_x, target_y))
        self.search_pos_anim.start()

    def _hide_search_btn_animated(self):
        if not self.btn_search.isVisible():
            return
        self.search_fade_anim.stop()
        self.search_fade_anim.setStartValue(self.search_opacity.opacity())
        self.search_fade_anim.setEndValue(0.0)
        try:
            self.search_fade_anim.finished.disconnect()
        except Exception:
            pass
        def on_done():
            if self.search_opacity.opacity() == 0.0:
                self.btn_search.hide()
        self.search_fade_anim.finished.connect(on_done)
        self.search_fade_anim.start()

    def _on_progress_fade_finished(self):
        if self.progress_opacity.opacity() == 0.0:
            self.progress_bar.hide()

    def _sync_nav_actions(self):
        current = self.tabs.currentWidget()
        if current:
            self.btn_back.setEnabled(current.pageAction(QWebEnginePage.WebAction.Back).isEnabled())
            self.btn_forward.setEnabled(current.pageAction(QWebEnginePage.WebAction.Forward).isEnabled())
        else:
            self.btn_back.setEnabled(False)
            self.btn_forward.setEnabled(False)

    def toggle_fullscreen_mode(self):
        if self.isFullScreen():
            if getattr(self, '_pre_f11_maximized', False):
                self.showMaximized()
            else:
                self.showNormal()
            self.toolbar.show()
            self.tabs.tab_container.show()
        else:
            self._pre_f11_maximized = self.isMaximized()
            self.showFullScreen()

    def toggle_tabs_visibility(self):
        is_visible = self.tabs.toggle_tabs_visibility()
        if is_visible:
            self.btn_toggle_tabs.setIcon(get_svg_icon('chevron_up', color='#d8d8d8'))
            self.btn_toggle_tabs.setToolTip('Скрыть вкладки (Ctrl+Shift+T)')
        else:
            self.btn_toggle_tabs.setIcon(get_svg_icon('chevron_down', color='#d8d8d8'))
            self.btn_toggle_tabs.setToolTip('Показать вкладки (Ctrl+Shift+T)')

    def toggle_downloads_popup(self):
        if datetime.datetime.now().timestamp() - getattr(self.downloads_popup, '_last_close_time', 0) < 0.25:
            return
        if self.downloads_popup.isVisible():
            self.downloads_popup.hide_animated()
        else:
            self.downloads_popup.show_below(self.btn_downloads)

    def handle_download_requested(self, download):
        try:
            downloads_dir = self.downloads_popup.download_dir
            os.makedirs(downloads_dir, exist_ok=True)
            suggested = download.suggestedFileName() or 'download'
            clean = re.sub(r'[\\/*?:"<>|]', '_', suggested).strip('. ') or 'download'
            if download.isSavePageDownload() and not clean.endswith(('.html', '.htm', '.mhtml')):
                clean += '.mhtml'
            base, ext = os.path.splitext(clean)
            target_path = os.path.join(downloads_dir, clean)
            counter = 1
            while os.path.exists(target_path):
                target_path = os.path.join(downloads_dir, f'{base} ({counter}){ext}')
                counter += 1
            download.setDownloadDirectory(downloads_dir)
            download.setDownloadFileName(os.path.basename(target_path))
            download.accept()
            self.downloads_popup.add_download(download, target_path)
            self.downloads_popup.show_below(self.btn_downloads)
        except Exception:
            pass

    def setup_shortcuts(self):
        shortcuts = [
            ("Alt+Left", self._go_back), ("Alt+Right", self._go_forward),
            (Qt.Key.Key_Back, self._go_back), (Qt.Key.Key_Forward, self._go_forward),
            ("Ctrl+R", self._reload_or_stop_page), ("F5", self._reload_or_stop_page),
            ("Escape", self._stop_page_load),
            ("F11", self.toggle_fullscreen_mode), ("Ctrl+T", lambda: self.add_new_tab(HOME_URL, 'Новая вкладка')),
            ("Ctrl+W", lambda: self.close_tab(self.tabs.currentIndex())),
            ("Ctrl+Tab", self._next_tab), ("Ctrl+Shift+Tab", self._prev_tab),
            ("Ctrl+Shift+T", self.toggle_tabs_visibility), ("Ctrl+J", self.toggle_downloads_popup),
            ("Ctrl+L", lambda: (self.url_bar.setFocus(), self.url_bar.selectAll())),
            ("Ctrl+=", self._zoom_in), ("Ctrl++", self._zoom_in),
            ("Ctrl+-", self._zoom_out), ("Ctrl+0", self._zoom_reset)
        ]
        for key, slot in shortcuts:
            QShortcut(QKeySequence(key), self, slot)

    def _zoom_in(self):
        current = self.tabs.currentWidget()
        if current:
            new_val = min(5.0, round(current.zoomFactor() + 0.1, 2))
            current.setZoomFactor(new_val)
            self._show_zoom_toast(new_val)

    def _zoom_out(self):
        current = self.tabs.currentWidget()
        if current:
            new_val = max(0.25, round(current.zoomFactor() - 0.1, 2))
            current.setZoomFactor(new_val)
            self._show_zoom_toast(new_val)

    def _zoom_reset(self):
        current = self.tabs.currentWidget()
        if current:
            current.setZoomFactor(1.0)
            self._show_zoom_toast(1.0)

    def _show_zoom_toast(self, factor):
        tb_geo = self.toolbar.geometry()
        target_y = tb_geo.bottom() + 38
        self.zoom_toast.show_zoom(factor, target_y)

    def _next_tab(self):
        if self.tabs.count() > 1:
            self.tabs.setCurrentIndex((self.tabs.currentIndex() + 1) % self.tabs.count())

    def _prev_tab(self):
        if self.tabs.count() > 1:
            self.tabs.setCurrentIndex((self.tabs.currentIndex() - 1 + self.tabs.count()) % self.tabs.count())

    def _go_back(self):
        if self.tabs.currentWidget():
            self.tabs.currentWidget().triggerPageAction(QWebEnginePage.WebAction.Back)

    def _go_forward(self):
        if self.tabs.currentWidget():
            self.tabs.currentWidget().triggerPageAction(QWebEnginePage.WebAction.Forward)

    def _reload_or_stop_page(self):
        current = self.tabs.currentWidget()
        if current:
            if self.progress_bar.isVisible() and self.progress_bar.value() < 100:
                current.triggerPageAction(QWebEnginePage.WebAction.Stop)
            else:
                current.triggerPageAction(QWebEnginePage.WebAction.Reload)

    def _stop_page_load(self):
        if getattr(self, '_is_html5_fullscreen', False):
            current = self.tabs.currentWidget()
            if current:
                current.triggerPageAction(QWebEnginePage.WebAction.ExitFullScreen)
                current.page().runJavaScript('if(document.fullscreenElement) document.exitFullscreen();')
            return
        current = self.tabs.currentWidget()
        if current:
            current.triggerPageAction(QWebEnginePage.WebAction.Stop)

    def _close_tab_by_widget(self, browser_widget):
        idx = self.tabs.indexOf(browser_widget)
        if idx != -1:
            self.close_tab(idx)

    def add_new_tab(self, qurl=None, label='Новая вкладка'):
        self.tabs.ensure_tabs_visible()
        self.btn_toggle_tabs.setIcon(get_svg_icon('chevron_up', color='#d8d8d8'))
        self.btn_toggle_tabs.setToolTip('Скрыть вкладки (Ctrl+Shift+T)')

        browser = KageWebView(self.profile)
        browser.page().featurePermissionRequested.connect(
            lambda f, ft: browser.page().setFeaturePermission(f, ft, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser)
        )
        if qurl is not None:
            target_url = HOME_URL if (qurl == HOME_URL or qurl.toString() in ('', 'about:blank')) else qurl
            browser.setUrl(target_url)

        close_btn = QPushButton()
        close_btn.setObjectName('TabCloseBtn')
        close_btn.setIcon(get_svg_icon('close', color='#8c8c8c', render_size=96, stroke_width='2.4'))
        close_btn.setIconSize(QSize(16, 16))
        close_btn.setFixedSize(24, 24)
        close_btn.setToolTip('Закрыть вкладку (Ctrl+W / Клик колёсиком)')
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(lambda _, b=browser: self._close_tab_by_widget(b))

        idx = self.tabs.addTab(browser, get_svg_icon('globe', color='#8c8c8c'), f'  {label}', close_btn)
        self.tabs.setCurrentIndex(idx)

        browser.pageAction(QWebEnginePage.WebAction.Back).changed.connect(self._sync_nav_actions)
        browser.pageAction(QWebEnginePage.WebAction.Forward).changed.connect(self._sync_nav_actions)
        browser.urlChanged.connect(lambda q: (self._on_url_change(q, browser), self._sync_nav_actions()))
        browser.titleChanged.connect(lambda t: self._on_title_change(t, browser))
        browser.iconChanged.connect(lambda ico: self._on_icon_change(ico, browser))
        browser.loadProgress.connect(lambda p: self._on_load_progress(p, browser))
        browser.loadFinished.connect(lambda ok: (self._on_load_finished(ok, browser), self._sync_nav_actions()))
        self._sync_nav_actions()
        return browser

    def navigate(self):
        text = self.url_bar.text().strip()
        if not text:
            return
        self._hide_search_btn_animated()
        if '.' not in text or ' ' in text:
            url = QUrl(SEARCH_ENGINE + text.replace(' ', '+'))
        else:
            if not text.startswith(('http://', 'https://', 'file:///')):
                text = 'https://' + text
            url = QUrl(text)
        if self.tabs.currentWidget():
            self.tabs.currentWidget().setUrl(url)

    def _on_url_change(self, qurl, browser):
        if browser == self.tabs.currentWidget():
            url_str = qurl.toString()
            is_home = (qurl == HOME_URL or url_str.startswith('data:text/html') or url_str in ('', 'about:blank') or url_str.endswith('/start.html'))
            self.url_bar.setText('' if is_home else url_str)
            self._hide_search_btn_animated()

    def _on_title_change(self, title, browser):
        idx = self.tabs.indexOf(browser)
        if idx != -1:
            url_str = browser.url().toString()
            is_home = (browser.url() == HOME_URL or not title or title.startswith('data:text/html') or title == 'about:blank' or url_str.endswith('/start.html'))
            clean = 'Новая вкладка' if is_home else title
            if len(clean) > 28:
                clean = clean[:25] + '...'
            self.tabs.setTabText(idx, f'  {clean}')

    def _on_icon_change(self, icon, browser):
        idx = self.tabs.indexOf(browser)
        if idx != -1:
            url_str = browser.url().toString()
            is_home = (browser.url() == HOME_URL or url_str.endswith('/start.html'))
            if is_home:
                self.tabs.setTabIcon(idx, get_svg_icon('globe', color='#8c8c8c'))
            else:
                self.tabs.setTabIcon(idx, QIcon(icon.pixmap(16, 16)) if not icon.isNull() else get_svg_icon('globe', color='#8c8c8c'))

    def _on_load_progress(self, progress, browser):
        if browser == self.tabs.currentWidget():
            if progress < 100:
                self.btn_reload.setIcon(get_svg_icon('stop', color='#d8d8d8'))
                self.btn_reload.setToolTip('Остановить загрузку (Esc)')
                if not self.progress_bar.isVisible():
                    self.progress_fade_anim.stop()
                    self.progress_opacity.setOpacity(1.0)
                    self.progress_bar.show()
                self.progress_val_anim.stop()
                self.progress_val_anim.setStartValue(self.progress_bar.value())
                self.progress_val_anim.setEndValue(progress)
                self.progress_val_anim.start()
            else:
                self.btn_reload.setIcon(get_svg_icon('reload', color='#d8d8d8'))
                self.btn_reload.setToolTip('Перезагрузить (Ctrl+R / F5)')
                self.progress_val_anim.stop()
                self.progress_bar.setValue(100)
                self.progress_fade_anim.stop()
                self.progress_fade_anim.setStartValue(1.0)
                self.progress_fade_anim.setEndValue(0.0)
                self.progress_fade_anim.start()

    def _on_load_finished(self, ok, browser):
        if browser == self.tabs.currentWidget():
            self.btn_reload.setIcon(get_svg_icon('reload', color='#d8d8d8'))
            self.btn_reload.setToolTip('Перезагрузить (Ctrl+R / F5)')
            self.progress_fade_anim.stop()
            self.progress_fade_anim.setStartValue(self.progress_opacity.opacity())
            self.progress_fade_anim.setEndValue(0.0)
            self.progress_fade_anim.start()

    def _on_tab_changed(self, idx):
        browser = self.tabs.widget(idx)
        if browser:
            url_str = browser.url().toString()
            is_home = (browser.url() == HOME_URL or url_str.startswith('data:text/html') or url_str in ('', 'about:blank') or url_str.endswith('/start.html'))
            self.url_bar.setText('' if is_home else url_str)
            self._hide_search_btn_animated()
            self.progress_fade_anim.stop()
            self.progress_bar.hide()
            self.btn_reload.setIcon(get_svg_icon('reload', color='#d8d8d8'))
            self.btn_reload.setToolTip('Перезагрузить (Ctrl+R / F5)')
            self._sync_nav_actions()

    def close_tab(self, idx):
        if self.tabs.count() > 1:
            curr = self.tabs.currentIndex()
            if curr == idx:
                next_idx = idx - 1 if idx > 0 else 1
                self.tabs.setCurrentIndex(next_idx)

            def do_remove(i):
                widget = self.tabs.widget(i)
                self.tabs.removeTab(i)
                if widget:
                    widget.deleteLater()
                self._sync_nav_actions()

            self.tabs.tabBar().animate_close_tab(idx, do_remove)
        else:
            self.tabs.widget(0).setUrl(HOME_URL)
            self.tabs.setTabText(0, '  Новая вкладка')
            self.tabs.setTabIcon(0, get_svg_icon('globe', color='#8c8c8c'))
            self.url_bar.setText('')
            self._sync_nav_actions()


if __name__ == '__main__':
    os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--enable-gpu-rasterization --enable-gpu-compositing --num-raster-threads=4 --enable-media-stream --no-sandbox --disable-logging --log-level=3'
    app = QApplication(sys.argv)
    window = KageBrowser()
    window.show()
    sys.exit(app.exec())