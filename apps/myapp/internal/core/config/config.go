package config

import (
	"sync"

	"github.com/caarlos0/env/v11"
)

type Config struct {
	Host                     string `env:"HOST" envDefault:""`
	Port                     string `env:"PORT" envDefault:"3000"`
	Environment              string `env:"ENVIRONMENT" envDefault:"local"`
	PostgresConnectionString string `env:"POSTGRES_CONNECTION_STRING,unset"`
	NatsURL                  string `env:"NATS_URL" envDefault:"nats://localhost:4222"`
	ProjectName              string `env:"PROJECT_NAME" envDefault:"mcp-atlassian"`
	CollectorURL             string `env:"OTEL_EXPORTER_OTLP_ENDPOINT" envDefault:""`
}

var (
	once      sync.Once
	singleton *Config
)

// GetConfig retrieves singleton object of application configurations.
func GetConfig() *Config {

	once.Do(func() {
		singleton = &Config{}
		if err := env.Parse(singleton); err != nil {
			panic("Unable to parse application configuration!")
		}
	})

	return singleton
}
