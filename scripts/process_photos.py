"""Descarga y grada la fotografia de ambiente de la web de Nando Muino.

Procedencia: el brief pedia "fotografia generada", pero en este entorno no
hay herramienta de generacion de imagen, asi que se usan fotos con licencia
Pexels (uso comercial libre, sin atribucion obligatoria), elegidas para el
concepto "manos y anatomia / taller, no clinica": manos sobre espalda,
cuello y hombro, camilla de madera, luz de ventana, nada de batas ni
aparatos. Ninguna es una foto real de Nando Muino ni de su consulta; la web
las etiqueta como "fotografia de ambiente" y el retrato como provisional.

  retrato     Pexels #9222425  perfil masculino a contraluz calido, pared de madera
  espalda     Pexels #9268048  manos del terapeuta sobre la espalda, luz calida
  cuello      Pexels #6188052  mano sobre cuello y hombro, claroscuro
  hombro      Pexels #275768   manos trabajando el hombro
  valoracion  Pexels #5794010  terapeuta con camisa de lino, camilla de madera
  lumbar      Pexels #6560291  manos sobre la zona lumbar, sabana cruda
  sala        Pexels #5794027  sala con camilla de madera y luz de ventana

Gradacion comun (script, no presets): altas luces viradas a crema (#F3EBDD),
sombras viradas a sepia (#2B2622), supresion de azules/cian (nada de blanco
clinico ni de luz fria), saturacion contenida y grano fino. Se generan
variantes 1600 / 900 / lqip desde el mismo master.
"""
import os
import urllib.request
import concurrent.futures
import numpy as np
from PIL import Image, ImageFilter, ImageOps

PHOTOS = {
    "retrato": "9222425",
    "espalda": "9268048",
    "cuello": "6188052",
    "hombro": "275768",
    "valoracion": "5794010",
    "lumbar": "6560291",
    "sala": "5794027",
}
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "photos_src")
OUT = os.path.join(HERE, "..", "assets", "img", "photos")
os.makedirs(SRC, exist_ok=True)
os.makedirs(OUT, exist_ok=True)

SEPIA = np.array([0x2B, 0x26, 0x22]) / 255.0
CREMA = np.array([0xF3, 0xEB, 0xDD]) / 255.0
ARCILLA = np.array([0xB5, 0x67, 0x4A]) / 255.0


def rgb_to_hsv_h(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx = a.max(-1)
    mn = a.min(-1)
    d = mx - mn + 1e-6
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) / 6.0
    s = d / (mx + 1e-6)
    return h, s


def grade(im: Image.Image) -> Image.Image:
    a = np.asarray(im.convert("RGB")).astype(np.float32) / 255.0
    # 1. balance de blancos "gray world" suave
    mean = a.reshape(-1, 3).mean(0)
    a = np.clip(a * (mean.mean() / mean) ** 0.5, 0, 1)
    # 2. supresion de azules / cian (sin blanco clinico ni luz fria)
    h, s = rgb_to_hsv_h(a)
    cold = np.exp(-((h - 0.58) ** 2) / (2 * 0.07 ** 2)) * np.clip(s * 2.2, 0, 1)
    lum = a @ np.array([0.299, 0.587, 0.114])
    a = a * (1 - cold[..., None] * 0.55) + lum[..., None] * cold[..., None] * 0.55
    # 3. saturacion contenida
    lum = a @ np.array([0.299, 0.587, 0.114])
    a = lum[..., None] + (a - lum[..., None]) * 0.78
    # 4. split-toning: sombras sepia, luces crema, medios un toque arcilla
    sh = np.clip(1.0 - lum, 0, 1)[..., None] ** 1.7
    hi = np.clip(lum - 0.55, 0, 1)[..., None] * 2.0
    mid = (1 - sh) * (1 - hi)
    a = a + (SEPIA - 0.5) * 0.34 * sh
    a = a + (CREMA - 0.5) * 0.36 * hi
    a = a + (ARCILLA - 0.5) * 0.06 * mid
    # 5. curva suave: negros levantados, luces contenidas (sin blancos puros)
    a = 0.035 + a * 0.93
    a = np.clip(a, 0, 1)
    a = a ** 0.96
    # 6. grano fino
    rng = np.random.default_rng(7)
    a = np.clip(a + rng.normal(0, 0.012, a.shape[:2])[..., None], 0, 1)
    return Image.fromarray((a * 255).astype(np.uint8))


def fetch(pid, w):
    url = f"https://images.pexels.com/photos/{pid}/pexels-photo-{pid}.jpeg?auto=compress&cs=tinysrgb&w={w}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=240) as r:
        return r.read()


def process(name):
    pid = PHOTOS[name]
    src = os.path.join(SRC, f"{name}-{pid}.jpg")
    if not os.path.exists(src):
        with open(src, "wb") as f:
            f.write(fetch(pid, 2000))
    im = ImageOps.exif_transpose(Image.open(src))
    im = grade(im)
    for w in (1600, 900):
        r = im.copy()
        r.thumbnail((w, w * 3), Image.LANCZOS)
        r.save(os.path.join(OUT, f"{name}-{w}.jpg"), quality=82, optimize=True, progressive=True)
    tiny = im.copy()
    tiny.thumbnail((32, 96), Image.LANCZOS)
    tiny.filter(ImageFilter.GaussianBlur(1.5)).save(os.path.join(OUT, f"{name}-lqip.jpg"), quality=45)
    return name, im.size


if __name__ == "__main__":
    with concurrent.futures.ThreadPoolExecutor(3) as ex:
        for r in ex.map(process, list(PHOTOS)):
            print(r)
