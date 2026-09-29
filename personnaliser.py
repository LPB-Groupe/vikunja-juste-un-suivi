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
import json
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
              '"poweredBy": "Propulsé par Vikunja (code source)",')
    remplacer(r, "frontend/src/i18n/lang/en.json", '"poweredBy": "Powered by Vikunja",',
              '"poweredBy": "Powered by Vikunja (source code)",')

    garder = ("poweredBy", "vikunja")
    renommer_dans_traductions(r, "frontend/src/i18n/lang/fr-FR.json", garder, minimum=20)
    renommer_dans_traductions(r, "frontend/src/i18n/lang/en.json", garder, minimum=20)


# Signature commune à tous les courriels de Vikunja, alignée sur le pied des
# récapitulatifs n8n (W1, W2). Les courriels partent de l'adresse du support :
# y répondre le joint bien.
SIGNATURE = (f"Message automatique de {NOM}, un service le Juste Cloud. "
             "Une question ? Répondez à ce courriel, il parvient au support du Juste Cloud.")

# Formats Go : « %[1]s », « %[2]d »... Un « %[1] » sans lettre est cassé (Go
# affiche « %!(BADINDEX) ») ; un « %[1]s » sur un nombre affiche « %!s(int64=3) ».
FORMAT = re.compile(r"%(?:\[(\d+)\])?([a-zA-Z]?)")
# Clé où la version anglaise de Vikunja 2.3.0 est elle-même fausse : elle attend
# %[2]s alors que le code ne passe qu'un argument (l'erreur). Le français, juste,
# ne peut donc pas lui ressembler.
FORMATS_ANGLAIS_FAUX = {"notifications.migration.failed.error"}
INTERDITS = {"\u2014": "tiret cadratin", "\u2013": "tiret demi-cadratin", "\u00b7": "point médian"}


def formats(texte: str) -> list[tuple[str, str]]:
    return sorted({(m.group(1) or "1", m.group(2)) for m in FORMAT.finditer(texte)})


def aplatir(donnees: dict, prefixe: str = "") -> dict[str, str]:
    plat = {}
    for cle, valeur in donnees.items():
        complete = f"{prefixe}.{cle}" if prefixe else cle
        if isinstance(valeur, dict):
            plat.update(aplatir(valeur, complete))
        else:
            plat[complete] = valeur
    return plat


def traduire_courriels(r: Path) -> None:
    """Pose nos textes français (traductions/courriels-fr.json) dans la traduction
    fr-FR de Vikunja, après trois contrôles qui arrêtent la construction :
    - chaque clé que le code Go demande existe chez nous (une clé ajoutée en amont
      et non traduite partirait en anglais) ;
    - chaque clé de chez nous existe en anglais (une clé renommée en amont) ;
    - chaque format %[n]x correspond à l'anglais (une faute fait afficher
      « %!s(BADINDEX) » dans le courriel)."""
    nos = json.loads((ICI / "traductions" / "courriels-fr.json").read_text(encoding="utf-8"))
    anglais = aplatir(json.loads((r / "pkg/i18n/lang/en.json").read_text(encoding="utf-8")))

    utilisees = set()
    for go in (r / "pkg").rglob("*.go"):
        if go.name.endswith("_test.go"):
            continue
        utilisees |= set(re.findall(r'i18n\.TP?\(\s*\w+\s*,\s*"([^"]+)"', go.read_text(encoding="utf-8")))
    utilisees |= {k for k in anglais if k.startswith("time.")}  # clés passées par variable (durées)

    manquantes = sorted(utilisees - nos.keys())
    if manquantes:
        sys.exit("✗ clés de courriel sans traduction française : " + ", ".join(manquantes))
    inconnues = sorted(nos.keys() - anglais.keys())
    if inconnues:
        sys.exit("✗ clés traduites qui n'existent plus dans Vikunja : " + ", ".join(inconnues))
    for cle, texte in nos.items():
        if cle not in FORMATS_ANGLAIS_FAUX and formats(texte) != formats(anglais[cle]):
            sys.exit(f"✗ {cle} : formats {formats(texte)} au lieu de {formats(anglais[cle])} (anglais)")
        if any(verbe == "" for _, verbe in formats(texte)):
            sys.exit(f"✗ {cle} : format sans lettre, Go afficherait %!(BADINDEX)")
        if "Vikunja" in texte:
            sys.exit(f"✗ {cle} : « Vikunja » ne doit pas apparaître dans un courriel")
        for car, nom in INTERDITS.items():
            if car in texte:
                sys.exit(f"✗ {cle} : {nom} interdit")

    f = r / "pkg/i18n/lang/fr-FR.json"
    francais = json.loads(f.read_text(encoding="utf-8"))
    for cle, texte in nos.items():
        noeud = francais
        *parents, feuille = cle.split(".")
        for p in parents:
            noeud = noeud.setdefault(p, {})
        noeud[feuille] = texte
    restes = [k for k, v in aplatir(francais).items() if "Vikunja" in v]
    if restes:
        sys.exit("✗ fr-FR.json garde « Vikunja » dans : " + ", ".join(restes))
    f.write_text(json.dumps(francais, ensure_ascii=False, indent="\t") + "\n", encoding="utf-8")
    print(f"  pkg/i18n/lang/fr-FR.json : {len(nos)} textes, {len(utilisees)} clés utilisées, toutes traduites")


def courriels(r: Path) -> None:
    print("Courriels")
    copier(r, "logo-mail.png", "pkg/notifications/logo.png")
    f = "pkg/notifications/mail_render.go"
    remplacer(r, f, 'style="height: 75px;" alt="Vikunja"/>', f'style="height: 75px;" alt="{NOM}"/>')
    remplacer(r, f, "font-family: 'Open Sans', sans-serif;", "font-family: 'Public Sans', Arial, Helvetica, sans-serif;")
    remplacer(r, f, "background-color: #1973ff;", "background-color: #286355;")
    remplacer(r, f, "color: #0969da;", "color: #286355;")
    # Boutons en casse normale, comme ceux des récapitulatifs n8n.
    remplacer(r, f, "Text-transform: uppercase;", "")
    # Le gabarit se dit compatible mode sombre mais ne définit aucune couleur
    # sombre : Apple Mail fonce alors la carte et garde le texte gris foncé,
    # illisible. Déclaré clair uniquement, il s'affiche tel que dessiné.
    remplacer(r, f, '<meta name="color-scheme" content="light dark">', '<meta name="color-scheme" content="light only">')
    remplacer(r, f, '<meta name="supported-color-schemes" content="light dark">',
              '<meta name="supported-color-schemes" content="light only">')
    remplacer(r, f, "        :root {\n            color-scheme: light dark;\n        }",
              "        :root {\n            color-scheme: light only;\n        }\n"
              "        a { color: #286355; }")
    # Gabarit « conversation » (commentaires, mentions) : même règle du thème clair,
    # et liens verts (le nettoyage HTML retire le style posé sur les liens).
    remplacer(r, f, '    <meta charset="utf-8">\n</head>',
              '    <meta charset="utf-8">\n    <meta name="color-scheme" content="light only">\n'
              '    <meta name="supported-color-schemes" content="light only">\n'
              '    <style>:root { color-scheme: light only; } a { color: #286355; }</style>\n</head>')
    # Signature sous la carte (gabarit classique), en pied du gabarit
    # conversation, et en fin des deux versions texte.
    pied = ('<p style="color: #6b706e; font-size: 11px; line-height: 1.5; Text-align: center; '
            f'margin: 14px auto 24px; width: 520px;">{SIGNATURE}</p>')
    remplacer(r, f, "{{ end }}\n{{ end }}\n</div>\n</div>\n</div>\n</body>",
              "{{ end }}\n{{ end }}\n</div>\n" + pied + "\n</div>\n</div>\n</body>")
    remplacer(r, f, "    {{ end }}\n</div>\n</body>",
              "    {{ end }}\n"
              f'    <div style="padding: 8px 20px 12px; color: #6b706e; font-size: 11px;">{SIGNATURE}</div>\n'
              "</div>\n</body>")
    remplacer(r, f, "{{ range $line := .FooterLines}}\n{{ $line.Text }}\n{{ end }}`",
              "{{ range $line := .FooterLines}}\n{{ $line.Text }}\n{{ end }}\n-- \n" + SIGNATURE + "\n`", fois=2)
    # Version texte : « Ouvrir la tâche : » (espace avant les deux-points).
    remplacer(r, f, "{{ if .ActionURL }}{{ .ActionText }}:\n", "{{ if .ActionURL }}{{ .ActionText }} :\n", fois=2)
    # Lien vers la tâche en tête des courriels de conversation : vert de la charte.
    remplacer(r, "pkg/notifications/mail.go", 'style="color: #0969da; text-decoration: none;">(%s',
              'style="color: #286355; text-decoration: none;">(%s')

    # Expéditeur. Sans nom fourni : « Juste un suivi ». Pour une assignation, un
    # commentaire, une mention ou un ajout à une équipe, Vikunja écrit
    # « Prénom Nom via Vikunja » : « via Juste un suivi » désormais.
    remplacer(r, "pkg/mail/send_mail.go", 'opts.From = "Vikunja <"', f'opts.From = "{NOM} <"')
    remplacer(r, "pkg/mail/send_mail.go", 'm.SetUserAgent("Vikunja " + version.Version)',
              f'm.SetUserAgent("{NOM} (Vikunja " + version.Version + ")")')
    remplacer(r, "pkg/user/user.go", 'Name:    u.GetName() + " via Vikunja",', f'Name:    u.GetName() + " via {NOM}",')
    # Nom affiché dans l'appli d'authentification (TOTP).
    remplacer(r, "pkg/user/totp.go", 'Issuer:      "Vikunja",', f'Issuer:      "{NOM}",')

    # Langue : le service est francophone. Tout courriel part en français, quelle
    # que soit la langue réglée sur le compte (vide, « fr », « fr-FR », « en »...) :
    # Vikunja traduit chaque courriel dans la langue que rend User.Lang().
    remplacer(r, "pkg/user/user.go", "func (u *User) Lang() string {\n\treturn u.Language\n}",
              "func (u *User) Lang() string {\n"
              "\t// Juste un suivi : service francophone, courriels en français pour tous.\n"
              "\treturn \"fr-FR\"\n}")
    # Deux durées de retard lues dans la langue du compte et non dans celle du
    # courriel (« overdue since 3 days » au milieu d'un texte français), et un
    # appel sans langue du tout : la liste des retards perdait « en retard ».
    f = "pkg/models/notifications.go"
    remplacer(r, f, "getOverdueSinceString(until, n.User.Language)))", "getOverdueSinceString(until, lang)))")
    remplacer(r, f, 'i18n.T("notifications.task.overdue.overdue", getOverdueSinceString(until, n.User.Language))',
              'i18n.T(lang, "notifications.task.overdue.overdue", getOverdueSinceString(until, lang))')
    # Date d'expiration d'un jeton d'API au format français.
    remplacer(r, "pkg/models/api_tokens_expiry_notification.go", 'n.Token.ExpiresAt.Format("2006-01-02")',
              'n.Token.ExpiresAt.Format("02/01/2006")', fois=2)
    # Courriel de test de l'administrateur (vikunja testmail) : en français aussi.
    f = "pkg/cmd/testmail.go"
    remplacer(r, f, 'From("Vikunja <"+config.MailerFromEmail.GetString()+">").',
              f'From("{NOM} <"+config.MailerFromEmail.GetString()+">").')
    remplacer(r, f, 'Subject("Test from Vikunja").', f'Subject("Courriel de test de {NOM}").')
    remplacer(r, f, 'Line("This is a test mail!").', 'Line("Ceci est un courriel de test.").')
    remplacer(r, f, 'Line("If you received this, Vikunja is correctly set up to send emails.").',
              f'Line("Si vous le recevez, {NOM} sait envoyer ses courriels.").')
    remplacer(r, f, 'Action("Go to your instance", config.ServicePublicURL.GetString())',
              f'Action("Ouvrir {NOM}", config.ServicePublicURL.GetString())')
    remplacer(r, f, 'notifications.RenderMail(message, "en")', 'notifications.RenderMail(message, "fr-FR")')

    traduire_courriels(r)
    renommer_dans_traductions(r, "pkg/i18n/lang/en.json", (), minimum=20)
    # Les traductions sont rangées sous « fr-FR ». User.Lang() rend toujours
    # « fr-FR » désormais, mais un compte réglé sur « fr » (defaultsettings.language
    # de jus.1, hérité par les premiers comptes OIDC) doit rester valide aux yeux du
    # validateur des paramètres : alias « fr », même contenu, déclaré dans
    # availableLanguages sans quoi Init() ignore le fichier (cas de jus.2).
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
