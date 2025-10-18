package ports

import (
	"context"

	"wirelesscar.com/mcp-atlassian/internal/core/domain"
)

type BookingPublisher interface {
	PublishCreatedBooking(ctx context.Context, booking domain.Booking)
	PublishUpdatedBooking(ctx context.Context, booking domain.Booking)
	PublishDeletedBooking(ctx context.Context, booking domain.Booking)
}

type BookingRepository interface {
	CreateBooking(ctx context.Context, booking *domain.Booking) error
	ListBookings(ctx context.Context) ([]domain.Booking, error)
	GetBookingById(ctx context.Context, id string) (domain.Booking, error)
	DeleteBookingById(ctx context.Context, id string) error
	UpdateBookingById(ctx context.Context, id string, booking *domain.Booking) error
}

type BookingService interface {
	CreateBooking(ctx context.Context, booking *domain.Booking) error
	GetBookingById(ctx context.Context, id string) (domain.Booking, error)
	ListBookings(ctx context.Context) ([]domain.Booking, error)
	DeleteBookingById(ctx context.Context, id string) error
	UpdateBookingById(ctx context.Context, id string, booking *domain.Booking) error
}
