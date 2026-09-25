# Privacy & Data Governance Policy (POL-GDPR)

1. **Email Logging Prohibition**: User email addresses must not be written to logs in plaintext.
2. **PII Masking**: Personal identifiers (emails, phone numbers, SSNs, credit cards) must be masked with `mask_email()` or redacted prior to recording in logs or stdout.
3. **Secret Isolation**: Secrets, tokens, and private keys must never be hardcoded in application sources.
4. **Environment Variables**: All API credentials must be fetched dynamically from environment variables (`os.getenv`).
5. **Test Data Minimization**: Plaintext personal data must not be stored in test fixtures.
