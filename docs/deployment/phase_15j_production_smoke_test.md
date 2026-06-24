# Production Smoke Test

After deploying:
1. Load `https://tunitech-abroad.com` - Should return 200 OK.
2. Check admin panel `https://tunitech-abroad.com/admin/` - Should prompt for login.
3. Attempt to visit an imaginary media URL `https://tunitech-abroad.com/media/cvs/test.pdf` - Must return 404 from Django, NOT Caddy, confirming no direct exposure.
4. Run `sudo systemctl status gunicorn celery` - Check for active/running states.
