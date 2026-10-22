.PHONY: check test vet build demo

check: vet test build demo

test:
	go test -race ./...

vet:
	go vet ./...

build:
	go build ./cmd/server

demo:
	go run ./cmd/demo
