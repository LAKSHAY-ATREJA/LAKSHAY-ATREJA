FROM golang:1.23-alpine AS build
WORKDIR /src
COPY . .
RUN CGO_ENABLED=0 go test ./... && go build -buildvcs=false -o /flagship ./cmd/server
FROM gcr.io/distroless/static-debian12
COPY --from=build /flagship /flagship
EXPOSE 8080
ENTRYPOINT ["/flagship"]
