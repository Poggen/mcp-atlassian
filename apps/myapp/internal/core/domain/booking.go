package domain

type Booking struct {
	ID       string `json:"id"`
	Date     string `json:"date"`
	Service  string `json:"service"`
	Customer string `json:"customer"`
}
