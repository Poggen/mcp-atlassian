package logger

import (
	"log/slog"
	"sync"
)

var (
	logOnce         sync.Once
	singletonLogger *slog.Logger
)

// GetLogging retrieves singletonLogger object of application log configuration.
func GetLogger() *slog.Logger {

	logOnce.Do(func() {
		singletonLogger = slog.Default()
	})

	return singletonLogger
}
