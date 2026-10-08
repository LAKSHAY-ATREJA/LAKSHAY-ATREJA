package api

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/LAKSHAY-ATREJA/Flagship-Feature-Flags/internal/flags"
)

func request(t *testing.T, handler http.Handler, method, path, body string) *httptest.ResponseRecorder {
	t.Helper()
	req := httptest.NewRequest(method, path, bytes.NewBufferString(body))
	rec := httptest.NewRecorder()
	handler.ServeHTTP(rec, req)
	return rec
}

func TestHealthAndMethodValidation(t *testing.T) {
	handler := NewHandler(flags.New(nil))
	if rec := request(t, handler, http.MethodGet, "/health", ""); rec.Code != http.StatusOK {
		t.Fatalf("health status = %d", rec.Code)
	}
	if rec := request(t, handler, http.MethodGet, "/v1/evaluate", ""); rec.Code != http.StatusMethodNotAllowed {
		t.Fatalf("evaluate GET status = %d", rec.Code)
	}
}

func TestFlagLifecycleAndTargeting(t *testing.T) {
	handler := NewHandler(flags.New(nil))
	flag := `{"key":"beta","enabled":true,"rollout":100,"rules":[{"attribute":"country","operator":"eq","value":"AU"}]}`
	if rec := request(t, handler, http.MethodPut, "/v1/flags", flag); rec.Code != http.StatusNoContent {
		t.Fatalf("put status = %d: %s", rec.Code, rec.Body.String())
	}

	evaluate := func(country string) bool {
		body := `{"key":"beta","subject":"user-1","context":{"country":"` + country + `"}}`
		rec := request(t, handler, http.MethodPost, "/v1/evaluate", body)
		if rec.Code != http.StatusOK {
			t.Fatalf("evaluate status = %d: %s", rec.Code, rec.Body.String())
		}
		var result struct {
			Enabled bool `json:"enabled"`
		}
		if err := json.Unmarshal(rec.Body.Bytes(), &result); err != nil {
			t.Fatal(err)
		}
		return result.Enabled
	}
	if !evaluate("AU") || evaluate("US") {
		t.Fatal("targeting result did not match the country rule")
	}

	disabled := `{"key":"beta","enabled":false,"rollout":100}`
	if rec := request(t, handler, http.MethodPut, "/v1/flags", disabled); rec.Code != http.StatusNoContent {
		t.Fatalf("disable status = %d", rec.Code)
	}
	if evaluate("AU") {
		t.Fatal("kill switch did not override targeting")
	}
}

func TestRejectsInvalidPayload(t *testing.T) {
	handler := NewHandler(flags.New(nil))
	if rec := request(t, handler, http.MethodPut, "/v1/flags", `{"key":"x","enabled":true,"rollout":101}`); rec.Code != http.StatusBadRequest {
		t.Fatalf("invalid rollout status = %d", rec.Code)
	}
	if rec := request(t, handler, http.MethodPost, "/v1/evaluate", `{"subject":"x"}`); rec.Code != http.StatusBadRequest {
		t.Fatalf("missing key status = %d", rec.Code)
	}
}
