FROM golang:1.23-alpine AS build
WORKDIR /src
COPY . .
RUN go test ./... && go vet ./... && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /apisentinel ./cmd/server
FROM gcr.io/distroless/static-debian12
COPY --from=build /apisentinel /apisentinel
EXPOSE 8080
ENTRYPOINT ["/apisentinel"]
