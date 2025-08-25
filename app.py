# Streamlit app: display a local or uploaded HTML file
# -----------------------------------------------------
# Features
# - Upload an HTML file OR type a path to a local HTML file
# - Two rendering modes:
#     1) Embed (srcdoc): reads the file and embeds the HTML directly
#        (simple, but relative asset links may not load)
#     2) Static server: spins up a tiny HTTP server to serve the file's folder,
#        so relative assets (CSS/JS/images) work. (Best for complex exports)
# - Adjustable iframe height, dark background toggle, and download button
#
# Usage:
#   streamlit run streamlit_show_html.py
# -----------------------------------------------------

import os
import io
import sys
import time
import mimetypes
import threading
import socket
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from pathlib import Path

import streamlit as st
from streamlit.components.v1 import html as st_html

st.set_page_config(page_title="HTML Viewer", layout="wide")

# ---------------------- helpers ----------------------

def _read_text(path: Path) -> str:
    # Try UTF-8 first; fallback to latin-1 to avoid surprises
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("localhost", 0))
        return s.getsockname()[1]


class _QuietHandler(SimpleHTTPRequestHandler):
    # Reduce logging noise in Streamlit terminal
    def log_message(self, format, *args):  # noqa: N802 (keep signature)
        pass


def _start_static_server(root_dir: Path, port: int) -> TCPServer:
    # Change working directory for the handler to serve from root_dir
    # We create a handler subclass bound to that directory
    os.chdir(root_dir)
    httpd = TCPServer(("localhost", port), _QuietHandler)

    def _serve():
        try:
            httpd.serve_forever()
        except Exception:
            pass

    t = threading.Thread(target=_serve, daemon=True)
    t.start()
    return httpd


def _stop_static_server(server: TCPServer | None):
    if server is not None:
        try:
            server.shutdown()
        except Exception:
            pass
        try:
            server.server_close()
        except Exception:
            pass


# Persist server state between reruns
if "_static_server" not in st.session_state:
    st.session_state._static_server = None
if "_static_root" not in st.session_state:
    st.session_state._static_root = None
if "_static_port" not in st.session_state:
    st.session_state._static_port = None

# ---------------------- UI ----------------------

st.title("📄 HTML Viewer (Streamlit)")

colA, colB = st.columns([2, 1])
with colA:
    uploaded = st.file_uploader("Upload an HTML file", type=["html", "htm"], accept_multiple_files=False)
    path_str = st.text_input("...or enter a local path to an HTML file", value="", placeholder="/path/to/file.html")

with colB:
    mode = st.radio("Rendering mode", ["Embed (srcdoc)", "Static server (handles assets)"], index=1, help="Use 'Static server' if your HTML uses relative CSS/JS/images.")
    iframe_h = st.number_input("Iframe height (px)", min_value=200, max_value=5000, value=900, step=50)
    dark_bg = st.toggle("Dark page background", value=True)
    show_download = st.toggle("Show download button", value=True)

# Pick source
html_bytes = None
html_path: Path | None = None
html_name = None

if uploaded is not None:
    html_name = uploaded.name
    html_bytes = uploaded.read()
    # Save to a temp file inside Streamlit's cache dir so static server can serve it if needed
    tmp_dir = Path(st.experimental_user) if hasattr(st, "experimental_user") else Path(os.getcwd())
    # Fallback to a subdir in CWD to avoid permission fuss
    tmp_dir = tmp_dir / "._html_viewer_cache"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    html_path = tmp_dir / html_name
    html_path.write_bytes(html_bytes)
elif path_str.strip():
    p = Path(path_str).expanduser().resolve()
    if p.exists() and p.is_file():
        html_path = p
        html_name = p.name
        try:
            html_bytes = p.read_bytes()
        except Exception as e:
            st.error(f"Failed to read file: {e}")
    else:
        st.warning("Path does not exist or is not a file.")

# Styling
bg_color = "#0e1117" if dark_bg else "#ffffff"
st.markdown(
    f"""
    <style>
    .stApp {{ background-color: {bg_color}; }}
    .viewer-container iframe {{ border: 1px solid #444; border-radius: 8px; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------- Render ----------------------

if html_path is None:
    st.info("Upload a file or enter a path to begin.")
    st.stop()

st.caption(f"Selected: **{html_name}**  •  Location: `{str(html_path)}`")

if show_download and html_bytes is not None:
    st.download_button("⬇️ Download HTML", data=html_bytes, file_name=html_name, mime="text/html")

placeholder = st.empty()

if mode.startswith("Embed"):
    try:
        content = _read_text(html_path)
    except Exception as e:
        st.error(f"Could not read HTML: {e}")
    else:
        with placeholder.container():
            st_html(content, height=int(iframe_h), scrolling=True)
    # Stop any static server if running
    if st.session_state._static_server is not None:
        _stop_static_server(st.session_state._static_server)
        st.session_state._static_server = None
        st.session_state._static_root = None
        st.session_state._static_port = None
else:
    # Serve the parent directory so relative assets resolve
    root = html_path.parent
    needs_restart = (
        st.session_state._static_server is None
        or st.session_state._static_root != str(root)
    )
    if needs_restart:
        _stop_static_server(st.session_state._static_server)
        port = _find_free_port()
        server = _start_static_server(root, port)
        st.session_state._static_server = server
        st.session_state._static_root = str(root)
        st.session_state._static_port = port
        time.sleep(0.1)  # small grace period

    port = st.session_state._static_port
    src = f"/Users/edeneldar/beta_comparison/corr_beta_MULTI_REPORT.html"

    with placeholder.container():
        st.markdown(
            f"<div class='viewer-container'><iframe src='{src}' width='100%' height='{int(iframe_h)}'></iframe></div>",
            unsafe_allow_html=True,
        )

# Footer
st.caption("Tip: If your HTML uses big local assets, prefer 'Static server' mode so relative links resolve correctly.")
