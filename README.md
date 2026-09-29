# Vikunja aux couleurs de Juste un suivi

[Juste un suivi](https://lejustecloud.fr/justeunsuivi.html) est le service de suivi des actions du
Juste Cloud, opéré par Le Poisson Barbu. Il repose sur [Vikunja](https://vikunja.io), logiciel libre
publié sous licence AGPL v3.

Ce dépôt contient **tout ce qui distingue notre version de Vikunja** : les changements apportés à
son code, et rien d'autre. Il est public parce que l'AGPL v3 le demande : quiconque utilise une
version modifiée d'un logiciel AGPL servi en ligne doit pouvoir en obtenir le code source.

## Ce qui change par rapport à Vikunja

De l'habillage, et un seul ajout fonctionnel (en fin de liste) :

- logo, favicon et icônes de l'application ;
- couleur principale (vert `#286355`) et typographie (Public Sans) de l'interface ;
- le nom « Juste un suivi » à la place de « Vikunja » dans les titres et les textes (français et
  anglais) ;
- les couleurs, le logo, le nom d'expéditeur et la signature des courriels de notification ;
- des courriels **toujours en français**, quelle que soit la langue réglée sur le compte, avec nos
  propres textes ([`traductions/courriels-fr.json`](traductions/courriels-fr.json)) à la place de la
  traduction française de Vikunja, incomplète. `personnaliser.py` arrête la construction si une clé
  utilisée par un courriel n'y figure pas ou si un format (`%[1]s`, `%[1]d`) diffère de l'anglais.
- `PUT /api/v1/jus/comptes` ([`code/jus_comptes.go`](code/jus_comptes.go)) : crée d'avance le compte
  « Se connecter avec Juste un CR » d'une personne, pour qu'une tâche puisse lui être assignée avant
  sa première connexion. Fermé tant que `VIKUNJA_JUS_PROVISION_SECRET` et
  `VIKUNJA_JUS_PROVISION_ISSUER` ne sont pas posés.

« Propulsé par Vikunja » reste affiché en bas du menu et mène ici.

## Comment c'est construit

Le code source correspondant à une image se reconstitue ainsi :

1. le code de Vikunja à la version indiquée dans [`VERSION`](VERSION) (`2.6.0-jus.1` = Vikunja
   `v2.6.0`, habillage n° 1), téléchargé depuis [go-vikunja/vikunja](https://github.com/go-vikunja/vikunja) ;
2. [`personnaliser.py`](personnaliser.py) appliqué à ce code, qui y dépose les fichiers de
   [`visuels/`](visuels) ;
3. le `Dockerfile` de Vikunja, inchangé.

Le workflow [`image.yml`](.github/workflows/image.yml) enchaîne ces trois étapes à chaque push sur
`main` et publie `ghcr.io/lpb-groupe/vikunja-juste-un-suivi:<VERSION>`.

Pour reproduire l'image localement :

```sh
git clone --depth 1 --branch v2.6.0 https://github.com/go-vikunja/vikunja.git vikunja
python3 personnaliser.py vikunja
docker build -t vikunja-juste-un-suivi vikunja
```

## Monter de version

1. Changer la version amont dans `VERSION` et repartir à `jus.1` (`2.4.0-jus.1`).
2. Pousser. Si Vikunja a réécrit un fichier que nous modifions, `personnaliser.py` s'arrête en
   nommant le fichier et le texte introuvable : on corrige l'ancre, rien d'autre.
3. Vérifier l'image sur une instance de test avant de la poser sur les tenants.

Un changement d'habillage seul incrémente le numéro final (`2.6.0-jus.2`).

## Visuels

`visuels/` est généré par [`generer-visuels.py`](generer-visuels.py) à partir de la charte le Juste
Cloud et des polices de `sources/polices/`. On ne le relance que si le logo ou la charte changent.

## Licences

- Code de Vikunja et de ce dépôt : [AGPL v3](https://github.com/go-vikunja/vikunja/blob/main/LICENSE).
- Public Sans : SIL Open Font License 1.1 ([`sources/polices/OFL.txt`](sources/polices/OFL.txt)).
- Pictogramme de liste : dérivé de [Lucide](https://lucide.dev) (licence ISC).
- Le nom et le logo Juste un suivi / le Juste Cloud sont des marques de Le Poisson Barbu et ne
  sont pas couverts par ces licences.
