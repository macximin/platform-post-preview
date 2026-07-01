"""platform_post_preview — 캐릭터 소셜앱 화면 프리뷰 (내부 검토용).

`characters/<slug>/` 의 canon.md + images/ 를 **직접 로드**해서 홈 피드 / 캐릭터 프로필 /
포스트 상세 화면 구조를 미리본다. 사이드바 수동 입력 없이 repo 데이터가 원본.
특정 플랫폼 로고/상표/원본 UI는 복제하지 않는 일반화 UI. 외부 게시용 아님.

이미지 규칙: images/기준선.png = 대표/아바타, images/인스타_<제목>.png = 포스트(제목=캡션).
"""

import base64
import html
import io
import re
from pathlib import Path

import streamlit as st
from PIL import Image, ImageOps

st.set_page_config(page_title="platform_post_preview", page_icon="🖼️", layout="centered")

# --- 선택적 비밀번호 게이트: Streamlit Cloud > Settings > Secrets 에 app_password 를 넣으면 활성화 ---
try:
    _APP_PW = st.secrets.get("app_password", "")
except Exception:
    _APP_PW = ""
if _APP_PW:
    if not st.session_state.get("_authed"):
        _pw = st.text_input("접근 비밀번호", type="password")
        if _pw and _pw == _APP_PW:
            st.session_state["_authed"] = True
            st.rerun()
        elif _pw:
            st.error("비밀번호가 틀렸습니다.")
        if not st.session_state.get("_authed"):
            st.stop()

ACCENT = "#8b5cf6"
CHARS_DIR = Path(__file__).resolve().parent / "characters"
DEMO_FOLLOWERS = "2.1만"   # canon에 없는 데모 수치 (프리뷰용)
DEMO_FOLLOWING = "187"

COMING_SOON_CHARS = [
    {"slug": "awkward-actress", "name": "예쁜데 못 뜬 배우"},
    {"slug": "engineering-areumi", "name": "공대 아름이"},
    {"slug": "ex-before-wedding", "name": "정서아"},
    {"slug": "gomshin-leave-night", "name": "휴가 나온 남친을 만나 주는 곰신"},
    {"slug": "room-gamer-girl", "name": "방구석 겜순이형 여성"},
    {"slug": "secret-account-senior", "name": "뒷계정 들킨 회사 선배"},
]


# ------------------------------------------------ 이미지 헬퍼
def _prep(img: Image.Image, ratio: float) -> Image.Image:
    img = ImageOps.exif_transpose(img).convert("RGB")
    w, h = img.size
    if w / h > ratio:
        nw = int(round(h * ratio))
        img = img.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = int(round(w / ratio))
        img = img.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    img.thumbnail((1080, 1350))
    return img


def _to_uri(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=86)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


@st.cache_data(show_spinner=False)
def img_uri(path_str: str, mtime: int, ratio: float) -> str:
    return _to_uri(_prep(Image.open(path_str), ratio))


def esc(s) -> str:
    return html.escape(s or "")


def tag(ref, ratio):
    if ref:
        return (
            f'<img src="{img_uri(ref["path"], ref["mtime"], ratio)}" '
            'style="width:100%;height:100%;object-fit:cover;display:block;"/>'
        )
    return (
        '<div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;'
        'background:linear-gradient(135deg,#2b2b3a,#4a3a4f);color:#cdb9c9;font-size:0.8rem;">이미지 없음</div>'
    )


def box45(ref):
    return (
        '<div style="position:relative;width:100%;padding-bottom:125%;background:#000;">'
        f'<div style="position:absolute;inset:0;">{tag(ref, 4 / 5)}</div></div>'
    )


# ------------------------------------------------ 캐릭터 로딩 (canon.md + images/)
def parse_canon(text):
    fm, body = {}, text
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line and not line.lstrip().startswith("#"):
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip().strip('"')
        body = m.group(2)
    sections = {}
    for hm in re.finditer(r"(?ms)^##\s+(.+?)\s*\n(.*?)(?=^##\s|\Z)", body):
        sections[hm.group(1).strip()] = hm.group(2).strip()
    return fm, sections


def sect(sections, *needles):
    for k, v in sections.items():
        if any(n in k for n in needles):
            return v
    return ""


def bullets(t):
    return [re.sub(r"^[-*]\s*", "", ln).strip() for ln in t.splitlines() if ln.strip()[:1] in "-*"]


def quotes(t):
    out = []
    for ln in t.splitlines():
        s = ln.strip()
        if s.startswith(">"):
            s = s.lstrip(">").strip().strip('"').strip("“”")
            if s:
                out.append(s)
    return out


def split_tags(value):
    return [x.strip().lstrip("#") for x in re.split(r"[,/|]", value or "") if x.strip()]


def _sig(slug):
    d = CHARS_DIR / slug
    fs = [d / "canon.md"] + sorted((d / "images").glob("*"))
    return tuple((f.name, int(f.stat().st_mtime)) for f in fs if f.exists())


@st.cache_data(show_spinner=False)
def load_char(slug, sig):
    d = CHARS_DIR / slug
    fm, sc = parse_canon((d / "canon.md").read_text(encoding="utf-8"))
    imgs = d / "images"
    main = imgs / "기준선.png"
    posts = [
        {"path": str(p), "mtime": int(p.stat().st_mtime), "caption": p.stem[len("인스타_"):]}
        for p in sorted(imgs.glob("인스타_*.png"))
    ]
    age = fm.get("age", "")
    mnum = re.search(r"\d+", age)
    return {
        "slug": slug,
        "name": fm.get("instagram_display_name") or fm.get("name") or slug,
        "handle": fm.get("instagram_handle") or "@" + slug.replace("-", "_"),
        "age": mnum.group() if mnum else age,
        "job": fm.get("job", ""),
        "concept": fm.get("concept_title", "") or fm.get("name", ""),
        "intro": sect(sc, "소개"),
        "story": sect(sc, "스토리 개요"),
        "interests": bullets(sect(sc, "관심사")),
        "hobbies": bullets(sect(sc, "취미")),
        "hashtags": split_tags(fm.get("hashtags", "")),
        "says": quotes(sect(sc, "좋아하는 말")),
        "ideal": sect(sc, "이상형"),
        "main": {"path": str(main), "mtime": int(main.stat().st_mtime)} if main.exists() else None,
        "posts": posts,
    }


def list_chars():
    if not CHARS_DIR.exists():
        return []
    return [
        d.name
        for d in sorted(CHARS_DIR.iterdir())
        if d.is_dir() and d.name != "_TEMPLATE" and (d / "images" / "기준선.png").exists()
    ]


def char_label(slug):
    d = CHARS_DIR / slug
    if not (d / "canon.md").exists():
        return slug
    fm, _ = parse_canon((d / "canon.md").read_text(encoding="utf-8"))
    return fm.get("instagram_display_name") or fm.get("name") or slug


def list_char_options():
    ready = [{"slug": slug, "label": char_label(slug), "ready": True} for slug in list_chars()]
    ready_slugs = {item["slug"] for item in ready}
    waiting = [
        {"slug": item["slug"], "label": item["name"], "ready": False}
        for item in COMING_SOON_CHARS
        if item["slug"] not in ready_slugs
    ]
    return ready + waiting


def placeholder_char(option):
    return {
        "slug": option["slug"],
        "name": option["label"],
        "handle": "@" + option["slug"].replace("-", "_"),
        "age": "",
        "job": "",
        "concept": option["label"],
        "intro": "프리뷰 준비 중",
        "story": "",
        "interests": [],
        "hobbies": [],
        "hashtags": [],
        "says": [],
        "ideal": "",
        "main": None,
        "posts": [],
    }


# ------------------------------------------------ 프레임 / 공통 조각
FRAME_OPEN = (
    '<div style="max-width:390px;margin:0 auto;background:#0c0c0f;border:1px solid #24242a;'
    "border-radius:16px;overflow:hidden;font-family:-apple-system,'Segoe UI',Roboto,sans-serif;color:#eee;\">"
)
FRAME_CLOSE = "</div>"


def topbar(center="", back=True):
    left = '<span style="position:absolute;left:12px;color:#ddd;">‹</span>' if back else ""
    return (
        '<div style="position:relative;display:flex;align-items:center;justify-content:center;height:44px;'
        f'border-bottom:1px solid #1e1e24;font-weight:600;font-size:0.95rem;">{left}{esc(center)}</div>'
    )


def bottom_nav():
    items = [("🏠", "홈", True), ("💬", "대화", False), ("👤", "마이페이지", False)]
    cells = "".join(
        f'<div style="flex:1;text-align:center;color:{"#fff" if a else "#777"};font-size:0.62rem;">'
        f'<div style="font-size:1.1rem;">{ic}</div>{lb}</div>'
        for ic, lb, a in items
    )
    return '<div style="display:flex;border-top:1px solid #1e1e24;padding:7px 0 5px;">' + cells + "</div>"


def slide_controls(key, n):
    n = max(1, n)
    st.session_state.setdefault(key, 0)
    _, c_prev, c_mid, c_next, _ = st.columns([3, 1, 2, 1, 3])
    if c_prev.button("◀", key=f"{key}_p", use_container_width=True):
        st.session_state[key] -= 1
    if c_next.button("▶", key=f"{key}_n", use_container_width=True):
        st.session_state[key] += 1
    i = st.session_state[key] % n
    st.session_state[key] = i
    c_mid.markdown(
        f"<div style='text-align:center;color:#8a8a92;padding-top:6px;font-size:0.85rem;'>{i + 1} / {n}</div>",
        unsafe_allow_html=True,
    )
    return i


# ================================================================ 뷰
def render_home(char):
    logo = (
        '<div style="text-align:center;height:46px;line-height:46px;font-weight:800;font-size:1.05rem;'
        'border-bottom:1px solid #1e1e24;"><span style="color:#fff;">post</span>'
        f'<span style="color:{ACCENT};">preview</span></div>'
    )
    hero = (
        '<div style="position:relative;width:100%;padding-bottom:125%;background:#000;">'
        f'<div style="position:absolute;inset:0;">{tag(char["main"], 4 / 5)}</div>'
        '<div style="position:absolute;inset:0;background:linear-gradient(to top,rgba(0,0,0,.85),transparent 55%);"></div>'
        f'<div style="position:absolute;left:14px;bottom:70px;background:{ACCENT};color:#fff;'
        'padding:2px 9px;border-radius:6px;font-size:0.72rem;font-weight:700;">TOP 1</div>'
        f'<div style="position:absolute;left:14px;bottom:40px;right:14px;color:#fff;font-weight:700;'
        f'font-size:1.02rem;">{esc(char["concept"])}</div>'
        f'<div style="position:absolute;left:14px;bottom:12px;background:{ACCENT};color:#fff;'
        'padding:6px 16px;border-radius:999px;font-size:0.8rem;font-weight:600;">대화 미리보기</div></div>'
    )
    hashtags = ["#" + x.replace(" ", "") for x in (char["hashtags"] + char["interests"] + char["hobbies"])][:5]
    tagline = " ".join(f'<span style="color:#5a8fd6;">{esc(t)}</span>' for t in hashtags)
    hook = (char["intro"].split(".")[0] if char["intro"] else char["concept"])
    card = (
        '<div style="width:170px;flex:0 0 170px;border-radius:12px;overflow:hidden;background:#141418;border:1px solid #22222a;">'
        f"{box45(char['main'])}"
        f'<div style="padding:7px 9px 9px;"><div style="font-weight:600;font-size:0.85rem;">{esc(char["name"])}</div>'
        f'<div style="color:#bbb;font-size:0.72rem;margin:2px 0 5px;">{esc(hook)}</div>'
        f'<div style="font-size:0.68rem;">{tagline}</div></div></div>'
    )
    row = (
        '<div style="padding:12px;"><div style="font-weight:700;font-size:0.9rem;margin-bottom:8px;">🆕 새로 등장한 캐릭터</div>'
        '<div style="display:flex;gap:10px;overflow-x:auto;">' + card + "</div></div>"
    )
    st.markdown(FRAME_OPEN + logo + hero + row + bottom_nav() + FRAME_CLOSE, unsafe_allow_html=True)


def render_profile(char):
    ava = (
        f'<div style="width:100%;height:100%;">{tag(char["main"], 1.0)}</div>'
        if char["main"]
        else f'<div style="width:100%;height:100%;background:linear-gradient(135deg,#c94b7b,#7a4bc9);'
        f'display:flex;align-items:center;justify-content:center;font-weight:700;font-size:1.4rem;">{esc(char["name"][:1])}</div>'
    )
    stat = lambda v, l: (  # noqa: E731
        f'<div style="text-align:center;flex:1;"><div style="font-weight:700;">{esc(v)}</div>'
        f'<div style="color:#9a9aa2;font-size:0.72rem;">{l}</div></div>'
    )
    bio = []
    if char["age"] or char["job"]:
        bio.append("🖤 " + " · ".join(x for x in [char["age"], "Seoul"] if x))
    if char["interests"] or char["hobbies"]:
        bio.append("🍃 " + " · ".join(char["interests"] + char["hobbies"]))
    if char["intro"]:
        bio.append("✨ " + char["intro"].split(".")[0])
    bio_html = "<br/>".join(esc(x) for x in bio)

    head = (
        topbar(char["handle"].lstrip("@"))
        + '<div style="padding:14px 14px 6px;display:flex;gap:14px;align-items:center;">'
        '<div style="width:72px;height:72px;border-radius:50%;overflow:hidden;flex:0 0 72px;">' + ava + "</div>"
        '<div style="flex:1;"><div style="font-weight:700;font-size:1.05rem;margin-bottom:6px;">' + esc(char["name"]) + "</div>"
        '<div style="display:flex;">'
        + stat(str(len(char["posts"])), "게시물") + stat(DEMO_FOLLOWERS, "팔로워") + stat(DEMO_FOLLOWING, "팔로잉")
        + "</div></div></div>"
        + f'<div style="padding:0 14px 10px;font-size:0.83rem;color:#ddd;">{bio_html}</div>'
        + f'<div style="padding:0 14px 12px;"><div style="text-align:center;background:{ACCENT};color:#fff;'
        'padding:9px;border-radius:10px;font-weight:600;font-size:0.9rem;">🗨️ 대화 미리보기</div></div>'
    )
    st.markdown(FRAME_OPEN + head, unsafe_allow_html=True)

    t_grid, t_info = st.tabs(["▦  그리드", "ⓘ  정보"])
    with t_grid:
        pool = char["posts"] or [None] * 6
        cells = "".join(box45(p) for p in pool[:9])
        st.markdown(
            f'<div style="max-width:390px;margin:0 auto;display:grid;grid-template-columns:repeat(3,1fr);gap:2px;">{cells}</div>',
            unsafe_allow_html=True,
        )
    with t_info:
        story_html = esc(char["story"]).replace("\n\n", "<PBR>").replace("\n", "<br/>").replace("<PBR>", "<br/><br/>")
        chips = lambda xs: " ".join(  # noqa: E731
            f'<span style="background:#20202a;border-radius:999px;padding:2px 9px;margin-right:4px;font-size:0.8rem;">{esc(x)}</span>'
            for x in xs
        )
        say_html = "<br/>".join(f"“{esc(x)}”" for x in char["says"])

        def s(icon, title, body):
            return (
                f'<div style="margin-bottom:14px;"><div style="font-weight:700;margin-bottom:5px;">{icon} {title}</div>'
                f'<div style="color:#f5f5f5;font-size:0.85rem;line-height:1.55;">{body}</div></div>'
            )

        info = (
            s("📖", "스토리 개요", story_html)
            + s("✨", "관심사", chips(char["interests"]))
            + s("🎯", "취미", chips(char["hobbies"]))
            + s("💬", "좋아하는 말", say_html)
            + s("💕", "이상형", esc(char["ideal"]))
        )
        st.markdown(f'<div style="max-width:390px;margin:0 auto;padding:14px 4px;">{info}</div>', unsafe_allow_html=True)
    st.markdown('<div style="max-width:390px;margin:0 auto;">' + bottom_nav() + FRAME_CLOSE, unsafe_allow_html=True)


def render_post(char):
    posts = char["posts"]
    i = slide_controls("post_i", len(posts))  # ◀ ▶ 이전/다음 포스트
    p = posts[i] if posts else None
    caption = p["caption"] if p else ""
    body = (
        topbar("게시물")
        + box45(p)
        + '<div style="padding:10px 14px 4px;font-size:1.25rem;color:#e5405e;">♡ '
        '<span style="color:#fff;font-size:0.85rem;font-weight:600;vertical-align:middle;">1,284</span></div>'
        f'<div style="padding:2px 14px 14px;font-size:0.88rem;"><b style="color:#fff;">{esc(char["handle"])}</b> '
        f'<span style="color:#ddd;">{esc(caption)}</span></div>'
    )
    st.markdown(FRAME_OPEN + body + bottom_nav() + FRAME_CLOSE, unsafe_allow_html=True)


# ================================================================ 상단 컨트롤 + 라우팅
char_options = list_char_options()
if not char_options:
    st.error(f"`기준선.png` 이미지를 가진 캐릭터 폴더가 없습니다:\n\n`{CHARS_DIR}`")
    st.stop()

option_by_slug = {item["slug"]: item for item in char_options}
slugs = [item["slug"] for item in char_options]
default_slug = "officetel-classmate" if "officetel-classmate" in slugs else slugs[0]
slug = st.selectbox(
    "캐릭터",
    slugs,
    index=slugs.index(default_slug),
    format_func=lambda key: option_by_slug[key]["label"],
    label_visibility="collapsed",
)
selected_option = option_by_slug[slug]
char = load_char(slug, _sig(slug)) if selected_option["ready"] else placeholder_char(selected_option)

VIEWS = ["🏠 홈 피드", "👤 캐릭터 프로필", "🖼️ 포스트 상세"]
st.session_state.setdefault("view_i", 0)
navL, navC, navR = st.columns([1, 3, 1])
if navL.button("◀ 이전 화면", use_container_width=True):
    st.session_state["view_i"] = (st.session_state["view_i"] - 1) % len(VIEWS)
if navR.button("다음 화면 ▶", use_container_width=True):
    st.session_state["view_i"] = (st.session_state["view_i"] + 1) % len(VIEWS)
view = VIEWS[st.session_state["view_i"]]
navC.markdown(
    f"<div style='text-align:center;font-weight:700;padding-top:6px;'>{view}"
    f" &nbsp;·&nbsp; {st.session_state['view_i'] + 1}/{len(VIEWS)}</div>",
    unsafe_allow_html=True,
)

if view.startswith("🏠"):
    render_home(char)
elif view.startswith("👤"):
    render_profile(char)
else:
    render_post(char)

source_note = f"`characters/{slug}` 데이터 로드" if selected_option["ready"] else f"`{selected_option['label']}` 이름만 표시"
st.caption(f"· 내부 검토용 목업 · {source_note} · 특정 서비스 UI/로고/CTA 복제 아님 · 가상 성인 캐릭터 ·")
