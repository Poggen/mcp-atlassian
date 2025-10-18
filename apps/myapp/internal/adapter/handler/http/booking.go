package http

import (
	"encoding/json"
	"io"
	"log/slog"
	"net/http"

	"go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
	"wirelesscar.com/mcp-atlassian/internal/core/config/logger"
	"wirelesscar.com/mcp-atlassian/internal/core/domain"
	"wirelesscar.com/mcp-atlassian/internal/core/ports"
)

type BookingHandler struct {
	svc ports.BookingService
}

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

type UpdateBookingRequest struct {
	ID       string `json:"id"`
	Date     string `json:"date"`
	Service  string `json:"service"`
	Customer string `json:"customer"`
}

type BookingResponse struct {
	ID       string `json:"id"`
	Date     string `json:"date"`
	Service  string `json:"service"`
	Customer string `json:"customer"`
}

func newBookingResponse(booking *domain.Booking) BookingResponse {
	return BookingResponse{
		ID:       booking.ID,
		Date:     booking.Date,
		Service:  booking.Service,
		Customer: booking.Customer,
	}
}

func (sh *BookingHandler) CreateBooking(w http.ResponseWriter, r *http.Request) {
	logger.GetLogger().InfoContext(r.Context(), "Creating booking")
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

	response := newBookingResponse(&booking)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(response)
}

func (sh *BookingHandler) UpdateBookingById(w http.ResponseWriter, r *http.Request) {
	logger.GetLogger().InfoContext(r.Context(), "Update booking")
	id := r.PathValue("id")
	var req UpdateBookingRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	ctx := r.Context()
	booking := domain.Booking{
		ID:       req.ID,
		Date:     req.Date,
		Service:  req.Service,
		Customer: req.Customer,
	}

	err := sh.svc.UpdateBookingById(ctx, id, &booking)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	response := newBookingResponse(&booking)
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(response)
}

func (sh *BookingHandler) GetBookingById(w http.ResponseWriter, r *http.Request) {
	logger.GetLogger().InfoContext(r.Context(), "Get booking by id")
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
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(booking)
}

func (sh *BookingHandler) ListBookings(w http.ResponseWriter, r *http.Request) {
	logger.GetLogger().InfoContext(r.Context(), "List bookings")
	ctx := r.Context()
	var bookingsList []BookingResponse

	bookings, err := sh.svc.ListBookings(ctx)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	if len(bookings) == 0 {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode([]BookingResponse{})
		return
	}

	for _, booking := range bookings {
		bookingsList = append(bookingsList, newBookingResponse(&booking))
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(bookingsList)
}

func (sh *BookingHandler) DeleteBookingById(w http.ResponseWriter, r *http.Request) {
	logger.GetLogger().InfoContext(r.Context(), "Delete booking")
	id := r.PathValue("id")
	ctx := r.Context()

	err := sh.svc.DeleteBookingById(ctx, id)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusOK)
}

func (sh *BookingHandler) GetExternalBookings(w http.ResponseWriter, r *http.Request) {
	logger.GetLogger().InfoContext(r.Context(), "Getting external bookings")

	externalBookingURL := "http://localhost:3000/bookings"

	client := http.Client{Transport: otelhttp.NewTransport(http.DefaultTransport)}
	req, _ := http.NewRequestWithContext(r.Context(), "GET", externalBookingURL, nil)

	resp, err := client.Do(req)
	if err != nil {
		logger.GetLogger().ErrorContext(r.Context(), "Failed to call external service", slog.String("error", err.Error()))
		http.Error(w, "Failed to call external service: "+err.Error(), http.StatusInternalServerError)
		return
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		logger.GetLogger().ErrorContext(r.Context(), "Failed to read response body", slog.String("error", err.Error()))
		http.Error(w, "Failed to read response body: "+err.Error(), http.StatusInternalServerError)
		return
	}

	// Slice to hold all bookings
	var bookings []BookingResponse

	// Parse body into bookings
	err = json.Unmarshal(body, &bookings)
	if err != nil {
		logger.GetLogger().ErrorContext(r.Context(), "Failed to parse JSON", slog.String("error", err.Error()))
		http.Error(w, "Failed to parse JSON: "+err.Error(), http.StatusInternalServerError)
		return
	}

	// Set content type as JSON
	w.Header().Set("Content-Type", "application/json")
	// Encode bookings as JSON
	err = json.NewEncoder(w).Encode(bookings)
	if err != nil {
		logger.GetLogger().ErrorContext(r.Context(), "Failed to decode json", slog.String("error", err.Error()))

		http.Error(w, "Failed to encode bookings as JSON: "+err.Error(), http.StatusInternalServerError)
		return
	}
}
