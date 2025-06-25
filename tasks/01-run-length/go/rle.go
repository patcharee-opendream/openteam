package rle

import (
	"fmt"
	"strings"
)

// Encode returns the run‑length encoding of UTF‑8 string s.
//
// "AAB" → "A2B1"
func Encode(s string) string {
	if len(s) == 0 {
		return ""
	}
	var b strings.Builder
	runes := []rune(s)
	prev := runes[0]
	count := 1
	for _, r := range runes[1:] {
		if r == prev {
			count++
		} else {
			b.WriteRune(prev)
			b.WriteString(fmt.Sprintf("%d", count))
			prev = r
			count = 1
		}
	}
	b.WriteRune(prev)
	b.WriteString(fmt.Sprintf("%d", count))
	return b.String()
}
