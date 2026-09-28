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

package v1

// Création anticipée d'un compte « Se connecter avec Juste un CR ».
//
// Vikunja n'assigne une tâche qu'à un compte existant, et un compte OIDC ne
// naît qu'à la première connexion. Une action décidée en réunion pour un
// collègue qui ne s'est jamais connecté restait donc sans responsable. Ce point
// d'entrée crée le compte d'avance, exactement comme le ferait la connexion
// (mêmes émetteur et sujet, même identifiant, projet par défaut) : à sa
// première connexion, Vikunja le retrouve au lieu d'en créer un second.
//
// Fermé tant que VIKUNJA_JUS_PROVISION_SECRET (32 caractères au moins) et
// VIKUNJA_JUS_PROVISION_ISSUER ne sont pas posés. Le secret n'ouvre que la
// création d'un compte vide, sans mot de passe : personne ne peut s'y
// connecter autrement que par le fournisseur OIDC, avec le bon sujet.

import (
	"crypto/sha256"
	"crypto/subtle"
	"encoding/hex"
	"net/http"
	"os"
	"strings"

	"code.vikunja.io/api/pkg/db"
	"code.vikunja.io/api/pkg/models"
	"code.vikunja.io/api/pkg/user"

	"github.com/labstack/echo/v5"
)

type jusCompte struct {
	// Sujet OIDC : l'identifiant de la personne chez le fournisseur (Juste un CR).
	Subject string `json:"subject"`
	// Doit valoir « u- » + les 16 premiers caractères hexadécimaux du SHA-256 du
	// sujet : la règle de Juste un CR (lib/suivi-identity.ts). Un identifiant
	// qui ne la respecte pas ne serait jamais celui que la connexion demande.
	Username string `json:"username"`
	Name     string `json:"name"`
	Email    string `json:"email"`
}

type jusCompteReponse struct {
	ID       int64  `json:"id"`
	Username string `json:"username"`
	Cree     bool   `json:"cree"`
}

func jusIdentifiant(subject string) string {
	empreinte := sha256.Sum256([]byte(subject))
	return "u-" + hex.EncodeToString(empreinte[:])[:16]
}

// JusCreerCompte crée (ou retrouve) le compte OIDC d'une personne.
func JusCreerCompte(c *echo.Context) error {
	secret := os.Getenv("VIKUNJA_JUS_PROVISION_SECRET")
	issuer := strings.TrimSpace(os.Getenv("VIKUNJA_JUS_PROVISION_ISSUER"))
	if len(secret) < 32 || issuer == "" {
		return echo.NewHTTPError(http.StatusNotFound, "Not found")
	}
	fourni := c.Request().Header.Get("X-JC-Provision")
	if subtle.ConstantTimeCompare([]byte(fourni), []byte(secret)) != 1 {
		return echo.NewHTTPError(http.StatusUnauthorized, "Secret refusé.")
	}

	var in jusCompte
	if err := c.Bind(&in); err != nil {
		return echo.NewHTTPError(http.StatusBadRequest, "Corps illisible.").Wrap(err)
	}
	in.Subject = strings.TrimSpace(in.Subject)
	in.Name = strings.TrimSpace(in.Name)
	in.Email = strings.TrimSpace(in.Email)
	if in.Subject == "" || len(in.Subject) > 250 {
		return echo.NewHTTPError(http.StatusBadRequest, "Sujet absent ou trop long.")
	}
	if in.Username != jusIdentifiant(in.Subject) {
		return echo.NewHTTPError(http.StatusBadRequest, "Identifiant sans rapport avec le sujet.")
	}
	if !strings.Contains(in.Email, "@") || len(in.Email) > 250 || len(in.Name) > 250 {
		return echo.NewHTTPError(http.StatusBadRequest, "Adresse ou nom invalide.")
	}

	s := db.NewSession()
	defer s.Close()

	existant, err := user.GetUserWithEmail(s, &user.User{Issuer: issuer, Subject: in.Subject})
	if err == nil || (user.IsErrUserStatusError(err) && existant != nil && existant.ID != 0) {
		// Déjà là (créé d'avance ou déjà connecté) : rien à faire. Un compte
		// désactivé reste désactivé, ce n'est pas à ce point d'entrée d'en décider.
		return c.JSON(http.StatusOK, jusCompteReponse{ID: existant.ID, Username: existant.Username})
	}
	if !user.IsErrUserDoesNotExist(err) {
		return err
	}

	u, err := user.CreateUser(s, &user.User{
		Username: in.Username,
		Email:    in.Email,
		Name:     in.Name,
		Status:   user.StatusActive,
		Issuer:   issuer,
		Subject:  in.Subject,
	})
	if err != nil {
		_ = s.Rollback()
		if user.IsErrUsernameExists(err) {
			return echo.NewHTTPError(http.StatusConflict, "Identifiant déjà pris par un autre compte.")
		}
		return err
	}
	// Le projet par défaut que la connexion OIDC aurait créé (cf. openid.getOrCreateUser).
	if err := models.CreateNewProjectForUser(s, u); err != nil {
		_ = s.Rollback()
		return err
	}
	if err := s.Commit(); err != nil {
		_ = s.Rollback()
		return err
	}
	return c.JSON(http.StatusCreated, jusCompteReponse{ID: u.ID, Username: u.Username, Cree: true})
}
