package metrics

import (
	"sync"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/metric"
	"wirelesscar.com/mcp-atlassian/internal/core/config"
)

var (
	apiOnce    sync.Once
	apiCounter metric.Int64Counter
)

// GetLogging retrieves singleton object of application log configuration.
func GetApiCounter() metric.Int64Counter {

	apiOnce.Do(func() {
		meter := otel.Meter(config.GetConfig().ProjectName)
		apiCounter, _ = meter.Int64Counter(
			"api.counter",
			metric.WithDescription("Number of API calls."),
			metric.WithUnit("{call}"),
		)
	})

	return apiCounter
}
