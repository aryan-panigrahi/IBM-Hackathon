# Security & Resilience Policy (POL-SEC)

1. **Unbounded Loop Prohibition**: Retry loops without finite upper bounds or exponential backoffs are strictly prohibited.
2. **SAST Cleanliness**: Code must produce 0 HIGH severity findings when scanned with Bandit.
3. **No Dynamic Code Execution**: `eval()` and `exec()` on untrusted input are strictly forbidden.
4. **Subprocess Sanitization**: Never invoke `subprocess` with `shell=True` on dynamic user input.
5. **Human-in-the-Loop Gate**: All authentication, payment gateway, and cryptography changes require explicit human sign-off before merge.
