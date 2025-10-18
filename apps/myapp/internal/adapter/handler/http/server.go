package http

import (
	"net/http"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/nats-io/nats.go"
)

func NewServer(
	db *pgxpool.Pool,
	nc *nats.Conn,
	healthzHandler *HealthCheckHttpHandler,
	readyzHandler *HealthCheckHttpHandler,
	bookingHandler *BookingHandler,
	tickHandler *TickHandler,
) http.Handler {
	mux := http.NewServeMux()
	AddRoutes(
		mux,
		db,
		nc,
		healthzHandler,
		readyzHandler,
		bookingHandler,
		tickHandler,
	)
	var handler http.Handler = mux
	return handler
}
