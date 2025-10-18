package http

import (
	"net/http"

	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/metric"
	"wirelesscar.com/mcp-atlassian/internal/core/config/logger"
	"wirelesscar.com/mcp-atlassian/internal/core/config/metrics"
)

type TickHandler struct {
}

func NewTickHandler() *TickHandler {
	return &TickHandler{}
}

func (sh *TickHandler) Tick(w http.ResponseWriter, r *http.Request) {
	logger.GetLogger().InfoContext(r.Context(), "Tick!")
	w.Header().Set("Content-Type", "application/json")
	metrics.GetApiCounter().Add(r.Context(), 1, metric.WithAttributes(attribute.String("type", "hits")))
	w.WriteHeader(http.StatusOK)
}
