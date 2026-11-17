package main

import (
	"bytes"
	"context"
	"io"
	"os"
	"path/filepath"
	"strings"
	"syscall"
	"testing"
	"time"
)

func TestChainFileRejectsNamedPipeWithoutWaiting(t *testing.T) {
	home := isolateCallEnv(t)
	writeChainSetting(t, home, "typesafe")
	path := filepath.Join(home, filepath.FromSlash(pluginKeyDirectory), "chain")
	if err := os.Remove(path); err != nil {
		t.Fatal(err)
	}
	if err := syscall.Mkfifo(path, 0600); err != nil {
		t.Fatal(err)
	}
	var diagnostic bytes.Buffer
	done := make(chan int, 1)
	go func() {
		done <- runCall(context.Background(), callOptions{check: true}, strings.NewReader(""), io.Discard, &diagnostic)
	}()
	select {
	case code := <-done:
		if code != 4 || !strings.Contains(diagnostic.String(), "not a regular file") {
			t.Fatalf("exit=%d stderr=%s; want exit 4 naming non-regular chain file", code, diagnostic.String())
		}
	case <-time.After(time.Second):
		// Release a regressed blocking open, so the failing test leaves no
		// reader behind and never needs to kill the whole test process.
		writer, err := os.OpenFile(path, os.O_WRONLY|syscall.O_NONBLOCK, 0)
		if err != nil {
			t.Fatal(err)
		}
		writer.Close()
		<-done
		t.Fatal("chain-file reader waited for a FIFO writer instead of rejecting it")
	}
}
