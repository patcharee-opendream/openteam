// Package aggregator – stub for Concurrent File Stats Processor.
package aggregator

import (
	"bufio"
	"context"
	"fmt"
	"os"
	"strings"
	"time"
)

// Result mirrors one JSON object in the final array.
type Result struct {
	Path   string `json:"path"`
	Lines  int    `json:"lines,omitempty"`
	Words  int    `json:"words,omitempty"`
	Status string `json:"status"` // "ok" or "timeout"
}

func processFile(ctx context.Context, baseDir, relPath string) Result {
	absPath := baseDir + string(os.PathSeparator) + relPath
	file, err := os.Open(absPath)
	if err != nil {
		return Result{Path: relPath, Status: "timeout"}
	}
	defer file.Close()
	lines := []string{}
	scanner := bufio.NewScanner(file)
	var sleepSec int
	first := true
	for scanner.Scan() {
		line := scanner.Text()
		if first && strings.HasPrefix(line, "#sleep=") {
			first = false
			parts := strings.SplitN(line, "=", 2)
			if len(parts) == 2 {
				sleepSec = 0
				_, err := fmt.Sscanf(parts[1], "%d", &sleepSec)
				if err == nil && sleepSec > 0 {
					select {
					case <-time.After(time.Duration(sleepSec) * time.Second):
					case <-ctx.Done():
						return Result{Path: relPath, Status: "timeout"}
					}
				}
			}
			continue
		}
		lines = append(lines, line)
		first = false
	}
	if err := scanner.Err(); err != nil {
		return Result{Path: relPath, Status: "timeout"}
	}
	wordCount := 0
	for _, l := range lines {
		wordCount += len(strings.Fields(l))
	}
	return Result{Path: relPath, Lines: len(lines), Words: wordCount, Status: "ok"}
}

// Aggregate must read filelistPath, spin up *workers* goroutines,
// apply a per‑file timeout, and return results in **input order**.
func Aggregate(filelistPath string, workers, timeout int) ([]Result, error) {
	file, err := os.Open(filelistPath)
	if err != nil {
		return nil, err
	}
	defer file.Close()
	var paths []string
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line != "" {
			paths = append(paths, line)
		}
	}
	if err := scanner.Err(); err != nil {
		return nil, err
	}
	baseDir := filelistPath[:strings.LastIndex(filelistPath, string(os.PathSeparator))]
	results := make([]Result, len(paths))
	ch := make(chan struct {
		idx int
		res Result
	})
	for i, path := range paths {
		go func(i int, path string) {
			ctx, cancel := context.WithTimeout(context.Background(), time.Duration(timeout)*time.Second)
			defer cancel()
			res := processFile(ctx, baseDir, path)
			ch <- struct {
				idx int
				res Result
			}{i, res}
		}(i, path)
	}
	for range paths {
		out := <-ch
		results[out.idx] = out.res
	}
	return results, nil
}
