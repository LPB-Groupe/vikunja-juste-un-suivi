"""Applique l'habillage Juste un suivi à un code source Vikunja.

    python3 personnaliser.py <dossier-vikunja>

Chaque remplacement vérifie qu'il trouve exactement le texte attendu, le bon
nombre de fois, et arrête tout sinon : à une montée de version de Vikunja, un
fichier réécrit en amont fait échouer la construction au lieu de produire une
image à moitié habillée. On corrige alors l'ancre ici, et rien d'autre.

Deux mentions de Vikunja restent volontairement : « Propulsé par Vikunja »
(l'attribution due au projet, AGPL v3) et le nom du service dans
« Importer depuis Vikunja », qui désigne bien un export Vikunja.
"""
import re
import shutil
import sys
from pathlib import Path

ICI = Path(__file__).parent
VISUELS = ICI / "visuels"
NOM = "Juste un suivi"
# Dépôt public de cet habillage : c'est l'offre de code source que l'AGPL v3 (§13)
# exige envers les utilisateurs d'une version modifiée servie en ligne.
DEPOT = "https://github.com/LPB-Groupe/vikunja-juste-un-suivi"

# Vert #286355 de la charte, exprimé en TSL comme Vikunja définit sa couleur primaire.
# Thème sombre : même teinte, éclaircie pour rester lisible sur fond foncé tout en
# gardant un texte blanc lisible sur les boutons.
PRIMAIRE_CLAIR = ("166deg", "42%", "27%")
PRIMAIRE_SOMBRE = ("166deg", "42%", "40%")


def remplacer(racine: Path, fichier: str, ancien: str, nouveau: str, fois: int = 1) -> None:
    chemin = racine / fichier
    texte = chemin.read_text(encoding="utf-8")
    trouve = texte.count(ancien)
    if trouve != fois:
        sys.exit(f"✗ {fichier} : « {ancien[:70]} » trouvé {trouve} fois, {fois} attendu(s)")
    chemin.write_text(texte.replace(ancien, nouveau), encoding="utf-8")


def copier(racine: Path, source: str, destination: str) -> None:
    cible = racine / destination
    if not cible.exists():
        sys.exit(f"✗ {destination} n'existe plus dans Vikunja : vérifier où ce visuel a été déplacé")
    shutil.copyfile(VISUELS / source, cible)


def renommer_dans_traductions(racine: Path, fichier: str, garder: tuple[str, ...], minimum: int) -> None:
    """Remplace Vikunja par Juste un suivi dans les valeurs, sauf les clés à garder."""
    chemin = racine / fichier
    lignes, faits = [], 0
    for ligne in chemin.read_text(encoding="utf-8").splitlines(keepends=True):
        cle = re.match(r'\s*"([^"]+)"\s*:', ligne)
        if "Vikunja" in ligne and not (cle and cle.group(1) in garder):
            ligne = ligne.replace("Vikunja", NOM)
            faits += 1
        lignes.append(ligne)
    if faits < minimum:
        sys.exit(f"✗ {fichier} : {faits} mentions remplacées, au moins {minimum} attendues")
    chemin.write_text("".join(lignes), encoding="utf-8")
    print(f"  {fichier} : {faits} mentions")


def interface(r: Path) -> None:
    print("Interface")
    # Logo : le même fichier sert au logo habituel et à la variante de juin.
    copier(r, "logo-full.svg", "frontend/src/assets/logo-full.svg")
    copier(r, "logo-full.svg", "frontend/src/assets/logo-full-pride.svg")
    remplacer(r, "frontend/src/components/home/Logo.vue", 'alt="Vikunja"', f'alt="{NOM}"', fois=2)

    # Icônes et favicon, aux mêmes noms que ceux d'origine.
    for png in sorted((VISUELS / "icons").iterdir()):
        copier(r, f"icons/{png.name}", f"frontend/public/images/icons/{png.name}")
    copier(r, "favicon.ico", "frontend/public/favicon.ico")

    # Illustrations : photo de vigognes (connexion), lamas (fond, liste vide,
    # écran hors ligne) et logo de l'écran de chargement.
    for nom in ("no-auth-image.jpg", "llama-nightscape.jpg", "logo.svg", "llama-cool.svg", "llama.svg"):
        copier(r, f"illustrations/{nom}", f"frontend/src/assets/{nom}")

    # Titres : onglet du navigateur, application installée (PWA), page sans JavaScript.
    f = "frontend/index.html"
    remplacer(r, f, "<title>Vikunja</title>", f"<title>{NOM}</title>")
    remplacer(r, f, '<meta name="theme-color" content="#1973ff"/>', '<meta name="theme-color" content="#286355"/>')
    remplacer(r, f, "content=\"Vikunja (/vɪˈkuːnjə/) - The to-do app to organize your life.\"",
              "content=\"Juste un suivi - les actions décidées ne se perdent plus. Un service le Juste Cloud.\"")
    remplacer(r, f, '<html lang="en">', '<html lang="fr">')
    remplacer(r, f, "We're sorry but Vikunja doesn't work properly without JavaScript enabled. Please enable it to continue.",
              f"{NOM} a besoin de JavaScript pour fonctionner. Activez-le dans votre navigateur pour continuer.")
    f = "frontend/src/composables/useTitle.ts"
    remplacer(r, f, "? 'Vikunja'", f"? '{NOM}'")
    remplacer(r, f, "| Vikunja`", f"| {NOM}`")
    f = "frontend/vite.config.ts"
    # short_name d'abord : « name: 'Vikunja', » est aussi contenu dans short_name.
    remplacer(r, f, "short_name: 'Vikunja',", f"short_name: '{NOM}',")
    remplacer(r, f, "\t\t\t\t\tname: 'Vikunja',", f"\t\t\t\t\tname: '{NOM}',")
    remplacer(r, f, "theme_color: '#1973ff',", "theme_color: '#286355',")

    # Couleurs : primaire (boutons, liens, sélection) et texte du logo.
    f = "frontend/src/styles/custom-properties/colors.scss"
    remplacer(r, f, "  --primary-h: 217deg;\n  --primary-s: 98%;\n  --primary-l: 53%;",
              "  --primary-h: {};\n  --primary-s: {};\n  --primary-l: {};".format(*PRIMAIRE_CLAIR))
    remplacer(r, f, "      --primary-h: 217deg;\n      --primary-s: 98%;\n      --primary-l: 58%;",
              "      --primary-h: {};\n      --primary-s: {};\n      --primary-l: {};".format(*PRIMAIRE_SOMBRE))
    remplacer(r, f, "--logo-text-color: hsl(180, 1%, 15%);", "--logo-text-color: #286355;")

    # Typographie : Public Sans partout, titres comme texte courant.
    for police in ("PublicSans[wght].woff2", "PublicSans-Italic[wght].woff2"):
        shutil.copyfile(VISUELS / "fonts" / police, r / "frontend/src/assets/fonts" / police)
    f = "frontend/src/styles/fonts.scss"
    if "$unicode-range:" not in (r / f).read_text(encoding="utf-8"):
        sys.exit(f"✗ {f} : $unicode-range a disparu, les @font-face ajoutés en dépendent")
    with open(r / f, "a", encoding="utf-8") as sortie:
        sortie.write("""
@font-face {
  font-family: 'Public Sans';
  src: url($font-files-path + 'PublicSans[wght].woff2') format('woff2-variations');
  src: url($font-files-path + 'PublicSans[wght].woff2') format('woff2') tech('variations');
  font-weight: 100 900;
  font-display: swap;
  unicode-range: $unicode-range;
}

@font-face {
  font-family: 'Public Sans';
  src: url($font-files-path + 'PublicSans-Italic[wght].woff2') format('woff2-variations');
  src: url($font-files-path + 'PublicSans-Italic[wght].woff2') format('woff2') tech('variations');
  font-weight: 100 900;
  font-style: italic;
  font-display: swap;
  unicode-range: $unicode-range;
}
""")
    f = "frontend/src/styles/common-imports.scss"
    remplacer(r, f, "$family-sans-serif: 'Open Sans', Helvetica, Arial, sans-serif;",
              "$family-sans-serif: 'Public Sans', 'Inter', Arial, sans-serif;")
    remplacer(r, f, "$vikunja-font: 'Quicksand', sans-serif;",
              "$vikunja-font: 'Public Sans', 'Inter', Arial, sans-serif;")

    # « Propulsé par Vikunja », en bas du menu, mène au dépôt du correctif (qui
    # crédite et renvoie vers Vikunja) : attribution et offre de code source.
    remplacer(r, "frontend/src/urls.ts", "export const POWERED_BY = 'https://vikunja.io/?utm_source=powered_by'",
              f"export const POWERED_BY = '{DEPOT}?utm_source=powered_by'")
    remplacer(r, "frontend/src/i18n/lang/fr-FR.json", '"poweredBy": "Propulsé par Vikunja",',
              '"poweredBy": "Propulsé par Vikunja · code source",')
    remplacer(r, "frontend/src/i18n/lang/en.json", '"poweredBy": "Powered by Vikunja",',
              '"poweredBy": "Powered by Vikunja · source code",')

    garder = ("poweredBy", "vikunja")
    renommer_dans_traductions(r, "frontend/src/i18n/lang/fr-FR.json", garder, minimum=20)
    renommer_dans_traductions(r, "frontend/src/i18n/lang/en.json", garder, minimum=20)


def courriels(r: Path) -> None:
    print("Courriels")
    copier(r, "logo-mail.png", "pkg/notifications/logo.png")
    f = "pkg/notifications/mail_render.go"
    remplacer(r, f, 'style="height: 75px;" alt="Vikunja"/>', f'style="height: 75px;" alt="{NOM}"/>')
    remplacer(r, f, "font-family: 'Open Sans', sans-serif;", "font-family: 'Public Sans', Arial, Helvetica, sans-serif;")
    remplacer(r, f, "background-color: #1973ff;", "background-color: #286355;")
    remplacer(r, f, "color: #0969da;", "color: #286355;")
    # Le gabarit se dit compatible mode sombre mais ne définit aucune couleur
    # sombre : Apple Mail fonce alors la carte et garde le texte gris foncé,
    # illisible. Déclaré clair uniquement, il s'affiche tel que dessiné.
    remplacer(r, f, '<meta name="color-scheme" content="light dark">', '<meta name="color-scheme" content="light only">')
    remplacer(r, f, '<meta name="supported-color-schemes" content="light dark">',
              '<meta name="supported-color-schemes" content="light only">')
    remplacer(r, f, "        :root {\n            color-scheme: light dark;\n        }",
              "        :root {\n            color-scheme: light only;\n        }\n"
              "        a { color: #286355; }")
    # Nom d'expéditeur quand aucun n'est fourni, et nom affiché dans l'appli d'authentification (TOTP).
    remplacer(r, "pkg/mail/send_mail.go", 'opts.From = "Vikunja <"', f'opts.From = "{NOM} <"')
    remplacer(r, "pkg/user/totp.go", 'Issuer:      "Vikunja",', f'Issuer:      "{NOM}",')
    # Deux formats cassés dans la traduction française de Vikunja 2.3.0 : sans le
    # « s », Go affiche « %!\"(BADINDEX) » au lieu du nom de la tâche ou du nombre.
    f = "pkg/i18n/lang/fr-FR.json"
    remplacer(r, f, '"message_to_assignee": "%[1]s vous a assigné à \\"%[2]\\".",',
              '"message_to_assignee": "%[1]s vous a assigné la tâche « %[2]s ».",')
    remplacer(r, f, '"subject_to_assignee": "Vous avez été assigné à \\"%[1]s\\" (%[2]s)",',
              '"subject_to_assignee": "Nouvelle tâche pour vous : « %[1]s » (%[2]s)",')
    remplacer(r, f, '"since_weeks": "une semaine|%[1] semaines",', '"since_weeks": "une semaine|%[1]s semaines",')
    renommer_dans_traductions(r, "pkg/i18n/lang/fr-FR.json", (), minimum=20)
    renommer_dans_traductions(r, "pkg/i18n/lang/en.json", (), minimum=20)
    # Les traductions sont rangées sous « fr-FR », mais un compte réglé sur « fr »
    # (defaultsettings.language: fr, hérité par les comptes OIDC) ne les trouve pas
    # et reçoit ses courriels en anglais. Alias « fr » : même contenu, et déclaré
    # dans availableLanguages, sans quoi Init() ignore le fichier (cas de jus.2).
    shutil.copyfile(r / "pkg/i18n/lang/fr-FR.json", r / "pkg/i18n/lang/fr.json")
    remplacer(r, "pkg/i18n/i18n.go", '\t"fr-FR":    true,\n', '\t"fr-FR":    true,\n\t"fr":       true,\n')


def comptes(r: Path) -> None:
    """Seul ajout fonctionnel : créer d'avance le compte OIDC d'un responsable
    (code/jus_comptes.go), pour qu'une action puisse lui être assignée avant
    sa première connexion. Fermé tant que ses deux variables ne sont pas posées."""
    print("Comptes anticipés")
    shutil.copyfile(ICI / "code" / "jus_comptes.go", r / "pkg/routes/api/v1/jus_comptes.go")
    ancre = '\t\tur.POST("/auth/openid/:provider/callback", openid.HandleCallback)\n\t}\n'
    remplacer(r, "pkg/routes/routes.go", ancre,
              ancre + '\n\t// Juste un suivi : comptes OIDC créés d\'avance (secret requis).\n'
                      '\tur.PUT("/jus/comptes", apiv1.JusCreerCompte)\n')


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    racine = Path(sys.argv[1])
    interface(racine)
    courriels(racine)
    comptes(racine)
    print("✓ habillage appliqué")
