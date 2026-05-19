package main

import (
	"context"
	"log/slog"
	"net"
	"os"
	"os/signal"
	"syscall"

	"dionisio/core/deps"
	"dionisio/core/registry"
	pbv1 "github.com/yourorg/dionisio/proto/dionisio/v1"
	"google.golang.org/grpc"
)

func init() {
	// Registrazione moduli (compile-time)
	registry.Register(newAPIModule())
	registry.Register(newAuthModule())
	registry.Register(newPaymentsModule())
	registry.Register(newAIModule())
	registry.Register(newNotificationsModule())
}

func main() {
	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	d, err := deps.New(ctx)
	if err != nil {
		slog.Error("deps init failed", "error", err)
		os.Exit(1)
	}
	defer func() { d.DB.Close(); d.Redis.Close() }()

	// Init moduli abilitati
	for _, m := range registry.All() {
		if err := m.Init(ctx); err != nil {
			slog.Error("module init failed", "name", m.Name(), "error", err)
			os.Exit(1)
		}
	}

	// Avvia server gRPC
	lis, err := net.Listen("tcp", ":9090")
	if err != nil {
		slog.Error("listen failed", "error", err)
		os.Exit(1)
	}

	srv := grpc.NewServer()
	pbv1.RegisterDionisioServiceServer(srv, newGRPCHandler(d))

	go func() {
		slog.Info("gRPC server listening on :9090")
		if err := srv.Serve(lis); err != nil {
			slog.Error("grpc serve failed", "error", err)
		}
	}()

	<-ctx.Done()
	slog.Info("shutting down gracefully...")

	srv.GracefulStop()
	for _, m := range registry.All() {
		if err := m.Shutdown(); err != nil {
			slog.Error("module shutdown failed", "name", m.Name(), "error", err)
		}
	}
	slog.Info("dionisio stopped")
}