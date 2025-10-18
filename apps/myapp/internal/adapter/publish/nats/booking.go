package publish

import (
	"context"
	"encoding/json"
	"log/slog"

	"github.com/nats-io/nats.go"
	"wirelesscar.com/mcp-atlassian/internal/core/config/logger"
	"wirelesscar.com/mcp-atlassian/internal/core/domain"
)

type BookingPublisher struct {
	nc *nats.Conn
}

func NewBookingPublisher(nc *nats.Conn) *BookingPublisher {
	return &BookingPublisher{
		nc,
	}
}

func (sp *BookingPublisher) PublishCreatedBooking(ctx context.Context, booking domain.Booking) {
	subject := "bookings.created"
	if sp.nc != nil {
		jsonBooking, err := json.Marshal(booking)
		if err != nil {
			logger.GetLogger().Error("Failed to marshal booking", slog.String("error", err.Error()))
			return
		}
		logger.GetLogger().Debug("Publishing booking on subject ", subject, slog.String("error", ""))
		err = sp.nc.Publish(subject, jsonBooking)
		if err != nil {
			logger.GetLogger().Error("Failed publish booking", slog.String("error", err.Error()))
		}
	}
}

func (sp *BookingPublisher) PublishUpdatedBooking(ctx context.Context, booking domain.Booking) {
	subject := "bookings.updated"
	if sp.nc != nil {
		jsonBooking, err := json.Marshal(booking)
		if err != nil {
			logger.GetLogger().Error("Failed to marshal booking", slog.String("error", err.Error()))
			return
		}
		logger.GetLogger().Debug("Publishing booking on subject ", subject, slog.String("error", ""))
		err = sp.nc.Publish(subject, jsonBooking)
		if err != nil {
			logger.GetLogger().Error("Failed publish booking", slog.String("error", err.Error()))
		}
	}
}

func (sp *BookingPublisher) PublishDeletedBooking(ctx context.Context, booking domain.Booking) {
	subject := "bookings.deleted"
	if sp.nc != nil {
		jsonBooking, err := json.Marshal(booking)
		if err != nil {
			logger.GetLogger().Error("Failed to marshal booking", slog.String("error", err.Error()))
			return
		}
		logger.GetLogger().Debug("Publishing booking on subject ", subject, slog.String("error", ""))
		err = sp.nc.Publish(subject, jsonBooking)
		if err != nil {
			logger.GetLogger().Error("Failed publish booking", slog.String("error", err.Error()))
		}
	}
}
