package repository

import (
	"context"
	"database/sql"
	"log/slog"

	"github.com/jackc/pgx/v5/pgxpool"
	"wirelesscar.com/mcp-atlassian/internal/core/config/logger"
	"wirelesscar.com/mcp-atlassian/internal/core/domain"
)

type BookingRepository struct {
	db *pgxpool.Pool
}

func NewBookingRepository(db *pgxpool.Pool) *BookingRepository {
	return &BookingRepository{
		db,
	}
}

func (p *BookingRepository) ListBookings(ctx context.Context) ([]domain.Booking, error) {
	query := "SELECT id, date, service, customer FROM bookings"

	rows, err := p.db.Query(ctx, query)
	if err != nil {
		logger.GetLogger().Error("Failed list database", slog.String("error", err.Error()))
		return nil, err
	}
	defer rows.Close()

	var bookings []domain.Booking
	for rows.Next() {
		var b domain.Booking
		err := rows.Scan(&b.ID, &b.Date, &b.Service, &b.Customer)
		if err != nil {
			logger.GetLogger().Error("Failed parse rows from database", slog.String("error", err.Error()))
			return nil, err
		}
		bookings = append(bookings, b)
	}
	return bookings, nil
}

func (p *BookingRepository) GetBookingById(ctx context.Context, id string) (domain.Booking, error) {
	query := "SELECT id, date, service, customer FROM bookings WHERE id = $1"

	var booking domain.Booking
	err := p.db.QueryRow(ctx, query, id).Scan(&booking.ID, &booking.Date, &booking.Service, &booking.Customer)
	if err != nil {
		if err == sql.ErrNoRows {
			return domain.Booking{}, nil
		}
		logger.GetLogger().Error("Failed parse rows from database", slog.String("error", err.Error()))
		return domain.Booking{}, err
	}

	return booking, nil
}

func (p *BookingRepository) CreateBooking(ctx context.Context, booking *domain.Booking) error {
	query := `INSERT INTO bookings (date, service, customer) VALUES ($1, $2, $3) RETURNING id`

	err := p.db.QueryRow(ctx, query, booking.Date, booking.Service, booking.Customer).Scan(&booking.ID)
	if err != nil {
		logger.GetLogger().ErrorContext(ctx, "Failed insert into database", slog.String("error", err.Error()))
		return err
	}
	return nil
}

func (p *BookingRepository) UpdateBookingById(ctx context.Context, id string, booking *domain.Booking) error {
	query := `UPDATE bookings SET date=$1, service=$2, customer=$3 WHERE id=$4`

	_, err := p.db.Exec(ctx, query, booking.Date, booking.Service, booking.Customer, booking.ID)
	if err != nil {
		logger.GetLogger().ErrorContext(ctx, "Failed update scipe in database", slog.String("error", err.Error()))
		return err
	}
	return nil
}

func (p *BookingRepository) DeleteBookingById(ctx context.Context, id string) error {
	query := "DELETE FROM bookings WHERE id = $1"

	_, err := p.db.Exec(ctx, query, id)
	if err != nil {
		logger.GetLogger().ErrorContext(ctx, "Failed to delete from database", slog.String("error", err.Error()))
		return err
	}

	return nil
}
