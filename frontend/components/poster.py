import hashlib
import logging
from html import escape
from io import BytesIO
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests
import streamlit as st
from PIL import Image, ImageOps

from frontend.utils.api import get_api_base_url


_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_LOCAL_ARTWORK = Path("frontend") / "pictures"
_MAX_POSTER_BYTES = 8 * 1024 * 1024
_POSTER_DIMENSIONS = {
    "card": (1000, 1500),
    "hero": (1600, 900),
    "compact": (960, 720),
}
_ARTWORK_RULES = (
    (("cricket", "sports", "sport"), "cricket.jpg"),
    (("comedy", "stand-up", "standup", "comic"), "comedy.jpg"),
    (("movie", "movies", "cinema", "film"), "movie.jpg"),
    (("concert", "concerts", "music", "band"), "concert.jpg"),
    (("technology", "tech", "conference", "startup"), "techfest.jpg"),
    (("theatre", "theater", "play", "drama"), "theatre.jpg"),
)
_logger = logging.getLogger(__name__)


def _safe_local_image_path(value):
    if not value:
        return None
    path = Path(str(value))
    if not path.is_absolute():
        path = _PROJECT_ROOT / path
    try:
        resolved = path.resolve()
        resolved.relative_to(_PROJECT_ROOT)
    except (OSError, ValueError):
        return None
    if resolved.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
        return None
    return resolved if resolved.is_file() else None


def resolve_poster_path(event):
    """Return a local event image or matching bundled artwork, if available."""
    for candidate in (event.get("poster_url"), event.get("image")):
        if candidate and not str(candidate).startswith(("http://", "https://")):
            path = _safe_local_image_path(candidate)
            if path:
                return path

    title = str(event.get("title", "")).casefold()
    category = str(event.get("category", "")).casefold()
    for text in (title, category):
        for keywords, filename in _ARTWORK_RULES:
            if any(keyword in text for keyword in keywords):
                return _PROJECT_ROOT / _LOCAL_ARTWORK / filename
    return None


def _trusted_upload_url(source):
    image_url = urlparse(source)
    backend_url = urlparse(get_api_base_url())
    path_parts = unquote(image_url.path).split("/")
    return (
        image_url.scheme in {"http", "https"}
        and image_url.scheme == backend_url.scheme
        and image_url.netloc == backend_url.netloc
        and len(path_parts) == 4
        and path_parts[:3] == ["", "uploads", "events"]
        and path_parts[3] not in {"", ".", ".."}
        and Path(path_parts[3]).name == path_parts[3]
        and Path(path_parts[3]).suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
    )


@st.cache_data(show_spinner=False, ttl=600, max_entries=128)
def _load_poster(source, width, height):
    if source.startswith(("http://", "https://")):
        if not _trusted_upload_url(source):
            raise ValueError("Poster URL is not a trusted event upload.")
        with requests.get(source, timeout=(1.5, 3), stream=True) as response:
            response.raise_for_status()
            content = bytearray()
            for chunk in response.iter_content(chunk_size=64 * 1024):
                content.extend(chunk)
                if len(content) > _MAX_POSTER_BYTES:
                    raise ValueError("Event poster exceeds the supported size.")
    else:
        content = Path(source).read_bytes()

    with Image.open(BytesIO(content)) as image:
        image.load()
        return ImageOps.fit(
            image.convert("RGB"),
            (width, height),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.42),
        )


def _poster_container_key(key, variant):
    suffix = hashlib.sha1(str(key).encode("utf-8")).hexdigest()[:12]
    return f"event-poster-{variant}-{suffix}"


def render_poster(event, key="poster", height=None, variant="compact"):
    width, target_height = _POSTER_DIMENSIONS.get(
        variant,
        _POSTER_DIMENSIONS["compact"],
    )
    container_key = _poster_container_key(key, variant)
    custom_source = event.get("poster_url") or event.get("image")
    local_path = resolve_poster_path(event)
    sources = []

    if custom_source and str(custom_source).startswith(("http://", "https://")):
        if _trusted_upload_url(str(custom_source)):
            sources.append(str(custom_source))
        else:
            _logger.warning("Ignoring event poster URL outside the configured upload service.")
    elif local_path:
        sources.append(str(local_path))

    fallback_path = resolve_poster_path({**event, "poster_url": None, "image": None})
    if fallback_path and str(fallback_path) not in sources:
        sources.append(str(fallback_path))

    image = None
    for source in sources:
        try:
            image = _load_poster(source, width, target_height)
            break
        except (OSError, ValueError, requests.RequestException, Image.DecompressionBombError) as error:
            _logger.warning("Could not load event poster (%s); trying themed fallback.", type(error).__name__)

    with st.container(key=container_key):
        if image is not None:
            st.image(
                image,
                width="stretch",
                output_format="auto",
                alt=f"Event poster for {event.get('title') or 'FlashReserve event'}",
            )
            return

        category = str(event.get("category", "LIVE EVENT")).upper()
        title = str(event.get("title", "FlashReserve"))
        st.markdown(
            f"<div class='poster-fallback'><span>{escape(category)}</span><strong>{escape(title)}</strong><small>FLASHRESERVE / LIVE EXPERIENCES</small></div>",
            unsafe_allow_html=True,
        )
