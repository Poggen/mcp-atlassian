package repository

import (
	"context"
	"log/slog"
	"time"

	"github.com/exaring/otelpgx"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"

	drive_config "wirelesscar.com/mcp-atlassian/internal/core/config"
	"wirelesscar.com/mcp-atlassian/internal/core/config/logger"
)

func NewDB(ctx context.Context) (*pgxpool.Pool, error) {
	dbConfig := Config()
	dbConfig.ConnConfig.Tracer = otelpgx.NewTracer()

	db, err := pgxpool.NewWithConfig(context.Background(), dbConfig)
	if err != nil {
		return nil, err
	}

	err = db.Ping(ctx)
	if err != nil {
		return nil, err
	}

	return db, nil
}

func Config() *pgxpool.Config {
	const defaultMaxConns = int32(7)
	const defaultMinConns = int32(3)
	const defaultMaxConnLifetime = time.Hour
	const defaultMaxConnIdleTime = time.Minute * 30
	const defaultHealthCheckPeriod = time.Minute
	const defaultConnectTimeout = time.Second * 5

	postgresConnectionString := drive_config.GetConfig().PostgresConnectionString
	dbConfig, err := pgxpool.ParseConfig(postgresConnectionString)
	if err != nil {
		logger.GetLogger().Error("Failed to parse the connection string", slog.String("error", err.Error()))
	}

	dbConfig.MaxConns = defaultMaxConns
	dbConfig.MinConns = defaultMinConns
	dbConfig.MaxConnLifetime = defaultMaxConnLifetime
	dbConfig.MaxConnIdleTime = defaultMaxConnIdleTime
	dbConfig.HealthCheckPeriod = defaultHealthCheckPeriod
	dbConfig.ConnConfig.ConnectTimeout = defaultConnectTimeout

	dbConfig.BeforeAcquire = func(ctx context.Context, c *pgx.Conn) bool {
		return true
	}

	dbConfig.AfterRelease = func(c *pgx.Conn) bool {
		return true
	}

	dbConfig.BeforeClose = func(c *pgx.Conn) {
	}

	return dbConfig
}
