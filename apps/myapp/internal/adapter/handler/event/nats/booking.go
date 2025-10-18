package event

import (
	"bytes"
	"context"
	"encoding/json"
	"log/slog"

	"github.com/nats-io/nats.go"
	"wirelesscar.com/mcp-atlassian/internal/core/config/logger"
	"wirelesscar.com/mcp-atlassian/internal/core/domain"
	"wirelesscar.com/mcp-atlassian/internal/core/ports"
)

type BookingEventHandler struct {
	svc ports.BookingService
}

func NewBookingEventHandler(svc ports.BookingService) *BookingEventHandler {
	return &BookingEventHandler{
		svc,
	}
}

type CreateBookingRequest struct {
	Date     string `json:"date"`
	Service  string `json:"service"`
	Customer string `json:"customer"`
}

func (sh *BookingEventHandler) Init(nc *nats.Conn, ctx context.Context) error {
	subject := "bookings.new"
	logger.GetLogger().Debug("Listen on subject", subject, slog.String("error", ""))
	_, err := nc.Subscribe(subject, func(msg *nats.Msg) {
		logger.GetLogger().InfoContext(ctx, "recivied new booking", "subject", msg.Subject, "data", msg.Data)

		var req CreateBookingRequest
		if err := json.NewDecoder(bytes.NewReader(msg.Data)).Decode(&req); err != nil {
			logger.GetLogger().ErrorContext(ctx, "Failed to decode message", slog.String("error", err.Error()))
			return
		}

		booking := domain.Booking{
			Date:     req.Date,
			Service:  req.Service,
			Customer: req.Customer,
		}

		if err := sh.svc.CreateBooking(ctx, &booking); err != nil {
			logger.GetLogger().ErrorContext(ctx, "Failed to create booking", slog.String("error", err.Error()))
			return
		}

		bookingMsg, err := json.Marshal(booking)
		if err != nil {
			logger.GetLogger().ErrorContext(ctx, "Failed to create booking", slog.String("error", err.Error()))
			return
		}

		logger.GetLogger().InfoContext(ctx, "created", "booking", booking)
		msg.Respond(bookingMsg)
	})
	if err != nil {
		logger.GetLogger().ErrorContext(ctx, "Failed to subscribe to subject", slog.String("subject", subject), slog.String("error", err.Error()))
		return err
	}

	return nil
}
