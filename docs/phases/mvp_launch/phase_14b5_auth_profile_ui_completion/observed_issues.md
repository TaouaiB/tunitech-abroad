# Observed Manual QA Issues

Baha manually found these after Phase 14B.3R / Phase 14B.4 attempts:

1. `/accounts/3rdparty/` has no design.
2. `/accounts/password/set/` has no design.
3. Some allauth pages are only discovered after clicking; this means the previous agent did not audit all pages.
4. Clicking GitHub login may silently use the current GitHub browser session and return to the existing profile without explaining the state.
5. User wants a way to connect Google later if account started with GitHub, and connect GitHub later if account started with Google.
6. OAuth signup did not populate provider data into profile reliably.
7. OAuth signup did not capture/show avatar/photo.
8. OAuth-created users need a visible set-password option in account settings.
9. CV parsing still only captured some fields for new account testing.
10. `target_country` was set/displayed as France, but MVP is France-only and should not ask/show target country now.
11. Recommendations page says missing fields that appear already filled elsewhere.
12. Profile page says missing fields that are not actually missing.
13. Auth email text still says `example.test` and sends confusing duplicate-account/password-reset text.
14. Email subject/content says confirmation but may contain no confirmation link in some duplicate-account cases.
15. User expects all pages to be styled proactively, not only after discovery.
