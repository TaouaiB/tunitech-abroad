# Privacy Final Review Checklist

Before public launch, verify the following privacy constraints:

- [ ] **CV Files Private**: `PRIVATE_MEDIA_ROOT` is strictly protected. PDF files are not directly accessible via Caddy, Nginx, or Whitenoise.
- [ ] **User Ownership Validation**: 
  - CV downloads check `request.user == cv.user`.
  - Saved jobs list is scoped to `request.user`.
  - Recommendations are scoped to `request.user`.
- [ ] **Soft Deletion**: `CVUpload.objects` filters out `is_deleted=True`. Soft-deleted CVs never appear in user lists.
- [ ] **Account Deletion Flow**: Users can delete their accounts. Deleting an account removes or anonymizes all associated PII, including hard-deleting the CV files from disk.
- [ ] **CV Deletion Flow**: Users can delete individual CVs.
- [ ] **Email Unsubscribe Flow**: All automated emails have a functional unsubscribe link.
- [ ] **Admin Access Security**: The Django admin and custom operations dashboard are accessible only to staff/superusers.
- [ ] **Log Hygiene**: Ensure Django error logs, Celery logs, and system journals do not dump:
  - Raw CV text or PII.
  - LLM raw prompts containing full CVs.
  - Real secrets, API keys, or access tokens.
  - Passwords or sensitive session IDs.
