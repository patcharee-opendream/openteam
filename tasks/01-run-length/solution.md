# Solution: Run-Length Encoder

## Approach

We implemented a run-length encoder in Python, Go, and C#. The encoder processes any UTF-8 string, including emoji and rare Unicode, and outputs a string where each run of characters is replaced by the character followed by its count (e.g., `AAB` → `A2B1`).

- **Case-sensitive**: `A` and `a` are distinct.
- **Handles multi-digit counts**: e.g., `CCCCCCCCCCCC` → `C12`.
- **Full Unicode support**: Each code-point or grapheme is treated as a single character, so emoji and combined characters are encoded correctly.

## Interesting Twist

Imagine encoding a string of rare emoji or ancient script symbols for a digital museum archive, where each symbol's frequency is important for linguistic analysis. This encoder can handle such data without loss or confusion.

## Example

```
Input:  "AAAaaaBBB🦄🦄🦄🦄🦄CCCCCCCCCCCC"
Output: "A3a3B3🦄5C12"
```

## Testing

The provided tests cover empty strings, ASCII, Unicode, and emoji. All implementations pass these tests after the fix.
