package api

import (
	"encoding/json"
	"io"
	"net/http"

	"github.com/LAKSHAY-ATREJA/Flagship-Feature-Flags/internal/flags"
)

const maxBodyBytes = 1 << 20

type evaluationRequest struct {
	Key     string        `json:"key"`
	Subject string        `json:"subject"`
	Context flags.Context `json:"context"`
}

func NewHandler(engine *flags.Engine) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}
		writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
	})
	mux.HandleFunc("/v1/flags", func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodGet:
			writeJSON(w, http.StatusOK, engine.Snapshot())
		case http.MethodPut:
			var flag flags.Flag
			if err := decodeJSON(w, r, &flag); err != nil {
				http.Error(w, err.Error(), http.StatusBadRequest)
				return
			}
			if err := engine.Upsert(flag); err != nil {
				http.Error(w, err.Error(), http.StatusBadRequest)
				return
			}
			w.WriteHeader(http.StatusNoContent)
		default:
			w.WriteHeader(http.StatusMethodNotAllowed)
		}
	})
	mux.HandleFunc("/v1/evaluate", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			w.WriteHeader(http.StatusMethodNotAllowed)
			return
		}
		var request evaluationRequest
		if err := decodeJSON(w, r, &request); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
		if request.Key == "" {
			http.Error(w, "key is required", http.StatusBadRequest)
			return
		}
		writeJSON(w, http.StatusOK, map[string]any{
			"key": request.Key, "enabled": engine.Evaluate(request.Key, request.Subject, request.Context),
		})
	})
	return mux
}

func decodeJSON(w http.ResponseWriter, r *http.Request, value any) error {
	r.Body = http.MaxBytesReader(w, r.Body, maxBodyBytes)
	decoder := json.NewDecoder(r.Body)
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(value); err != nil {
		return err
	}
	if err := decoder.Decode(&struct{}{}); err != io.EOF {
		if err == nil {
			return io.ErrUnexpectedEOF
		}
		return err
	}
	return nil
}

func writeJSON(w http.ResponseWriter, status int, value any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(value)
}
