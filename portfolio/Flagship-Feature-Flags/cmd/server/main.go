package main

import (
	"log"
	"net/http"
	"os"
	"time"

	"github.com/LAKSHAY-ATREJA/Flagship-Feature-Flags/internal/api"
	"github.com/LAKSHAY-ATREJA/Flagship-Feature-Flags/internal/flags"
)

func main() {
	e := flags.New([]flags.Flag{{Key: "checkout-v2", Enabled: true, Rollout: 20}})
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	server := &http.Server{
		Addr:              ":" + port,
		Handler:           api.NewHandler(e),
		ReadHeaderTimeout: 5 * time.Second,
	}
	log.Printf("Flagship listening on %s", server.Addr)
	log.Fatal(server.ListenAndServe())
}
