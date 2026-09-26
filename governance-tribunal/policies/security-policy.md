# Security Policy v1.5

## Section 1: Code Safety
1. Do NOT use eval() or exec() on untrusted input.
2. Do NOT disable SSL/TLS certificate verification.
3. Do NOT execute shell commands with unescaped user input.
4. Do NOT use pickle for deserialization of untrusted data.

## Section 2: Authentication
5. All authentication-related code changes require human review.
6. Session tokens must have expiration.
7. Failed login attempts must be rate-limited.

## Section 3: Dependencies
8. Dependencies MUST NOT have known critical CVEs.
9. GPL-licensed dependencies are NOT approved for server-side distribution.
10. New dependencies require license review.

## Section 4: Enforcement
Security violations are classified as HIGH severity.
Human approval is mandatory before merging security-related patches.
