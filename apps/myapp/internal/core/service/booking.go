package service

import (
	"context"
	"fmt"

	"wirelesscar.com/mcp-atlassian/internal/core/domain"
	"wirelesscar.com/mcp-atlassian/internal/core/ports"
)

var _ ports.BookingService = &BookingService{}

type BookingService struct {
	bookingPublisher  ports.BookingPublisher
	bookingRepository ports.BookingRepository
}

func NewBookingService(bookingPublisher ports.BookingPublisher, bookingRepository ports.BookingRepository) *BookingService {
	return &BookingService{
		bookingPublisher,
		bookingRepository,
	}
}

func (srv *BookingService) CreateBooking(ctx context.Context, booking *domain.Booking) error {

	// Business logic in service. This is just a stupid example

	// Interacting with different adapters, which are the ports to the outside world
	err := srv.bookingRepository.CreateBooking(ctx, booking)
	if err != nil {
		return fmt.Errorf("failed to create booking: %w", err)
	}

	// Also publish an event to demonstrate messaging capablities
	srv.bookingPublisher.PublishCreatedBooking(ctx, *booking)

	return nil
}

func (srv *BookingService) GetBookingById(ctx context.Context, id string) (domain.Booking, error) {
	return srv.bookingRepository.GetBookingById(ctx, id)
}

func (srv *BookingService) ListBookings(ctx context.Context) ([]domain.Booking, error) {
	return srv.bookingRepository.ListBookings(ctx)
}

func (srv *BookingService) DeleteBookingById(ctx context.Context, id string) error {
	booking, err := srv.bookingRepository.GetBookingById(ctx, id)
	if err != nil {
		return err
	}

	err = srv.bookingRepository.DeleteBookingById(ctx, id)
	if err != nil {
		return err
	}

	srv.bookingPublisher.PublishDeletedBooking(ctx, booking)

	return nil
}

func (srv *BookingService) UpdateBookingById(ctx context.Context, id string, booking *domain.Booking) error {
	if id != booking.ID {
		return fmt.Errorf("provided id and booking ID do not match")
	}

	err := srv.bookingRepository.UpdateBookingById(ctx, id, booking)
	if err != nil {
		return err
	}

	srv.bookingPublisher.PublishUpdatedBooking(ctx, *booking)

	return nil
}
