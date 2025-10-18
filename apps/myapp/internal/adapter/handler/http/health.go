package http

import (
	"context"
	"net/http"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/nats-io/nats.go"
	"wirelesscar.com/mcp-atlassian/internal/core/config/logger"
)

type Checkable interface {
	Alive() bool
}

type HealthCheckHttpHandler struct {
	servicesToCheck []Checkable
}

type PingHealthChecker struct {
}

type NATSHealthChecker struct {
	nc *nats.Conn
}

type PostgresHealthChecker struct {
	ctx context.Context
	db  *pgxpool.Pool
}

func (d *PingHealthChecker) Alive() bool {
	return true
}

func (d *PostgresHealthChecker) Alive() bool {
	if err := d.db.Ping(d.ctx); err != nil {
		logger.GetLogger().Error("Database connection lost")
		return false
	}
	return true
}

func (n *NATSHealthChecker) Alive() bool {
	if !n.nc.IsConnected() {
		logger.GetLogger().Error("NATS connection lost")
		return false
	}
	return true
}

func NewHealthCheckHttpHandler(servicesToCheck ...Checkable) *HealthCheckHttpHandler {
	return &HealthCheckHttpHandler{
		servicesToCheck: servicesToCheck,
	}
}

func (h *HealthCheckHttpHandler) GetHealth(w http.ResponseWriter, r *http.Request) {
	for _, service := range h.servicesToCheck {
		if !service.Alive() {
			logger.GetLogger().WarnContext(r.Context(), "Health check failed")
			http.Error(w, "Service unavailable", http.StatusServiceUnavailable)
			return
		}
	}
	w.WriteHeader(http.StatusOK)
	w.Write([]byte("Success"))
}

func NewHealthzHandler() *HealthCheckHttpHandler {
	pingChecker := &PingHealthChecker{}
	return NewHealthCheckHttpHandler(pingChecker)
}

func NewReadyzHandler(ctx context.Context, db *pgxpool.Pool, nc *nats.Conn) *HealthCheckHttpHandler {
	dbChecker := &PostgresHealthChecker{ctx, db}
	natsChecker := &NATSHealthChecker{nc}
	return NewHealthCheckHttpHandler(dbChecker, natsChecker)
}
