# Nando Muiño · Fisioterapia y Osteopatía · Carballo

Web para Nando Muiño · Fisioterapia y Osteopatía, consulta de fisioterapia y osteopatía en Rúa Vila de Ordes, 23, Carballo. La marca es el nombre de Nando, pero el cliente confirmó (2026-09-15) que trabaja un **equipo**: la voz de la web es plural y hay un bloque de equipo. Concepto **"Manos y anatomía"**: el osteópata como artesano del cuerpo. Taller, no clínica. Hueso, tinta sepia, arcilla y oliva; cero azul sanitario. Es la única plantilla de salud de la carpeta sin azul/teal y la única con nombre propio como marca.

Sitio estático sin build: `index.html` + `css/style.css` + `js/main.js`. GSAP 3.15 + ScrollTrigger y Lenis 1.3 desde CDN, tipografías Fraunces + Inter desde Google Fonts.

## Estructura (propia, no reutiliza el esqueleto de otras plantillas)

1. **Portada**: nombre enorme en Fraunces (opsz 144) con char-reveal lento, "Fisioterapia · Osteopatía" en itálica, línea small caps "Carballo · L–J 8:00–22:00", CTA "Pedir cita" en arcilla y magnético. A la derecha, la **Lámina I: columna vertebral** (SVG de línea generado) que se dibuja con `stroke-dashoffset` al cargar; las etiquetas de atlas aparecen al terminar. Sin canvas, sin shaders.
2. **Marquee** lento con las especialidades en itálica (empuje suave con la velocidad de scroll, nunca cambia de sentido).
3. **01 — Manifiesto**: "Escuchamos, *exploramos*, ajustamos." sticky a la izquierda con la Lámina II (mano) debajo, dibujándose con el scroll; a la derecha texto en primera persona del plural (placeholder marcado), tres principios, el bloque de equipo (Nando + Diego + Leticia, pendientes de confirmar) y dos fotos con parallax.
4. **02 — Osteopatía vs fisioterapia**: dos columnas (bloque sepia / bloque papel) con qué es cada una y "cuándo elegirla"; Lámina III (pelvis) en el margen.
5. **03 — Tratamientos**: sticky stack con la **lámina cambiando por tarjeta** (mano, columna, tórax/diafragma, cráneo, rodilla, músculo con aguja, hombro con vendaje). Cada lámina se redibuja al activarse; las tarjetas pasadas se atenúan. En móvil la figura queda sticky bajo la cabecera.
6. **04 — Cómo es una sesión**: timeline de 4 pasos con la línea trazándose con el scroll (horizontal en escritorio, vertical en móvil) y dos fotos.
7. **05 — Horario** (bloque sepia): "8:00 → 22:00" como titular con la flecha dibujándose, y una tabla-gráfica L–D con barras sobre un eje 6:00–24:00 que se pintan al entrar. Chip "abierto ahora" con hora de Europe/Madrid.
8. **06 — Reseñas**: tres reseñas reales de Google (capturas enviadas por el cliente el 2026-09-15) con apellidos abreviados a la inicial a petición suya (sin indicarlo en la web); contador animado 5,0 · 38 reseñas.
9. **07 — Contacto**: datos, mapa de Google por consentimiento (`.map-consent`, sin API key), IG/FB.

Papel con grano: `body::before` con un SVG `feTurbulence` en data URI (unos 400 bytes), fijo, `mix-blend-mode: multiply`, sin eventos.

## Datos reales usados

- Nombre, dirección (Rúa Vila de Ordes, 23, bajo, 15100 Carballo), teléfono 698 11 16 68, horario (L–J 8:00–22:00, V 8:00–14:00, S–D cerrado), Facebook e Instagram: facilitados por el cliente.
- Valoración de Google: **5,0 con 38 reseñas** (dato facilitado por el cliente el 2026-09-15), en la sección de reseñas, la línea de la portada, la meta description y el `aggregateRating` del schema.
- Email `nando.fisioterapianm@gmail.com`: aparece en la tarjeta/logo original que envió el cliente; en la web va marcado `[CONFIRMAR]`.

## Pendiente (placeholders marcados en la web con `.pendiente`)

- Texto del manifiesto (hay un borrador orientativo en plural marcado como tal).
- Lista definitiva de tratamientos (la actual son categorías genéricas del sector, marcada `[CONFIRMAR CON EL PROFESIONAL]`).
- Precio y duración de la sesión.
- Equipo: apellidos, titulaciones y nº de colegiado de cada profesional; confirmar que Diego y Leticia (nombrados en las reseñas) siguen en el equipo y si hay más personas.
- Nº de colegiado, titulación y colegio profesional; NIF y registro sanitario (aviso legal).
- Sistema de cita online, si lo hay.
- Foto real del equipo (el retrato actual es de ambiente y está marcado como provisional).
- Aprobación del logo rediseñado y de los colores de marca.

## Reseñas

Transcritas casi literalmente de las capturas: se quitaron emojis, el saludo inicial "Hola equipo" y la firma de la tercera, se corrigió la ortografía ("anticap" → "handicap", mayúsculas) y se abreviaron los apellidos a la inicial (José Manuel A., Irene F., Carmen G.). Las fechas relativas ("hace 4 meses", "hace un año") son las de las capturas.

## Logo

El cliente envió su logo (columna de puntos dentro de una órbita, teal/azul marino, con teléfono y dirección) y pidió mejorarlo. Se rediseñó en `scripts/generate_plates.py`: **misma idea** (columna dentro de una órbita elíptica) en monolínea, vértebras como rectángulos redondeados crecientes, un tramo de la órbita en arcilla como acento, y wordmark "Nando Muiño" en Fraunces 500 + "FISIOTERAPIA · OSTEOPATÍA" en Inter, convertidos a trazados con fontTools para que el SVG no dependa de fuentes. Archivos en `assets/img/logo/` (`logo.svg`, `logo-claro.svg`, `mark.svg`, `mark-claro.svg`, `icon.svg` + PNG 96/180/192/512). **Provisional hasta aprobación.**

## Láminas anatómicas

Generadas por `scripts/generate_plates.py` (Python, sin dependencias): columna (lateral, 24 vértebras + sacro), mano (dorsal), rodilla, cráneo, caja torácica con diafragma, músculo con punto gatillo y aguja, hombro con vendaje y pelvis. Trazo uniforme sin sombreado, `pathLength="1"` en cada trazo para que el dibujo sea uniforme, etiquetas finas tipo lámina antigua en un grupo `.lbl`. El script las escribe en `assets/img/plates/` y las inyecta inline en `index.html` entre `<!--PLATE:nombre-->` y `<!--/PLATE:nombre-->` (idempotente). También inyecta el isotipo en el `<symbol id="mark">`.

## Fotografía

El brief pedía fotografía generada; en este entorno no hay herramienta de generación de imagen, así que se usaron fotos con licencia Pexels (uso comercial libre) elegidas para el concepto y gradadas por script (`scripts/process_photos.py`): balance de blancos, supresión de azules/cian, saturación contenida, sombras viradas a sepia y luces a crema, grano fino. Ninguna es de la consulta real (a petición del cliente, la web ya no las etiqueta como "fotografía de ambiente"; solo el retrato lleva el aviso de provisional).

| Archivo | Pexels | Uso |
|---|---|---|
| retrato | #9222425 | manifiesto (retrato provisional) |
| espalda | #9268048 | manifiesto |
| cuello | #6188052 | osteopatía |
| hombro | #275768 | fisioterapia |
| valoracion | #5794010 | sesión |
| lumbar | #6560291 | sesión |
| sala | #5794027 | (procesada, sin usar en la página) |

## Accesibilidad y rendimiento

- `prefers-reduced-motion`: sin Lenis, láminas ya dibujadas y etiquetadas, textos visibles, marquee estático.
- Sin JS: `html.no-js` mantiene todo visible; el mapa muestra el placeholder y el enlace "Cómo llegar".
- Los textos con char-reveal conservan el texto íntegro en `aria-label`.
- No hay canvas ni filtros por frame; solo transforms y `stroke-dashoffset`.
- Cookies: solo `localStorage` (`nm-cookie-ack`); el mapa de Google se carga únicamente al pulsar. `.cookie-banner[hidden]{display:none}` para que el botón funcione.

## Verificación

`node scripts/verify.js` (Playwright, servidor local en `http://127.0.0.1:8931/`, p. ej. `python -m http.server 8931`). Última ejecución (2026-09-15): todo OK: 0 errores JS, 0 longtasks >50 ms durante la intro y el scroll completo (solo el parse inicial antes de `load`, ~110 ms), lámina de portada 52/52 trazos, cookies, mapa por consentimiento, sticky stack cambiando de lámina, horario y timeline, reduced-motion, sin JS, menú móvil, sin scroll horizontal a 1440/400/360 px. Informe en `scripts/verify-report.json`, capturas en `screenshots/`.

## Scripts

- `scripts/generate_plates.py`: láminas + logo + inyección en `index.html`. Necesita las fuentes variables Fraunces e Inter (ruta por variable de entorno `NM_FONTS`; si no están, el logo usa `<text>`).
- `scripts/process_photos.py`: descarga y gradación de fotos → `assets/img/photos/`.
- `scripts/generate_icons.js`: iconos PNG e imagen OG desde el SVG del logo.
- `scripts/verify.js`: verificación Playwright.
