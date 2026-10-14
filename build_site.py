"""Build site/: a home page with the package downloads, and a three.js viewer.

The viewer page is web/viewer.html. It goes to site/viewer/ with the
installed-frame STLs (site/viewer/models) and site/viewer/manifest.json.
Run the package builds first. Serve with:
  python3 -m http.server 8800 --bind 0.0.0.0 --directory site
"""
import json
import os
import sys
import shutil

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "bittle_pi_addon"))
import pod  # noqa: E402

ROOT = pod.ROOT                                   # bittle_pi_addon/
SITE = os.path.join(os.path.dirname(ROOT), "site", "viewer")
MD = os.path.join(SITE, "models")

# id, label, group, source file, colour, explode offset (dx, dy, dz), extra transform
PARTS = [
    ("lid", "Pod lid", "Printed", "stl/installed/pod_lid.stl", "#f7b81a", (0, 60, 0), None),
    ("plug", "Charge-port plug (TPU)", "Printed", "stl/installed/usb_plug.stl", "#222222", (-12, 60, 0), None),
    ("tray", "Pod tray", "Printed", "stl/installed/pod_tray.stl", "#cfd2d6", (0, 12, 0), None),
    ("cover", "Stock cover + pegs", "Printed", "../bittle_platform/stl/installed/cover_pegs.stl", "#34363b", (0, 0, 0), None),
    ("pizero", "Raspberry Pi Zero 2 W", "Components", "stl/models/pizero.stl", "#2e9b4f", (0, 36, 0), None),
    ("pisugar", "PiSugar 2 board", "Components", "stl/models/pisugar2.stl", "#e06aa3", (0, 30, 0), None),
    ("battery", "1200 mAh cell", "Components", "stl/models/battery.stl", "#4a78d8", (0, 24, 0), None),
    ("amp", "NS4168 amp", "Components", "stl/models/amp_ns4168.stl", "#1f5f8f", (0, 30, 0), None),
    ("header", "BiBoard 5-pin header (est. height)", "Components", "stl/models/biboard_header.stl", "#0d0d0d", (0, 0, 0), None),
    ("plugs", "Dupont plugs + wire space", "Components", "stl/models/dupont_plugs.stl", "#d83a34", (0, 0, 0), None),
    ("slot", "Cover slot passage (wires)", "Components", "stl/models/cover_slot.stl", "#0d0d0d", (0, 0, 0), None),
    ("shoulder_r", "Side shoulder R", "Robot", "../bittle_platform/reference/Bittle_SideShoulder.stl", "#f2a71c", (0, 0, 0), None),
    ("shoulder_l", "Side shoulder L", "Robot", "../bittle_platform/reference/Bittle_SideShoulder.stl", "#f2a71c", (0, 0, 0), "mirror_x"),
    ("front_plate", "Front plate", "Robot", "../bittle_platform/reference/Bittle_FrontPlate.stl", "#26272b", (0, 0, 0), None),
    ("rear_plate", "Rear plate (mirror of front)", "Robot", "../bittle_platform/reference/Bittle_FrontPlate.stl", "#26272b", (0, 0, 0), "mirror_z"),
    ("speaker", "NULLLAB 3 W speaker (rump)", "Components", "stl/models/speaker.stl", "#7a52b8", (0, 30, 0), None),
    ("mic", "SPH0645 mic (front left)", "Components", "stl/models/mic_sph0645.stl", "#d83a34", (0, 30, 0), None),
]


def main():
    import shutil
    os.makedirs(MD, exist_ok=True)
    shutil.copy2(os.path.join(os.path.dirname(ROOT), "web", "viewer.html"), os.path.join(SITE, "index.html"))
    out = []
    copied = {}
    for pid, label, group, src, color, ex, tf in PARTS:
        path = os.path.join(ROOT, src)
        if not os.path.exists(path):
            print("missing", src)
            continue
        name = copied.get(src)
        if name is None:
            name = os.path.basename(os.path.dirname(src)) + "_" + os.path.basename(src)
            # ASCII STLs load slower; re-save every file as binary
            M = pod.mesh_to_manifold(pod.load_stl(path))
            pod.save_stl(M, os.path.join(MD, name))
            copied[src] = name
        out.append(dict(id=pid, label=label, group=group, file="models/" + name,
                        color=color, explode=ex, transform=tf))
    checks = json.load(open(os.path.join(pod.OUT, "checks.json")))["rows"]
    meta = dict(
        title="Bittle X Pi Add-on v0.7 on Platform v1.0",
        envelope=dict(width=2 * pod.W_HAUNCH, length=pod.ZR - pod.ZF, top=pod.H_MAIN,
                      above_cover=round(pod.H_MAIN - pod.COVER_TOP, 1)),
        bounds=dict(x=[-40, 40], z=[-70, 80], y=[-12, 70]),
        checks=[dict(a=a, b=b, v=round(v, 2)) for a, b, v in checks],
    )
    json.dump(dict(parts=out, meta=meta), open(os.path.join(SITE, "manifest.json"), "w"), indent=1)
    print("site ready:", len(out), "parts")


# --------------------------------------------------------------------------
# Home page: the two packages with their downloads, and a link to the viewer
# --------------------------------------------------------------------------
HOME = os.path.join(os.path.dirname(ROOT), "site")
PROJ = os.path.dirname(ROOT)
PACKAGES = [
    dict(key="platform", name="Bittle X Platform v1.0", dir="bittle_platform", zip="bittle_platform_v1.0.zip",
         pdf="bittle_platform_spec.pdf", img="doc/r2_starter.png",
         text="The stock Petoi Bittle X back cover with 4 pegs on its top. Add-ons drop onto the pegs, "
              "slide 7 mm rearward and click into place. No tools, glue or tape are necessary. "
              "The spec gives every number that you need to design an add-on.",
         extra=["interface.json"]),
    dict(key="addon", name="Bittle X Pi Add-on v0.7", dir="bittle_pi_addon", zip="bittle_pi_addon_v0.7.zip",
         pdf="bittle_pi_addon_guide.pdf", img="doc/01_assembly_iso.png", img2="doc/06_tray_loaded.png",
         text="A sample add-on for the platform: Raspberry Pi Zero 2 W, PiSugar 2 (1200 mAh), NS4168 amp with a 3 W speaker, "
              "and an SPH0645 mic. Three printed parts, all without supports.",
         extra=[]),
]


def esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def size(path):
    n = os.path.getsize(path)
    return f"{n / 1e6:.1f} MB" if n > 1e6 else f"{n / 1e3:.0f} kB"


def build_home():
    import shutil
    import datetime
    files = os.path.join(HOME, "files")
    shutil.rmtree(files, ignore_errors=True)
    cards = []
    for P in PACKAGES:
        src = os.path.join(PROJ, P["dir"])
        dst = os.path.join(files, P["key"])
        os.makedirs(dst, exist_ok=True)
        links = []

        def put(rel, label, cls=""):
            s_ = os.path.join(src, rel) if not rel.endswith(".zip") else os.path.join(PROJ, rel)
            name = os.path.basename(rel)
            shutil.copy2(s_, os.path.join(dst, name))
            links.append(f'<a class="dl {cls}" href="files/{P["key"]}/{name}" download><span>{esc(label)}</span>'
                         f'<small>{esc(name)} &middot; {size(s_)}</small></a>')
        put(P["pdf"], "Specification (PDF)" if P["key"] == "platform" else "Build guide (PDF)", "primary")
        put(P["zip"], "Full package (zip)", "primary")
        for f in sorted(os.listdir(os.path.join(src, "stl", "print"))):
            put(os.path.join("stl", "print", f), f"Print: {f[:-4]}")
        for f in sorted(os.listdir(os.path.join(src, "cad"))):
            put(os.path.join("cad", f), f"CAD: {f[:-5]}")
        for f in P["extra"]:
            put(f, f"Data: {f}")
        imgs = [P["img"]] + ([P["img2"]] if P.get("img2") else [])
        figs = ""
        for im in imgs:
            name = os.path.basename(im)
            shutil.copy2(os.path.join(src, im), os.path.join(dst, name))
            figs += f'<img src="files/{P["key"]}/{name}" alt="{esc(P["name"])}" loading="lazy">'
        cards.append(f'''<section class="card">
  <div class="figs">{figs}</div>
  <div class="body">
    <h2>{esc(P["name"])}</h2>
    <p>{esc(P["text"])}</p>
    <div class="links">{"".join(links)}</div>
  </div>
</section>''')
    html = PAGE.replace("{{CARDS}}", "\n".join(cards)).replace("{{DATE}}", datetime.date.today().isoformat())
    open(os.path.join(HOME, "index.html"), "w").write(html)
    print("home ready")


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bittle X Platform</title>
<style>
:root { --bg:#f6f5f2; --fg:#1d1d1f; --muted:#5f6368; --card:#ffffff; --line:#e3e1dc; --accent:#e8a317; --accent-fg:#1d1d1f; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg:#141416; --fg:#ececee; --muted:#a0a3a8; --card:#1e1f22; --line:#2f3035; --accent:#f2b632; --accent-fg:#141416; } }
:root[data-theme="dark"] { --bg:#141416; --fg:#ececee; --muted:#a0a3a8; --card:#1e1f22; --line:#2f3035; --accent:#f2b632; --accent-fg:#141416; }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--fg); font:16px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width:1040px; margin:0 auto; padding:32px 16px 48px; }
header h1 { margin:0 0 6px; font-size:clamp(1.6rem, 4vw, 2.2rem); letter-spacing:-0.01em; }
header p { margin:0 0 20px; color:var(--muted); max-width:62ch; }
.viewer { display:inline-flex; align-items:center; gap:8px; padding:10px 16px; border-radius:10px; background:var(--accent); color:var(--accent-fg); font-weight:600; text-decoration:none; margin-bottom:28px; }
.card { background:var(--card); border:1px solid var(--line); border-radius:14px; overflow:hidden; margin-bottom:24px; display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1.1fr); }
.figs { display:grid; gap:1px; background:var(--line); }
.figs img { width:100%; height:100%; object-fit:cover; display:block; background:#f7f7f7; min-height:180px; }
.body { padding:20px 22px; }
.body h2 { margin:0 0 8px; font-size:1.3rem; }
.body p { margin:0 0 16px; color:var(--muted); }
.links { display:grid; grid-template-columns:repeat(auto-fill, minmax(200px, 1fr)); gap:8px; }
.dl { display:flex; flex-direction:column; padding:9px 12px; border:1px solid var(--line); border-radius:9px; text-decoration:none; color:var(--fg); min-width:0; }
.dl:hover { border-color:var(--accent); }
.dl span { font-weight:600; font-size:0.93rem; }
.dl small { color:var(--muted); font-size:0.78rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.dl.primary { border-color:var(--accent); }
footer { color:var(--muted); font-size:0.85rem; margin-top:12px; }
@media (max-width:760px) { .card { grid-template-columns:1fr; } .figs img { max-height:260px; } }
</style>
</head>
<body>
<main>
<header>
  <h1>Bittle X Platform</h1>
  <p>A peg platform on the stock Petoi Bittle X back cover, and a Raspberry Pi add-on that clicks onto it. Download the documents, the print files and the CAD below.</p>
</header>
<a class="viewer" href="viewer/">Open the 3D viewer &rarr;</a>
{{CARDS}}
<footer>Updated {{DATE}}. The stock cover is a Petoi design; check the Petoi terms before you share it outside your group.</footer>
</main>
</body>
</html>
"""


if __name__ == "__main__":
    main()
    build_home()
