package main

import (
	"context"
	"fmt"
	"io"
	"log/slog"
	"net"
	"net/http"
	"os"
	"os/signal"
	"sync"
	"time"

	wirelesscar_otel "github.com/WirelessCar-WDP/go-opentelemetry-instrumentation"
	_ "github.com/lib/pq"
	"github.com/nats-io/nats.go"
	event "wirelesscar.com/mcp-atlassian/internal/adapter/handler/event/nats"
	handler "wirelesscar.com/mcp-atlassian/internal/adapter/handler/http"
	publish "wirelesscar.com/mcp-atlassian/internal/adapter/publish/nats"
	repository "wirelesscar.com/mcp-atlassian/internal/adapter/storage/repository/postgres"
	"wirelesscar.com/mcp-atlassian/internal/core/config"
	"wirelesscar.com/mcp-atlassian/internal/core/config/logger"
	"wirelesscar.com/mcp-atlassian/internal/core/service"
)

func main() {
	ctx := context.Background()
	if err := run(ctx, os.Stdout, os.Args); err != nil {
		fmt.Fprintf(os.Stderr, "%s\n", err)
		os.Exit(1)
	}
}

func run(ctx context.Context, w io.Writer, args []string) error {
	ctx, cancel := signal.NotifyContext(ctx, os.Interrupt)
	defer cancel()

	otelShutdown, err := wirelesscar_otel.SetupOTelSDK(ctx)
	if err != nil {
		if uw, ok := err.(interface{ Unwrap() []error }); ok {
			slog.Error("Error initializing OpenTelemetry SDK", "error", err)
			errs := uw.Unwrap()
			for _, e := range errs {
				slog.Error("Error initializing OpenTelemetry SDK", "error", e)
			}
		}
	}
	defer otelShutdown(ctx)

	cfg := config.GetConfig()

	db, err := repository.NewDB(ctx)
	if err != nil {
		slog.Error("Error initializing database connection", "error", err)
		os.Exit(1)
	}
	defer db.Close()

	nc := setupNatsConnection()
	defer nc.Close()

	healthzHandler := handler.NewHealthzHandler()
	readyzHandler := handler.NewReadyzHandler(ctx, db, nc)
	tickHandler := handler.NewTickHandler()

	bookingPublisher := publish.NewBookingPublisher(nc)
	bookingRepository := repository.NewBookingRepository(db)
	bookingService := service.NewBookingService(bookingPublisher, bookingRepository)
	bookingHandler := handler.NewBookingHandler(bookingService)

	BookingEventHandler := event.NewBookingEventHandler(bookingService)
	BookingEventHandler.Init(nc, ctx)

	srv := handler.NewServer(
		db,
		nc,
		healthzHandler,
		readyzHandler,
		bookingHandler,
		tickHandler,
	)

	httpServer := &http.Server{
		Addr:         net.JoinHostPort(cfg.Host, cfg.Port),
		ReadTimeout:  5 * time.Second,
		WriteTimeout: 10 * time.Second,
		IdleTimeout:  60 * time.Second,
		Handler:      srv,
	}

	go func() {
		logger.GetLogger().Info("starting server", "address", httpServer.Addr)
		if err := httpServer.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.GetLogger().Error("listening and serving: %s\n", slog.String("error", err.Error()))
		}
	}()
	var wg sync.WaitGroup
	wg.Add(1)
	go func() {
		defer wg.Done()
		<-ctx.Done()
		// make a new context for the shutdown procedure
		shutdownCtx, cancel := context.WithTimeout(ctx, 10*time.Second)
		defer cancel()
		if err := httpServer.Shutdown(shutdownCtx); err != nil {
			logger.GetLogger().Error("shutting down http server: %s\n", slog.String("error", err.Error()))
		}
	}()
	wg.Wait()
	return nil
}

func setupNatsConnection() *nats.Conn {
	credentialsPath := "/var/run/secrets/nats/user.creds"
	nc, err := nats.Connect(
		config.GetConfig().NatsURL,
		nats.UserCredentials(credentialsPath),
		nats.Name(config.GetConfig().ProjectName),
	)
	if err != nil {
		logger.GetLogger().Error("connecting to nats", slog.String("error", err.Error()))
	}

	return nc
}
