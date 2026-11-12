#!/usr/bin/env python3
"""Qeyam fixed-QR donation card generator.

Usage:
  python3 make_card.py --out card.png [--name "اسم المشروع"] [--sub "سطر وصفي"]
          [--logo qeyam-logo-mark.svg] [--fonts DIR_WITH_CAIRO_WOFF2]

The QR always encodes the fixed redirect URL below; it never changes.
"""
import argparse, html, os, re, shutil, subprocess, sys, tempfile

FIXED_URL = "https://abou010101-bot.github.io/donate/"
NAVY, GREEN, RED = "#253845", "#1A664B", "#DD3430"
TITLE = "تبرع للجمعية الكويتية لتعزيز القيم"


def qr_svg(url):
    import qrcode
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, border=0)
    qr.add_data(url)
    qr.make(fit=True)
    m = qr.get_matrix()
    n = len(m)
    d = "".join(f"M{x} {y}h1v1h-1z" for y, row in enumerate(m) for x, v in enumerate(row) if v)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n} {n}" '
            f'shape-rendering="crispEdges"><path fill="{NAVY}" d="{d}"/></svg>')


def rtl_text(t):
    """Escape text and isolate number/symbol runs (e.g. 10×1) so they keep left-to-right order."""
    t = html.escape(t)
    return re.sub(r"[0-9A-Za-z][0-9A-Za-z×*xX+\-/.%]*[0-9A-Za-z%]|[0-9]",
                  lambda m: f'<bdi dir="ltr">{m.group()}</bdi>', t)


def find_browser():
    for b in ("google-chrome", "chromium", "chromium-browser", "google-chrome-stable"):
        p = shutil.which(b)
        if p:
            return p
    sys.exit("No Chrome/Chromium found. Install one (e.g. apt-get install chromium) and retry.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--name", default="")
    ap.add_argument("--sub", default="")
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--logo", default=os.path.join(here, "qeyam-logo-mark.svg"))
    ap.add_argument("--fonts", default=os.path.join(here, "fonts"))
    a = ap.parse_args()

    logo = open(a.logo, encoding="utf-8").read()
    f700 = os.path.join(os.path.abspath(a.fonts), "cairo-arabic-700-normal.woff2")
    f800 = os.path.join(os.path.abspath(a.fonts), "cairo-arabic-800-normal.woff2")
    for f in (f700, f800):
        if not os.path.exists(f):
            sys.exit(f"Missing font {f}. Run: npm pack @fontsource/cairo@5 and extract package/files/ into {a.fonts}")

    name, sub = a.name.strip(), a.sub.strip()
    if name:
        size = 64 if len(name) <= 16 else (52 if len(name) <= 26 else 44)
        bottom = f'<div class="name" style="font-size:{size}px">{rtl_text(name)}</div>'
        if sub:
            bottom += f'<div class="sub">{rtl_text(sub)}</div>'
    else:
        bottom = '<div class="cta">امسح الرمز للتبرع</div>'

    page = f"""<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><style>
@font-face{{font-family:Cairo;font-weight:700;src:url("file://{f700}") format("woff2");}}
@font-face{{font-family:Cairo;font-weight:800;src:url("file://{f800}") format("woff2");}}
html,body{{margin:0;background:#fff;}}
.card{{width:1000px;height:1400px;box-sizing:border-box;position:relative;font-family:Cairo,sans-serif;color:{NAVY};
  display:flex;flex-direction:column;align-items:center;padding:56px 70px 0;}}
.card::before{{content:"";position:absolute;top:0;left:0;right:0;height:18px;background:{GREEN};}}
.logo{{height:170px;}} .logo svg{{height:100%;width:auto;display:block;}}
h1{{margin:18px 0 0;font-weight:800;font-size:50px;line-height:1.35;text-align:center;}}
.rule{{display:flex;gap:10px;align-items:center;margin:22px 0 30px;}}
.rule i{{display:block;height:6px;border-radius:3px;}}
.frame{{border:7px solid {GREEN};border-radius:36px;padding:34px;background:#fff;}}
.qr{{width:640px;height:640px;}} .qr svg{{width:100%;height:100%;display:block;}}
.bottom{{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;padding-bottom:40px;text-align:center;}}
.name{{font-weight:800;font-size:64px;line-height:1.3;}}
.sub{{font-weight:700;font-size:36px;line-height:1.4;color:{GREEN};margin-top:4px;}}
.cta{{font-weight:700;font-size:42px;color:{GREEN};}}
.foot{{position:absolute;bottom:0;left:0;right:0;height:18px;background:{NAVY};}}
.foot::after{{content:"";position:absolute;right:0;top:0;bottom:0;width:22%;background:{RED};}}
</style></head><body><div class="card">
<div class="logo">{logo}</div>
<h1>{TITLE}</h1>
<div class="rule"><i style="width:90px;background:{GREEN}"></i><i style="width:18px;background:{RED}"></i><i style="width:90px;background:{GREEN}"></i></div>
<div class="frame"><div class="qr">{qr_svg(FIXED_URL)}</div></div>
<div class="bottom">{bottom}</div>
<div class="foot"></div>
</div></body></html>"""

    tmp = tempfile.mkdtemp()
    hp = os.path.join(tmp, "card.html")
    open(hp, "w", encoding="utf-8").write(page)
    out = os.path.abspath(a.out)
    subprocess.run([find_browser(), "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                    "--allow-file-access-from-files", "--force-device-scale-factor=2",
                    "--window-size=1000,1400", f"--screenshot={out}", f"file://{hp}"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(out)


if __name__ == "__main__":
    main()
