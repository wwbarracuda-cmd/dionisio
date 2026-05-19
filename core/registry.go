package registry

import (
	"context"
	"sync"
)

type Module interface {
	Name() string
	Init(ctx context.Context) error
	Start(ctx context.Context) error
	Shutdown() error
}

var (
	modules = make(map[string]Module)
	mu      sync.RWMutex
)

func Register(m Module) {
	mu.Lock()
	defer mu.Unlock()
	modules[m.Name()] = m
}

func All() []Module {
	mu.RLock()
	defer mu.RUnlock()
	out := make([]Module, 0, len(modules))
	for _, m := range modules {
		out = append(out, m)
	}
	return out
}