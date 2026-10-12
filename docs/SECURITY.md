# Security Policy

**Current scope (2026-10-11):** This project is v0.8.0. The snapshots in
`SECURITY_AUDIT_2026.md` and `SECURITY_AUDIT_2026_02_17.md` are historical and do
not describe current route protections. See the root [README](../README.md) for
implemented session authentication, CSRF, ownership, and job limits. No VCN
deployment has been inspected or verified live.

## Supported Versions

| Version | Support status |
| ------- | -------------- |
| 0.8.x   | Current local release |

## Security Best Practices

### 1. Environment Variables

**CRITICAL: Never commit `.env` files to version control**

- ✅ Use `.env.example` as template
- ✅ Store actual secrets in `.env` (gitignored)
- ✅ Use strong, random SECRET_KEY in production
- ✅ Rotate API keys regularly

### 2. Production Deployment

Production requires named authentication and a strong random `SECRET_KEY`.
This app uses server-side sessions and CSRF protection; it does not use the JWT
setup shown in older snapshots. Keep secret values in ignored runtime
configuration and never paste them into documentation, source, or chat.

### 3. Dependencies

Keep all dependencies updated:

```bash
pip install -U pip
pip install -U -r requirements.txt
```

Run security audit:

```bash
pip install safety
safety check
```

### 4. Rate Limiting

Enable rate limiting in production:

```python
ENABLE_RATE_LIMITING=True
RATE_LIMIT_PER_MINUTE=60
```

### 5. HTTPS/SSL

Always use HTTPS in production. Configure Flask-Talisman:

```python
from flask_talisman import Talisman
Talisman(app, force_https=True)
```

## Reporting a Vulnerability

If you discover a security vulnerability, please email:

**security@ceo-agent-system.example.com** (replace with actual contact)

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if available)

### Response Time

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depending on severity
  - Critical: 24-48 hours
  - High: 1 week
  - Medium: 2 weeks
  - Low: 1 month

## Security Checklist for Deployment

- [ ] Strong SECRET_KEY set (min 32 characters)
- [ ] DEBUG=False in production
- [ ] HTTPS/SSL configured
- [ ] Rate limiting enabled
- [ ] Authentication enabled
- [ ] Input validation on all endpoints
- [ ] SQL injection protection (parameterized queries)
- [ ] XSS protection (input sanitization)
- [ ] CSRF protection enabled
- [ ] Secure headers configured
- [ ] Regular dependency updates
- [ ] Security audit completed
- [ ] Backup strategy implemented
- [ ] Monitoring and logging configured
- [ ] Incident response plan documented

## Known Security Features

### Input Validation

- Pydantic models for data validation
- XSS prevention via input sanitization
- Schema validation for all API requests

### Error Handling

- Centralized exception handling
- No sensitive data in error messages
- Comprehensive logging for audit trails

### Authentication & Authorization

- Named accounts with admin/reviewer roles; no API-key bypass or public registration.
- Server-side sessions and account revocation; state changes require CSRF.
- Development with auth disabled is restricted to localhost. Production refuses
  startup when authentication is disabled.

### Data Protection

- Encrypted environment variables support
- No hard-coded secrets
- Sensitive data excluded from logs

## Compliance

This project follows:

- OWASP Top 10 security practices
- CWE/SANS Top 25 Most Dangerous Software Errors
- Flask security best practices
