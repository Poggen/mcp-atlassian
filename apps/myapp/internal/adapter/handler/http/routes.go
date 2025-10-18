package http

import (
	"net/http"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/nats-io/nats.go"
	"go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
)

func AddRoutes(
	mux *http.ServeMux,
	db *pgxpool.Pool,
	nc *nats.Conn,
	healthzHandler *HealthCheckHttpHandler,
	readyzHandler *HealthCheckHttpHandler,
	bookingHandler *BookingHandler,
	tickHandler *TickHandler,
) {
	// handleFunc is a replacement for mux.HandleFunc
	// which enriches the handler's HTTP instrumentation with the pattern as the http.route.
	handleFunc := func(pattern string, handlerFunc func(http.ResponseWriter, *http.Request)) {
		routeHandler := otelhttp.WithRouteTag(pattern, http.HandlerFunc(handlerFunc))
		spanHandler := otelhttp.NewHandler(routeHandler, pattern, otelhttp.WithFilter(func(r *http.Request) bool {
			// Skip health checks from tracing, might want to trace a small percentage of them in the future
			if r.URL.Path == "/healthz" || r.URL.Path == "/readyz" {
				return false
			}
			return true
		}))

		mux.Handle(pattern, spanHandler)
	}

	handleFunc("POST /tick", tickHandler.Tick)
	handleFunc("GET /healthz", healthzHandler.GetHealth)
	handleFunc("GET /readyz", readyzHandler.GetHealth)
	handleFunc("GET /bookings", bookingHandler.ListBookings)
	handleFunc("POST /bookings", bookingHandler.CreateBooking)
	handleFunc("GET /bookings/{id}", bookingHandler.GetBookingById)
	handleFunc("PUT /bookings/{id}", bookingHandler.UpdateBookingById)
	handleFunc("DELETE /bookings/{id}", bookingHandler.DeleteBookingById)
	handleFunc("GET /external/bookings", bookingHandler.GetExternalBookings)
}
