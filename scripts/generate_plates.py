"""Genera las laminas anatomicas de linea (SVG) y el logo de Nando Muino.

Laminas (assets/img/plates/*.svg): columna, mano, rodilla, craneo, torax,
musculo (puncion seca), hombro (vendaje) y pelvis. Trazo uniforme, sin
sombreado, en tinta sepia; cada trazo lleva pathLength="1" para que el
dibujo con stroke-dashoffset sea uniforme desde CSS/GSAP. Las etiquetas van
en un grupo .lbl (aparecen despues del dibujo).

Logo (assets/img/logo/): rediseno del mark original (columna dentro de una
orbita eliptica) en version monolinea premium, con el wordmark convertido a
trazados desde Fraunces / Inter (fontTools) para que el SVG no dependa de
fuentes instaladas. Provisional hasta que el cliente apruebe.

Si existe index.html, inyecta cada lamina entre <!--PLATE:nombre--> y
<!--/PLATE:nombre--> (idempotente).
"""
import math
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
PLATES = os.path.join(ROOT, "assets", "img", "plates")
LOGO = os.path.join(ROOT, "assets", "img", "logo")
os.makedirs(PLATES, exist_ok=True)
os.makedirs(LOGO, exist_ok=True)

SEPIA = "#2B2622"
ARCILLA = "#B5674A"
OLIVA = "#6F7A5C"
HUESO = "#EFE9DF"


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def P(d, cls="ln", extra=""):
    return f'<path class="{cls}" d="{d}" pathLength="1"{extra}/>'


def catmull(points, closed=False):
    """Catmull-Rom -> cubic bezier path (points = [(x,y),...])."""
    pts = list(points)
    if len(pts) < 2:
        return ""
    d = f"M{f(pts[0][0])},{f(pts[0][1])}"
    n = len(pts)
    for i in range(n - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]
        p1 = pts[i]
        p2 = pts[i + 1]
        p3 = pts[i + 2] if i + 2 < n else pts[i + 1]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{f(c1[0])},{f(c1[1])} {f(c2[0])},{f(c2[1])} {f(p2[0])},{f(p2[1])}"
    return d + (" Z" if closed else "")


def sample_catmull(points, n=200):
    pts = list(points)
    out = []
    for i in range(len(pts) - 1):
        p0 = pts[i - 1] if i > 0 else pts[i]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[i + 2] if i + 2 < len(pts) else pts[i + 1]
        for k in range(n // (len(pts) - 1)):
            t = k / (n // (len(pts) - 1))
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(pts[-1])
    return out


def label(x, y, text, lx, ly, anchor="start"):
    """Etiqueta tipo lamina antigua: linea guia fina + texto mono."""
    return (f'<g class="lbl"><line x1="{f(lx)}" y1="{f(ly)}" x2="{f(x)}" y2="{f(y)}"/>'
            f'<circle cx="{f(lx)}" cy="{f(ly)}" r="1.8"/>'
            f'<text x="{f(x + (6 if anchor == "start" else -6))}" y="{f(y + 3)}" text-anchor="{anchor}">{text}</text></g>')


def svg(name, vb, body, title):
    w, h = vb
    return (f'<svg class="plate plate-{name}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{title}"><title>{title}</title>{body}</svg>')


def bone(x, y, L, ang, we, ws, flat_base=False):
    """Hueso largo: base en (x,y), apunta hacia arriba, rotado ang grados (horario)."""
    he, hs = we / 2, ws / 2
    k = min(L * 0.22, 14)
    d = (f"M{f(-he)},0 C{f(-he)},{f(-k * 0.4)} {f(-hs)},{f(-k)} {f(-hs)},{f(-k * 1.4)} "
         f"L{f(-hs)},{f(-(L - k * 1.4))} C{f(-hs)},{f(-(L - k))} {f(-he)},{f(-(L - k * 0.4))} {f(-he)},{f(-L)} "
         f"A{f(he)},{f(he * 0.6)} 0 0 1 {f(he)},{f(-L)} "
         f"C{f(he)},{f(-(L - k * 0.4))} {f(hs)},{f(-(L - k))} {f(hs)},{f(-(L - k * 1.4))} "
         f"L{f(hs)},{f(-k * 1.4)} C{f(hs)},{f(-k)} {f(he)},{f(-k * 0.4)} {f(he)},0 "
         f"A{f(he)},{f(he * 0.6)} 0 0 1 {f(-he)},0 Z")
    return f'<path class="ln" d="{d}" pathLength="1" transform="translate({f(x)} {f(y)}) rotate({f(ang)})"/>'


def tip(x, y, L, ang):
    return (x + L * math.sin(math.radians(ang)), y - L * math.cos(math.radians(ang)))


# ---------------------------------------------------------------- columna
def plate_columna():
    W, H = 420, 640
    ctrl = [(196, 30), (184, 70), (186, 108), (198, 150), (218, 210), (228, 270), (222, 330), (204, 390), (188, 440), (192, 490), (212, 540), (236, 600), (244, 630)]
    ctrl = [(x, y) for x, y in ctrl]  # (x,y)
    curve = sample_catmull(ctrl, 600)

    def at(y):
        best = min(curve, key=lambda p: abs(p[1] - y))
        i = curve.index(best)
        a, b = curve[max(0, i - 3)], curve[min(len(curve) - 1, i + 3)]
        ang = math.degrees(math.atan2(b[0] - a[0], b[1] - a[1]))  # desviacion respecto a vertical
        return best[0], ang

    segs = [("c", 7, 10.5, 15, 3.2), ("t", 12, 15.5, 23, 3.8), ("l", 5, 22, 31, 5)]
    y = 44
    out = []
    marks = {}
    idx = 0
    for kind, n, h, w, gap in segs:
        for i in range(n):
            if kind == "t":
                h_i = h + i * 0.45
                w_i = w + i * 0.5
            elif kind == "c":
                h_i, w_i = h + i * 0.3, w + i * 0.6
            else:
                h_i, w_i = h + i * 0.4, w + i * 0.4
            cy = y + h_i / 2
            cx, ang = at(cy)
            # cuerpo vertebral: rectangulo redondeado, cara anterior algo concava
            hw, hh, r = w_i / 2, h_i / 2, 2.4
            body = (f"M{f(-hw + r)},{f(-hh)} L{f(hw - r)},{f(-hh)} Q{f(hw)},{f(-hh)} {f(hw)},{f(-hh + r)} "
                    f"L{f(hw)},{f(hh - r)} Q{f(hw)},{f(hh)} {f(hw - r)},{f(hh)} L{f(-hw + r)},{f(hh)} "
                    f"Q{f(-hw)},{f(hh)} {f(-hw)},{f(hh - r)} Q{f(-hw + 1.5)},0 {f(-hw)},{f(-hh + r)} Q{f(-hw)},{f(-hh)} {f(-hw + r)},{f(-hh)} Z")
            # apofisis espinosa hacia posterior (derecha) y abajo
            if kind == "c":
                sl, sa = w_i * 0.75, 28
            elif kind == "t":
                sl, sa = w_i * 0.95, 48
            else:
                sl, sa = w_i * 0.7, 12
            dx, dy = sl * math.cos(math.radians(sa)), sl * math.sin(math.radians(sa))
            sp = (f"M{f(hw)},{f(-hh * 0.35)} L{f(hw + dx)},{f(dy - 1.5)} L{f(hw + dx + 1)},{f(dy + 2)} L{f(hw)},{f(hh * 0.45)}")
            g = f'<g transform="translate({f(cx)} {f(cy)}) rotate({f(-ang)})">{P(body)}{P(sp)}</g>'
            out.append(g)
            key = f"{kind}{i}"
            marks[key] = (cx, cy, hw, dx)
            y += h_i + gap
            idx += 1
    # sacro: cuna curvada, y coxis
    cx, ang = at(y + 30)
    sac = (f"M{f(cx - 16)},{f(y)} L{f(cx + 16)},{f(y)} C{f(cx + 30)},{f(y + 24)} {f(cx + 36)},{f(y + 46)} {f(cx + 34)},{f(y + 62)} "
           f"C{f(cx + 28)},{f(y + 66)} {f(cx + 22)},{f(y + 64)} {f(cx + 18)},{f(y + 60)} "
           f"C{f(cx + 8)},{f(y + 40)} {f(cx - 6)},{f(y + 22)} {f(cx - 16)},{f(y)} Z")
    out.append(P(sac))
    for i in range(3):
        cxx, cyy = cx + 22 + i * 4, y + 68 + i * 9
        out.append(P(f"M{f(cxx - 3)},{f(cyy)} a3,3 0 1 0 6,0 a3,3 0 1 0 -6,0"))
    marks["s"] = (cx, y + 30, 16, 20)
    lbls = ""
    c3 = marks["c3"]
    lbls += label(c3[0] + 92, c3[1], "Cervical", c3[0] + c3[2] + c3[3] + 4, c3[1] + 4)
    t5 = marks["t5"]
    lbls += label(t5[0] + 96, t5[1], "Dorsal", t5[0] + t5[2] + t5[3] + 4, t5[1] + 8)
    l2 = marks["l2"]
    lbls += label(l2[0] + 106, l2[1], "Lumbar", l2[0] + l2[2] + l2[3] + 4, l2[1] + 3)
    s = marks["s"]
    lbls += label(s[0] + 92, s[1] + 12, "Sacro", s[0] + 36, s[1] + 12)
    lbls += label(c3[0] - 56, 150, "Disco", marks["c6"][0] - marks["c6"][2] - 3, marks["c6"][1] + 8, anchor="end")
    body = '<g class="ink">' + "".join(out) + "</g>" + lbls
    return svg("columna", (W, H), body, "Columna vertebral, vista lateral")


# ---------------------------------------------------------------- mano
def plate_mano():
    W, H = 420, 560
    out = []
    # radio y cubito (extremos distales)
    out.append(P("M158,520 C160,506 172,498 186,498 L222,498 C232,498 236,506 236,514 L238,560 L156,560 Z"))
    out.append(P("M246,516 C246,506 254,500 262,502 L272,506 C278,508 280,514 280,520 L278,560 L246,560 Z"))
    # carpo
    carp = [(170, 490, 14, 10, -20), (203, 494, 14, 9, 5), (236, 492, 12, 9, 15), (250, 506, 7, 6, 0),
            (160, 460, 12, 10, -30), (188, 456, 11, 9, -10), (218, 455, 13, 11, 0), (247, 462, 12, 10, 20)]
    for cx, cy, rx, ry, rot in carp:
        out.append(P(f"M{f(cx - rx)},{f(cy)} a{rx},{ry} 0 1 0 {2 * rx},0 a{rx},{ry} 0 1 0 {-2 * rx},0", extra=f' transform="rotate({rot} {cx} {cy})"'))
    fingers = [
        # base x,y, mc len, ang, phalanges lens
        (152, 452, 92, -36, [56, 38]),
        (186, 446, 118, -7, [66, 40, 27]),
        (216, 444, 126, 0, [72, 45, 29]),
        (242, 448, 116, 6, [68, 42, 27]),
        (258, 456, 98, 13, [54, 32, 24]),
    ]
    tips = []
    for x, y, mcl, ang, ph in fingers:
        we, ws = (17, 10) if ang == -36 else (15, 8.5)
        out.append(bone(x, y, mcl, ang, we, ws))
        px, py = tip(x, y, mcl + 5, ang)
        for j, L in enumerate(ph):
            we_j, ws_j = [(14, 8.5), (12, 7.5), (10, 6.5)][j if len(ph) == 3 else j + 1]
            out.append(bone(px, py, L, ang, we_j, ws_j))
            px, py = tip(px, py, L + 4.5, ang)
        tips.append((px, py))
    lbls = ""
    lbls += label(322, 300, "Falanges", 268, 304)
    lbls += label(330, 410, "Metacarpo", 276, 404)
    lbls += label(330, 476, "Carpo", 262, 470)
    lbls += label(90, 540, "Radio", 156, 536, anchor="end")
    body = '<g class="ink">' + "".join(out) + "</g>" + lbls
    return svg("mano", (W, H), body, "Huesos de la mano, vista dorsal")


# ---------------------------------------------------------------- rodilla
def plate_rodilla():
    W, H = 420, 560
    out = []
    femur = ("M168,0 L162,236 C150,262 146,300 176,318 C196,330 204,316 210,314 C216,316 224,330 244,318 "
             "C274,300 270,262 250,236 L244,0")
    out.append(P(femur))
    out.append(P("M172,254 C172,226 228,226 228,254 C228,290 214,310 200,316 C186,310 172,290 172,254 Z"))
    tibia = ("M150,350 C150,342 262,342 262,350 L266,372 C266,382 254,394 250,412 L238,560 L174,560 L162,412 "
             "C158,394 146,382 146,372 Z")
    out.append(P(tibia))
    out.append(P("M268,374 C268,362 292,362 292,374 L296,402 L300,560 L282,560 L276,402 Z"))
    out.append(P("M164,342 C176,336 186,336 196,340", cls="ln ln-thin"))
    out.append(P("M216,340 C226,336 236,336 248,342", cls="ln ln-thin"))
    out.append(P("M194,316 C192,340 190,370 194,398", cls="ln ln-thin ln-dash"))
    out.append(P("M206,316 C208,340 210,370 206,398", cls="ln ln-thin ln-dash"))
    lbls = ""
    lbls += label(322, 120, "Fémur", 246, 124)
    lbls += label(322, 262, "Rótula", 230, 266)
    lbls += label(322, 340, "Menisco", 250, 340)
    lbls += label(96, 470, "Tibia", 170, 470, anchor="end")
    lbls += label(340, 470, "Peroné", 298, 470)
    body = '<g class="ink">' + "".join(out) + "</g>" + lbls
    return svg("rodilla", (W, H), body, "Articulación de la rodilla, vista anterior")


# ---------------------------------------------------------------- craneo
def plate_craneo():
    W, H = 480, 480
    out = []
    cranium = ("M118,214 C110,150 152,72 240,60 C342,50 422,122 418,216 C416,272 400,302 372,324 "
               "C358,336 342,340 330,334 C322,330 318,318 320,308")
    out.append(P(cranium))
    face = ("M118,214 C108,232 108,248 112,262 L100,300 C102,308 110,310 118,304 C124,330 130,352 142,364 "
            "L150,372 L240,364")
    out.append(P(face))
    # orbita, arco cigomatico, oido
    out.append(P("M150,206 C118,214 116,262 150,272 C170,276 178,250 172,232"))
    out.append(P("M160,270 C200,272 250,272 300,270 C318,270 328,282 326,296"))
    out.append(P("M318,300 a7,7 0 1 0 14,0 a7,7 0 1 0 -14,0"))
    # mandibula
    mand = ("M140,378 C154,392 176,402 204,398 L298,382 C316,378 326,362 328,342 L330,318 "
            "M298,382 C290,368 288,352 294,336")
    out.append(P(mand))
    # dientes
    for i in range(8):
        x = 150 + i * 11
        out.append(P(f"M{x},{364 - i * 0.3} L{x + 1},{374 - i * 0.3}", cls="ln ln-thin"))
        out.append(P(f"M{x + 3},{378 - i * 0.6} L{x + 2},{388 - i * 0.6}", cls="ln ln-thin"))
    # suturas
    out.append(P("M236,62 C232,120 226,170 222,216", cls="ln ln-thin ln-dash"))
    out.append(P("M150,184 C200,120 320,116 386,196", cls="ln ln-thin"))
    out.append(P("M372,324 C392,300 404,272 406,240", cls="ln ln-thin ln-dash"))
    lbls = ""
    lbls += label(60, 120, "Frontal", 150, 118, anchor="end")
    lbls += label(330, 40, "Parietal", 300, 62)
    lbls += label(436, 300, "Occipital", 400, 296)
    lbls += label(80, 420, "Mandíbula", 176, 400, anchor="end")
    lbls += label(246, 440, "Arco cigomático", 236, 272)
    body = '<g class="ink">' + "".join(out) + "</g>" + lbls
    return svg("craneo", (W, H), body, "Cráneo, vista lateral")


# ---------------------------------------------------------------- torax
def plate_torax():
    W, H = 460, 520
    out = []
    out.append(P("M215,88 C210,110 210,140 218,170 L222,290 C226,300 234,300 238,290 L242,170 C250,140 250,110 245,88 C236,80 224,80 215,88 Z"))
    out.append(P("M212,84 C170,70 130,72 96,60 C82,56 70,58 62,66", cls="ln"))
    out.append(P("M248,84 C290,70 330,72 364,60 C378,56 390,58 398,66", cls="ln"))
    for i in range(10):
        yl = 92 + i * 30
        ys = yl + 30 + i * 3
        spread = 84 + i * 10 - max(0, i - 6) * 14
        for sgn in (1, -1):
            xl = 230 + sgn * spread
            xs = 230 + sgn * 18
            d = (f"M{f(xl)},{f(yl)} C{f(xl + sgn * 6)},{f(yl + 30)} {f(xs + sgn * 40)},{f(ys - 10)} {f(xs)},{f(ys)} "
                 f"L{f(xs)},{f(ys + 8)} C{f(xs + sgn * 46)},{f(ys + 2)} {f(xl + sgn * 14)},{f(yl + 40)} {f(xl + sgn * 8)},{f(yl + 4)} Z")
            out.append(P(d))
    for sgn in (1, -1):
        out.append(P(f"M{f(230 + sgn * 74)},{f(400)} C{f(230 + sgn * 80)},{f(420)} {f(230 + sgn * 60)},{f(440)} {f(230 + sgn * 40)},{f(446)}", cls="ln ln-thin"))
        out.append(P(f"M{f(230 + sgn * 54)},{f(430)} C{f(230 + sgn * 56)},{f(444)} {f(230 + sgn * 44)},{f(456)} {f(230 + sgn * 34)},{f(458)}", cls="ln ln-thin"))
    out.append(P("M104,352 C150,286 310,286 356,352", cls="ln ln-dash"))
    lbls = ""
    lbls += label(400, 96, "Clavícula", 352, 66)
    lbls += label(232, 36, "Esternón", 230, 82)
    lbls += label(392, 260, "Costilla", 336, 250)
    lbls += label(392, 346, "Diafragma", 340, 336)
    body = '<g class="ink">' + "".join(out) + "</g>" + lbls
    return svg("torax", (W, H), body, "Caja torácica y diafragma, vista anterior")


# ---------------------------------------------------------------- musculo (puncion seca)
def plate_musculo():
    W, H = 460, 420
    out = []
    top = [(40, 236), (110, 214), (180, 156), (240, 142), (310, 150), (370, 166), (420, 160)]
    bot = [(40, 246), (110, 250), (180, 262), (240, 270), (310, 262), (370, 214), (420, 170)]
    d = catmull(top) + " L420,170 " + catmull(list(reversed(bot)))[1:] + " Z"
    out.append(P(d))
    ts, bs = sample_catmull(top, 120), sample_catmull(bot, 120)
    for k in range(1, 7):
        t = k / 7
        pts = []
        for i in range(0, len(ts), 4):
            j = min(i, len(bs) - 1)
            x = ts[i][0] * (1 - t) + bs[j][0] * t
            y = ts[i][1] * (1 - t) + bs[j][1] * t
            pts.append((x, y))
        pts = [p for p in pts if 62 < p[0] < 400]
        out.append(P(catmull(pts), cls="ln ln-thin"))
    out.append(P("M236,204 a16,14 0 1 0 32,0 a16,14 0 1 0 -32,0", cls="ln ln-thin ln-dash"))
    out.append(P("M252,204 a2,2 0 1 0 4,0 a2,2 0 1 0 -4,0"))
    out.append(P("M338,52 L254,196", cls="ln ln-thin"))
    out.append(P("M358,18 L338,52", cls="ln ln-thick"))
    lbls = ""
    lbls += label(158, 110, "Fibra muscular", 196, 186, anchor="end")
    lbls += label(120, 330, "Punto gatillo", 246, 220, anchor="end")
    lbls += label(392, 60, "Aguja", 344, 44)
    lbls += label(360, 330, "Tendón", 392, 196)
    body = '<g class="ink">' + "".join(out) + "</g>" + lbls
    return svg("musculo", (W, H), body, "Músculo con punto gatillo y aguja de punción seca")


# ---------------------------------------------------------------- hombro (vendaje)
def plate_hombro():
    W, H = 460, 460
    out = []
    # clavicula y acromion
    out.append(P("M56,124 C110,108 176,122 232,102 C244,98 254,98 262,102"))
    out.append(P("M256,96 C276,90 292,100 292,116 C292,128 282,134 268,132 L246,128"))
    # coracoides
    out.append(P("M240,128 C226,132 218,144 222,156", cls="ln ln-thin"))
    # humero: cabeza, tuberculos y diafisis
    out.append(P("M206,186 C206,140 248,118 282,132 C308,144 312,180 302,206"))
    out.append(P("M302,206 C314,216 310,238 298,244 L292,300 C290,360 288,400 286,440"))
    out.append(P("M206,186 C198,198 200,216 212,222 L214,300 C216,360 218,400 220,440"))
    out.append(P("M222,224 C226,212 232,210 240,214", cls="ln ln-thin"))
    # escapula: cavidad glenoidea y bordes
    out.append(P("M202,150 C190,172 190,204 204,226", cls="ln ln-thin"))
    out.append(P("M204,226 C190,254 166,292 130,330"))
    out.append(P("M234,124 C200,148 172,196 152,250 C144,278 138,306 130,330"))
    # contorno del deltoides (linea discontinua)
    out.append(P("M188,110 C246,96 322,122 332,176 C338,224 320,272 302,322", cls="ln ln-thin ln-dash"))
    # vendaje neuromuscular: dos tiras en Y desde la insercion del deltoides
    out.append('<path class="tape" d="M300,334 L238,120" pathLength="1"/>')
    out.append('<path class="tape" d="M300,334 L198,150" pathLength="1"/>')
    out.append(P("M296,334 a4,4 0 1 0 8,0 a4,4 0 1 0 -8,0", cls="ln ln-thin"))
    lbls = ""
    lbls += label(96, 70, "Clavícula", 140, 112, anchor="end")
    lbls += label(376, 96, "Acromion", 292, 108)
    lbls += label(370, 410, "Húmero", 290, 406)
    lbls += label(380, 250, "Vendaje", 282, 238)
    lbls += label(382, 180, "Deltoides", 334, 186)
    lbls += label(96, 396, "Escápula", 134, 324, anchor="end")
    body = '<g class="ink">' + "".join(out) + "</g>" + lbls
    return svg("hombro", (W, H), body, "Hombro con vendaje neuromuscular")


# ---------------------------------------------------------------- pelvis
def plate_pelvis():
    W, H = 480, 380
    out = []
    out.append(P("M212,92 C224,80 256,80 268,92 L262,204 C256,232 224,232 218,204 Z"))
    for r in range(4):
        y = 118 + r * 22
        for sgn in (1, -1):
            x = 240 + sgn * (12 - r * 1.5)
            out.append(P(f"M{f(x - 2.5)},{f(y)} a2.5,2.5 0 1 0 5,0 a2.5,2.5 0 1 0 -5,0", cls="ln ln-thin"))
    for sgn in (1, -1):
        def X(x):
            return f(240 + sgn * (x - 240))
        d = (f"M{X(270)},94 C{X(330)},52 {X(412)},70 {X(434)},122 C{X(448)},162 {X(420)},198 {X(386)},226 "
             f"C{X(374)},238 {X(368)},254 {X(374)},274 C{X(380)},302 {X(358)},332 {X(330)},338 "
             f"C{X(300)},344 {X(270)},334 {X(262)},318 L{X(262)},300 C{X(268)},296 {X(276)},294 {X(282)},294 "
             f"C{X(300)},280 {X(322)},264 {X(348)},262 C{X(360)},238 {X(346)},218 {X(324)},208 C{X(300)},198 {X(272)},204 {X(262)},214")
        out.append(P(d))
        ocx = 240 + sgn * 80
        out.append(P(f"M{f(ocx - 22)},304 a22,15 0 1 0 44,0 a22,15 0 1 0 -44,0", extra=f' transform="rotate({-22 * sgn} {f(ocx)} 304)"'))
        out.append(P(f"M{X(372)},246 C{X(392)},236 {X(412)},246 {X(418)},266 C{X(422)},284 {X(410)},300 {X(392)},304", cls="ln ln-thin ln-dash"))
    out.append(P("M236,318 L244,318 M236,326 L244,326", cls="ln ln-thin"))
    lbls = ""
    lbls += label(440, 70, "Ilion", 400, 78)
    lbls += label(300, 40, "Sacro", 246, 88)
    lbls += label(440, 300, "Cadera", 410, 286)
    lbls += label(150, 366, "Sínfisis", 236, 330, anchor="end")
    body = '<g class="ink">' + "".join(out) + "</g>" + lbls
    return svg("pelvis", (W, H), body, "Pelvis, vista anterior")


# ---------------------------------------------------------------- logo
def ellipse_arc(cx, cy, rx, ry, rot, a0, a1):
    """Arco de elipse rotada entre angulos a0..a1 (grados, parametricos)."""
    def pt(a):
        t = math.radians(a)
        x, y = rx * math.cos(t), ry * math.sin(t)
        r = math.radians(rot)
        return (cx + x * math.cos(r) - y * math.sin(r), cy + x * math.sin(r) + y * math.cos(r))
    x0, y0 = pt(a0)
    x1, y1 = pt(a1)
    large = 1 if (a1 - a0) % 360 > 180 else 0
    return f"M{f(x0)},{f(y0)} A{f(rx)},{f(ry)} {f(rot)} {large} 1 {f(x1)},{f(y1)}"


def mark_body(ink=SEPIA, accent=ARCILLA, sw=2.6):
    """Isotipo 120x120: columna monolinea dentro de una orbita eliptica."""
    parts = []
    cx, cy, rx, ry, rot = 60, 60, 52, 22, -34
    parts.append(f'<path d="{ellipse_arc(cx, cy, rx, ry, rot, 22, 300)}" fill="none" stroke="{ink}" stroke-width="{sw}" stroke-linecap="round"/>')
    parts.append(f'<path d="{ellipse_arc(cx, cy, rx, ry, rot, 312, 372)}" fill="none" stroke="{accent}" stroke-width="{sw}" stroke-linecap="round"/>')
    spine = [(62, 16), (55, 34), (60, 56), (67, 78), (60, 104)]
    curve = sample_catmull(spine, 160)
    n = 7
    for i in range(n):
        t = (i + 0.5) / n
        k = int(t * (len(curve) - 1))
        x, y = curve[k]
        a, b = curve[max(0, k - 3)], curve[min(len(curve) - 1, k + 3)]
        ang = math.degrees(math.atan2(b[0] - a[0], b[1] - a[1]))
        w = 6.2 + i * 1.35
        h = 4.2 + i * 0.9
        parts.append(f'<rect x="{f(-w / 2)}" y="{f(-h / 2)}" width="{f(w)}" height="{f(h)}" rx="{f(min(w, h) * 0.42)}" fill="{ink}" transform="translate({f(x)} {f(y)}) rotate({f(-ang)})"/>')
    return "".join(parts)


def text_paths(text, font_path, size, axes, tracking=0.0, italic_for=None):
    """Convierte texto en trazados SVG (fontTools). Devuelve (path_d, advance)."""
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    font = TTFont(font_path)
    font = instantiateVariableFont(font, axes)
    upem = font["head"].unitsPerEm
    scale = size / upem
    cmap = font.getBestCmap()
    gs = font.getGlyphSet()
    hmtx = font["hmtx"]
    kern = {}
    try:
        gpos = font["GPOS"].table
        for lookup in gpos.LookupList.Lookup:
            for st in lookup.SubTable:
                if st.LookupType != 2:
                    continue
                if st.Format == 1:
                    for gname, prs in zip(st.Coverage.glyphs, st.PairSet):
                        for pr in prs.PairValueRecord:
                            v = pr.Value1.XAdvance if pr.Value1 and hasattr(pr.Value1, "XAdvance") else 0
                            if v:
                                kern[(gname, pr.SecondGlyph)] = v
                elif st.Format == 2:
                    c1 = st.ClassDef1.classDefs
                    c2 = st.ClassDef2.classDefs
                    cov = set(st.Coverage.glyphs)
                    for g1 in cov:
                        k1 = c1.get(g1, 0)
                        rec1 = st.Class1Record[k1]
                        for g2, k2 in c2.items():
                            v = rec1.Class2Record[k2].Value1
                            adv = getattr(v, "XAdvance", 0) if v else 0
                            if adv:
                                kern[(g1, g2)] = adv
    except Exception:
        pass
    x = 0.0
    ds = []
    prev = None
    for ch in text:
        if ch == " ":
            x += hmtx["space"][0] * scale + tracking * size
            prev = None
            continue
        gname = cmap.get(ord(ch))
        if gname is None:
            continue
        if prev and (prev, gname) in kern:
            x += kern[(prev, gname)] * scale
        pen = SVGPathPen(gs)
        tpen = TransformPen(pen, (scale, 0, 0, -scale, x, 0))
        gs[gname].draw(tpen)
        d = pen.getCommands()
        if d:
            ds.append(d)
        x += hmtx[gname][0] * scale + tracking * size
        prev = gname
    return " ".join(ds), x


def build_logo():
    SP = os.environ.get("NM_FONTS") or os.path.join(os.environ.get("LOCALAPPDATA", ""), "Temp", "claude", "c--Users-alvar-Desktop-WEBS-NEGOCIOS", "186251b2-4b54-4848-98bb-e37dd0e14c95", "scratchpad", "fonts")
    fraunces = os.path.join(SP, "Fraunces[SOFT,WONK,opsz,wght].ttf")
    inter = os.path.join(SP, "Inter[opsz,wght].ttf")
    have_fonts = os.path.exists(fraunces) and os.path.exists(inter)
    variants = {"logo": (SEPIA, ARCILLA, OLIVA), "logo-claro": (HUESO, ARCILLA, "#B7BCA8")}
    for name, (ink, accent, sub) in variants.items():
        parts = []
        parts.append(f'<g transform="translate(0 0)">{mark_body(ink, accent)}</g>')
        if have_fonts:
            d1, w1 = text_paths("Nando Muiño", fraunces, 46, {"opsz": 72, "wght": 500, "SOFT": 0, "WONK": 0}, tracking=-0.005)
            d2, w2 = text_paths("FISIOTERAPIA · OSTEOPATÍA", inter, 11.2, {"opsz": 14, "wght": 500}, tracking=0.2)
            parts.append(f'<path fill="{ink}" transform="translate(134 66)" d="{d1}"/>')
            parts.append(f'<path fill="{sub}" transform="translate(136 92)" d="{d2}"/>')
            W = int(134 + max(w1, w2) + 8)
        else:
            parts.append(f'<text x="134" y="66" font-family="Fraunces, Georgia, serif" font-size="46" font-weight="500" fill="{ink}">Nando Muiño</text>')
            parts.append(f'<text x="136" y="92" font-family="Inter, Arial, sans-serif" font-size="11.2" letter-spacing="2.2" fill="{sub}">FISIOTERAPIA · OSTEOPATÍA</text>')
            W = 420
        svg_txt = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} 120" width="{W}" height="120" role="img" aria-label="Nando Muiño · Fisioterapia y Osteopatía">'
                   f'<title>Nando Muiño · Fisioterapia y Osteopatía</title>{"".join(parts)}</svg>')
        with open(os.path.join(LOGO, f"{name}.svg"), "w", encoding="utf-8") as fh:
            fh.write(svg_txt)
    for name, (ink, accent, bg) in {"mark": (SEPIA, ARCILLA, None), "mark-claro": (HUESO, ARCILLA, None), "icon": (SEPIA, ARCILLA, HUESO)}.items():
        bgr = f'<rect width="120" height="120" rx="26" fill="{bg}"/>' if bg else ""
        inner = mark_body(ink, accent, 3.0)
        if bg:
            inner = f'<g transform="translate(60 60) scale(0.82) translate(-60 -60)">{inner}</g>'
        svg_txt = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="120" height="120" role="img" aria-label="Nando Muiño">'
                   f'{bgr}{inner}</svg>')
        with open(os.path.join(LOGO, f"{name}.svg"), "w", encoding="utf-8") as fh:
            fh.write(svg_txt)
    return have_fonts


def inject(plates):
    idx = os.path.join(ROOT, "index.html")
    if not os.path.exists(idx):
        return False
    with open(idx, "r", encoding="utf-8") as fh:
        html = fh.read()
    for name, svg_txt in plates.items():
        pat = re.compile(rf"(<!--PLATE:{name}-->).*?(<!--/PLATE:{name}-->)", re.S)
        html, n = pat.subn(lambda m: m.group(1) + svg_txt + m.group(2), html)
        if n == 0:
            print("  (sin marcador para", name + ")")
    html = re.sub(r"(<!--MARK-->).*?(<!--/MARK-->)", lambda m: m.group(1) + mark_body("currentColor", ARCILLA, 3.0) + m.group(2), html, flags=re.S)
    with open(idx, "w", encoding="utf-8") as fh:
        fh.write(html)
    return True


if __name__ == "__main__":
    plates = {
        "columna": plate_columna(),
        "mano": plate_mano(),
        "rodilla": plate_rodilla(),
        "craneo": plate_craneo(),
        "torax": plate_torax(),
        "musculo": plate_musculo(),
        "hombro": plate_hombro(),
        "pelvis": plate_pelvis(),
    }
    for name, s in plates.items():
        with open(os.path.join(PLATES, f"{name}.svg"), "w", encoding="utf-8") as fh:
            fh.write(s)
        print(f"lamina {name}: {len(s)} bytes")
    print("logo con trazados de fuente:", build_logo())
    print("inyectado en index.html:", inject(plates))
