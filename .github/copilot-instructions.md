# Copilot Instructions

## Project scope

- Read `SPEC.md` and `PLAN.md` before implementing or changing project behavior.
- Implement the URL shortener only with the Python standard library.
- Keep changes focused on the requested issue or step.
- Do not modify unrelated files or existing test files unless the issue explicitly requests it.

## Data structures and hashing

- The core hash table must not use `dict`, `set`, or any existing mapping type for storage.
- Do not use Python's built-in `hash()` for table indexing or for generating short codes.
- Use chaining for hash-table collisions.
- Start with capacity 16 and resize to twice the capacity when load factor exceeds 0.75.
- Rehash every existing entry after resizing.

## Base62 and short URLs

- Use `0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ` as the exact Base62 character set.
- Encode non-negative integer IDs, not URL hash values, to create short codes.
- Repeated URLs must expand to the same short code.
- Validate URLs and raise the exceptions specified in `SPEC.md`.

## Testing

- Add or update `unittest` coverage before finalizing implementation behavior.
- Never change an existing test merely to make failing code pass; fix the implementation instead.
- Run `make test` and ensure all tests pass before every commit.

## Git and GitHub

- Commit only files relevant to the active issue.
- Use clear imperative commit messages that describe the change.
- Do not commit generated caches, build artifacts, or unrelated local files.
- Push the active development branch after a successful commit.
- Add a completion comment and close the active GitHub issue after verification.
