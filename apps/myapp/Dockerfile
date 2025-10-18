# BUILDER - Everything needed in order to build the application should be contained in the builder.
# Only the application should be moved to the resulting image
FROM golang:1.24.5-alpine@sha256:daae04ebad0c21149979cd8e9db38f565ecefd8547cf4a591240dc1972cf1399 AS builder
WORKDIR /app

RUN apk update && \
    apk add --no-cache \
    git openssh

ARG GIT_WDP_ORG="WirelessCar-WDP"
ARG GIT_WDP_ORG_NO="org-133124332"
ARG GIT_OWNER_ORG="WDP-EarlyBirds"
ARG GIT_OWNER_ORG_NO="org-171265158"

ENV GOPRIVATE=github.com/$GIT_WDP_ORG,github.com/$GIT_OWNER_ORG

RUN --mount=type=secret,id=GIT_WDP_TOKEN \
    --mount=type=secret,id=GIT_OWNER_TOKEN \
    sh -c ' \
    if [ -e /run/secrets/GIT_WDP_TOKEN ] && [ -e /run/secrets/GIT_OWNER_TOKEN ]; then \
    echo "Using HTTPS with tokens"; \
    WDP_TOKEN=$(cat /run/secrets/GIT_WDP_TOKEN) && \
    OWNER_TOKEN=$(cat /run/secrets/GIT_OWNER_TOKEN) && \
    git config --global url.https://${WDP_TOKEN}@github.com/$GIT_WDP_ORG/.insteadOf https://github.com/$GIT_WDP_ORG/ && \
    git config --global url.https://${OWNER_TOKEN}@github.com/$GIT_OWNER_ORG/.insteadOf https://github.com/$GIT_OWNER_ORG/; \
    else \
    echo "Secrets not found; defaulting to SSH"; \
    git config --global url.ssh://$GIT_WDP_ORG_NO@github.com/$GIT_WDP_ORG/.insteadOf https://github.com/$GIT_WDP_ORG/ && \
    git config --global url.ssh://$GIT_OWNER_ORG_NO@github.com/$GIT_OWNER_ORG/.insteadOf https://github.com/$GIT_OWNER_ORG/ && \
    mkdir -p /root/.ssh && \
    ssh-keyscan github.com >> /root/.ssh/known_hosts; \
    fi'

# First copy only dependencies in order to cache layers when possible
COPY go.mod go.sum ./
RUN --mount=type=ssh go mod download

# The rest is copied separately in order to avoid downloading dependencies unnecessarily (this part will likely invalidate the cache)
COPY . .

RUN go build -o app ./cmd

# PRODUCTION IMAGE
# This part is being deployed and should be as small as possible
FROM gcr.io/distroless/static-debian12:nonroot

WORKDIR /app
COPY --from=builder /app/app .
ENTRYPOINT ["/app/app"]
