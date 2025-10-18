package handler

import (
	"encoding/json"
	"net/http"

	"wirelesscar.com/mcp-atlassian/internal/core/domain"
	"wirelesscar.com/mcp-atlassian/internal/core/ports"
)

type BookingHandler struct {
	svc ports.BookingService
}

// NewOrderHandler creates a new OrderHandler instance
func NewBookingHandler(svc ports.BookingService) *BookingHandler {
	return &BookingHandler{
		svc,
	}
}

type CreateBookingRequest struct {
	Date     string `json:"date"`
	Service  string `json:"service"`
	Customer string `json:"customer"`
}

func (sh *BookingHandler) CreateBooking(w http.ResponseWriter, r *http.Request) {
	var req CreateBookingRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	ctx := r.Context()
	booking := domain.Booking{
		Date:     req.Date,
		Service:  req.Service,
		Customer: req.Customer,
	}

	err := sh.svc.CreateBooking(ctx, &booking)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(booking)
}

func (sh *BookingHandler) GetBookingById(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("id")
	ctx := r.Context()

	booking, err := sh.svc.GetBookingById(ctx, id)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	if booking.ID == "" {
		http.Error(w, "booking not found", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(booking)
}

func (sh *BookingHandler) ListBookings(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	bookings, err := sh.svc.ListBookings(ctx)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	if len(bookings) == 0 {
		http.Error(w, "no bookings found", http.StatusNotFound)
		return
	}
	json.NewEncoder(w).Encode(bookings)
}
