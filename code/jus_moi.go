// Vikunja is a to-do list application to facilitate your life.
// Copyright 2018-present Vikunja and contributors. All rights reserved.
// Ajout Juste un suivi, Le Poisson Barbu, 2026.
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

package models

// Mot-clé « moi » dans les filtres : `assignees in moi`, `created_by = moi`.
//
// Vikunja n'accepte dans ces deux champs que des noms d'utilisateur. Avec la
// connexion « Juste un CR », ce sont des identifiants opaques (`u-8d31…`) que
// personne ne connaît : un collègue ne pouvait pas filtrer sur ses propres
// actions sans aller chercher le sien. « moi » (ou « me ») est remplacé, juste
// avant la requête, par le nom d'utilisateur de la personne connectée.
//
// Limite : la vue Kanban d'un filtre enregistré range ses tâches par une autre
// voie (parseFilterCond), sans la personne connectée. Pour un filtre enregistré,
// le filtre « Mes actions » créé avec chaque compte porte déjà l'identifiant.

import (
	"strings"

	"code.vikunja.io/api/pkg/user"
	"code.vikunja.io/api/pkg/web"

	"xorm.io/xorm"
)

func jusEstMoi(valeur string) bool {
	v := strings.ToLower(strings.Trim(strings.TrimSpace(valeur), `"'`))
	return v == "moi" || v == "me"
}

// jusRemplacerMoi remplace « moi » dans les filtres sur les personnes. Sans
// compte (lien de partage), « moi » reste tel quel et ne trouve personne.
func jusRemplacerMoi(s *xorm.Session, a web.Auth, filtres []*taskFilter) {
	var identifiant string
	var remplacer func([]*taskFilter)
	remplacer = func(fs []*taskFilter) {
		for _, f := range fs {
			if groupe, ok := f.value.([]*taskFilter); ok {
				remplacer(groupe)
				continue
			}
			if f.field != "assignees" && f.field != "created_by" {
				continue
			}
			valeurs, ok := f.value.([]string)
			if !ok {
				continue
			}
			for i, v := range valeurs {
				if !jusEstMoi(v) {
					continue
				}
				if identifiant == "" {
					u, err := user.GetFromAuth(a)
					if err != nil || u == nil || u.ID == 0 {
						return
					}
					identifiant = u.Username
					if identifiant == "" {
						// Jeton d'API : l'objet d'authentification peut ne porter que l'ID.
						complet, err := user.GetUserByID(s, u.ID)
						if err != nil {
							return
						}
						identifiant = complet.Username
					}
				}
				valeurs[i] = identifiant
			}
		}
	}
	remplacer(filtres)
}
