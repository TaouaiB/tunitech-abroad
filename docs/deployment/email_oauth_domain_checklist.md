# Email, OAuth, & Domain Checklist

Ensure all external integrations and domain-specific settings are correctly configured for production.

- [ ] **Production Domain Placeholders replaced**: Update standard placeholders (`your-domain.example`) to the actual domain (e.g., `tunitech-abroad.com`) in all environments.
- [ ] **`ALLOWED_HOSTS` configured**: Must contain exactly the production domains (e.g., `['tunitech-abroad.com', 'www.tunitech-abroad.com']`).
- [ ] **`CSRF_TRUSTED_ORIGINS` configured**: Must match `ALLOWED_HOSTS` with the `https://` prefix.
- [ ] **Google OAuth Callbacks**: Update the Google Cloud Console with the production redirect URIs (e.g., `https://tunitech-abroad.com/accounts/google/login/callback/`).
- [ ] **GitHub OAuth Callbacks**: Update GitHub Developer Settings with the production homepage URL and authorization callback URL.
- [ ] **Email Sender Setup**: Configure `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, and `DEFAULT_FROM_EMAIL` (e.g., `noreply@tunitech-abroad.com`) using a reliable transactional email provider (SendGrid, Mailgun, or standard SMTP).
- [ ] **Domain DNS / Authentication**: Verify SPF, DKIM, and DMARC records are set for the sending domain to ensure deliverability.
- [ ] **Unsubscribe URL Correctness**: Test that absolute URLs in emails generate correctly using the production domain.
- [ ] **No Real Secrets in Docs**: Ensure no actual OAuth client secrets or email passwords exist in this or any other repository documentation.
