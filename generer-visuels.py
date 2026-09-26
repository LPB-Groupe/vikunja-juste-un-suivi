"""Génère les visuels Juste un suivi déposés dans le code de Vikunja.

Sortie dans visuels/ (versionné) : on ne relance ce script que si la charte ou
le logo changent. Le texte des logos est vectorisé depuis Public Sans, pour
qu'aucun rendu ne dépende d'une police installée.

    pip install fonttools cairosvg pillow
    python3 generer-visuels.py
"""
from io import BytesIO
from pathlib import Path

import cairosvg
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import Image

ICI = Path(__file__).parent
POLICES = ICI / "sources" / "polices"
SORTIE = ICI / "visuels"

VERT, JAUNE, NOIR, BLANC = "#286355", "#ffc325", "#272727", "#ffffff"


def _police(fichier: str) -> TTFont:
    f = TTFont(POLICES / fichier)
    return instantiateVariableFont(f, {"wght": 700}) if "fvar" in f else f


GRAS = _police("PublicSans[wght].ttf")
ITALIQUE = _police("PublicSans-Italic[wght].ttf")


def texte(txt: str, police: TTFont, taille: float, x: float, ligne: float):
    gs, cmap, hmtx = police.getGlyphSet(), police.getBestCmap(), police["hmtx"]
    k = taille / police["head"].unitsPerEm
    pen, cx = SVGPathPen(gs), x
    for ch in txt:
        nom = cmap[ord(ch)]
        gs[nom].draw(TransformPen(pen, (k, 0, 0, -k, cx, ligne)))
        cx += hmtx[nom][0] * k
    return pen.getCommands(), cx


def pictogramme(x=0.0, y=0.0, taille=100.0, arrondi=0.22, marge=0.14, fond=VERT, trait=BLANC):
    """Liste cochée (tracés Lucide « list-checks ») sur un carré, arrondi ou non."""
    k = taille * (1 - 2 * marge) / 24
    return (
        f'<rect x="{x}" y="{y}" width="{taille}" height="{taille}" rx="{taille * arrondi:.1f}" fill="{fond}"/>'
        f'<g transform="translate({x + taille * marge:.2f} {y + taille * marge:.2f}) scale({k:.4f})" '
        f'fill="none" stroke="{trait}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="m3 17 2 2 4-4"/><path d="m3 7 2 2 4-4"/>'
        '<path d="M13 6h8"/><path d="M13 12h8"/><path d="M13 18h8"/></g>'
    )


def logo(couleur_haut: str) -> str:
    haut, w1 = texte("juste un", GRAS, 58, 124, 46)
    bas, w2 = texte("suivi", ITALIQUE, 58, 124, 100)
    largeur = round(max(w1, w2) + 8)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -4 {largeur} 112" '
        f'width="{largeur}" height="112" role="img"><title>Juste un suivi</title>'
        f'{pictogramme(0, 2)}<path fill="{couleur_haut}" d="{haut}"/>'
        f'<path fill="{JAUNE}" d="{bas}"/></svg>'
    )


def barres(largeur: float, hauteur: float) -> str:
    """Barres verticales de la charte, en filigrane (fond de la page de connexion)."""
    pas, epaisseur = largeur / 5, largeur / 12
    rects = "".join(
        f'<rect x="{pas * (i + 0.6):.1f}" y="{hauteur * (0.35 + 0.1 * i):.1f}" width="{epaisseur:.1f}" '
        f'height="{hauteur:.1f}" rx="{epaisseur / 2:.1f}"/>' for i in range(4))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{largeur}" height="{hauteur}" '
            f'viewBox="0 0 {largeur} {hauteur}"><g fill="{VERT}" opacity=".18">{rects}</g></svg>')


def fond_marque(l: int, h: int) -> str:
    """Panneau vert de la charte : découpe diagonale, barres jaunes, pictogramme en filigrane.

    Vikunja cadre l'image par le bas (bottom/cover) : le tiers haut est souvent
    rogné, d'où les barres placées sous ce tiers."""
    u = min(l, h) / 100
    barres_jaunes = "".join(
        f'<rect x="{(8 + i * 5) * u:.1f}" y="{h * 0.36:.1f}" width="{2.2 * u:.1f}" height="{14 * u:.1f}" '
        f'rx="{1.1 * u:.1f}" fill="{JAUNE}"/>' for i in range(4))
    filigrane = pictogramme(l - 70 * u, 18 * u, 60 * u, fond="none", trait="#ffffff")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {l} {h}">'
        f'<rect width="{l}" height="{h}" fill="{VERT}"/>'
        f'<polygon points="0,{h * 0.62} {l},{h * 0.38} {l},{h} 0,{h}" fill="#1f4f44"/>'
        f'<g opacity=".10">{filigrane}</g>{barres_jaunes}</svg>'
    )


def carre(svg_interne: str, vue=100) -> str:
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vue} {vue}">{svg_interne}</svg>'


def png(svg: str, chemin: Path, largeur=None, hauteur=None, mode=None):
    data = cairosvg.svg2png(bytestring=svg.encode(), output_width=largeur, output_height=hauteur)
    im = Image.open(BytesIO(data))
    if mode:
        im = im.convert(mode)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    im.save(chemin, optimize=True)
    return im


def main():
    icones = SORTIE / "icons"
    icones.mkdir(parents=True, exist_ok=True)

    # Logo de l'interface : « juste un » suit la couleur du thème (currentColor,
    # réglée par --logo-text-color), « suivi » reste jaune dans les deux thèmes.
    (SORTIE / "logo-full.svg").write_text(logo("currentColor"))
    # Logo des courriels : affiché à 75 px de haut, fourni en 150 pour les écrans denses.
    png(logo(VERT), SORTIE / "logo-mail.png", hauteur=150)

    arrondi = carre(pictogramme())                                   # favicon, onglets
    plein = carre(pictogramme(arrondi=0))                            # iOS et Android arrondissent eux-mêmes
    masquable = carre(pictogramme(marge=0.26, arrondi=0))            # zone sûre des icônes masquables (80 %)

    for nom, svg, cote in [
        ("favicon-16x16.png", arrondi, 16), ("favicon-32x32.png", arrondi, 32),
        ("apple-touch-icon.png", plein, 180), ("apple-touch-icon-180x180.png", plein, 180),
        ("apple-touch-icon-152x152.png", plein, 152), ("apple-touch-icon-120x120.png", plein, 120),
        ("apple-touch-icon-76x76.png", plein, 76), ("apple-touch-icon-60x60.png", plein, 60),
        ("android-chrome-192x192.png", plein, 192), ("android-chrome-512x512.png", plein, 512),
        ("icon-maskable.png", masquable, 1024),
        ("msapplication-icon-144x144.png", plein, 144), ("mstile-150x150.png", plein, 270),
    ]:
        png(svg, icones / nom, largeur=cote)

    # Badge des notifications Android : silhouette blanche sur fond transparent.
    badge = carre(pictogramme(fond="none", marge=0.08))
    png(badge, icones / "badge-monochrome.png", largeur=128)
    # Onglet épinglé Safari : forme unie, Safari applique lui-même la couleur.
    (icones / "safari-pinned-tab.svg").write_text(carre(pictogramme(fond="none", trait="#000000", marge=0.08)))

    grand = png(arrondi, SORTIE / "_favicon-256.png", largeur=256, mode="RGBA")
    grand.save(SORTIE / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
    (SORTIE / "_favicon-256.png").unlink()

    # Illustrations de Vikunja remplacées par des motifs de la charte.
    fonds = SORTIE / "illustrations"
    fonds.mkdir(exist_ok=True)
    for nom, (l, h) in {"no-auth-image.jpg": (900, 1184), "llama-nightscape.jpg": (1920, 1920)}.items():
        png(fond_marque(l, h), fonds / nom, largeur=l, mode="RGB")
    (fonds / "logo.svg").write_text(carre(pictogramme()).replace("<svg ", '<svg width="256" height="256" ', 1))
    (fonds / "llama-cool.svg").write_text(carre(pictogramme()).replace("<svg ", '<svg width="160" height="160" ', 1))
    (fonds / "llama.svg").write_text(barres(145, 204))

    # Public Sans pour toute l'interface, réduite au latin comme les polices d'origine.
    from fontTools import subset
    for src, dst in [("PublicSans[wght].ttf", "PublicSans[wght].woff2"),
                     ("PublicSans-Italic[wght].ttf", "PublicSans-Italic[wght].woff2")]:
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.layout_features = ["*"]
        f = TTFont(POLICES / src)
        s = subset.Subsetter(opts)
        s.populate(unicodes=subset.parse_unicodes(
            "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,"
            "U+2000-206F,U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"))
        s.subset(f)
        (SORTIE / "fonts").mkdir(exist_ok=True)
        f.flavor = "woff2"
        f.save(SORTIE / "fonts" / dst)
    print("visuels générés dans", SORTIE)


if __name__ == "__main__":
    main()
