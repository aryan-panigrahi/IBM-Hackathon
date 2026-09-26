# Data Privacy Policy v2.0

## Section 1: Logging Standards
1. Email addresses MUST NOT be written to application logs.
2. User identifiers MUST be hashed or redacted before logging.
3. Full names MUST NOT appear in debug or info-level logs.

## Section 2: Credential Management
4. API keys and secrets MUST NOT be hardcoded in source code.
5. Secrets MUST be loaded from environment variables or a secrets manager.
6. Authentication tokens MUST NOT be stored in plain text.

## Section 3: Data Storage
7. Personal data MUST NOT be stored in plain text test fixtures.
8. Database connection strings MUST NOT contain credentials.

## Section 4: Enforcement
Violations of this policy require immediate remediation before code merge.
All remediation must be validated by automated scanners.
