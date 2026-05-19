package deps

import (
	"context"
	"log/slog"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/redis/go-redis/v9"
)

type Container struct {
	Logger   *slog.Logger
	DB       *pgxpool.Pool
	Redis    *redis.Client
	EventBus chan any // semplificato per demo; in prod usa libreria pub/sub strutturata
}

func New(ctx context.Context) (*Container, error) {
	logger := slog.New(slog.NewJSONHandler(slog.NewTextHandler(nil), nil))

	pool, err := pgxpool.New(ctx, getEnvOrPanic("DATABASE_URL"))
	if err != nil {
		return nil, err
	}

	rdb := redis.NewClient(&redis.Options{Addr: getEnvOrPanic("REDIS_URL")})
	if err := rdb.Ping(ctx).Err(); err != nil {
		return nil, err
	}

	return &Container{
		Logger:   logger,
		DB:       pool,
		Redis:    rdb,
		EventBus: make(chan any, 1000),
	}, nil
}

func getEnvOrPanic(key string) string {
	v := os.Getenv(key)
	if v == "" {
		panic("missing required env: " + key)
	}
	return v
}