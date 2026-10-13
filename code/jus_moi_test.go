// Ajout Juste un suivi, Le Poisson Barbu, 2026. Licence AGPL v3, comme Vikunja.

package models

import (
	"testing"

	"code.vikunja.io/api/pkg/db"
	"code.vikunja.io/api/pkg/user"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// idsFiltres renvoie les identifiants des tâches qu'un filtre donne à un compte.
func idsFiltres(t *testing.T, a *user.User, filtre string) []int64 {
	t.Helper()
	db.LoadAndAssertFixtures(t)
	s := db.NewSession()
	defer s.Close()
	got, _, _, err := (&TaskCollection{Filter: filtre}).ReadAll(s, a, "", 0, 500)
	require.NoError(t, err, filtre)
	taches, ok := got.([]*Task)
	require.True(t, ok, filtre)
	ids := make([]int64, 0, len(taches))
	for _, tache := range taches {
		ids = append(ids, tache.ID)
	}
	return ids
}

func TestJusMoi(t *testing.T) {
	u1 := &user.User{ID: 1, Username: "user1"}

	t.Run("moi vaut le nom d'utilisateur", func(t *testing.T) {
		attendu := idsFiltres(t, u1, "done = false && assignees in 'user1'")
		require.NotEmpty(t, attendu, "les données de test doivent assigner des tâches à user1")
		for _, f := range []string{
			"done = false && assignees in moi",
			"done = false && assignees in 'moi'",
			"done = false && assignees = MOI",
			"done = false && assignees in me",
			"done = false && (assignees in moi || assignees in 'personne-inconnue')",
		} {
			assert.Equal(t, attendu, idsFiltres(t, u1, f), f)
		}
	})

	t.Run("créé par moi", func(t *testing.T) {
		assert.Equal(t, idsFiltres(t, u1, "created_by = 'user1'"), idsFiltres(t, u1, "created_by = moi"))
	})

	t.Run("jeton d'API : compte réduit à l'ID", func(t *testing.T) {
		assert.Equal(t, idsFiltres(t, u1, "assignees in 'user1'"), idsFiltres(t, &user.User{ID: 1}, "assignees in moi"))
	})

	t.Run("moi dans une liste", func(t *testing.T) {
		assert.Equal(t, idsFiltres(t, u1, "assignees in 'user1,user2'"), idsFiltres(t, u1, "assignees in moi, user2"))
	})
}
