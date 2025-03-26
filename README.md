Secured Student Information Management System (SIMS) 🚀

A Django-based web application for managing student data securely. It provides role-based authentication, student enrollment, fee payment, and academic record management while ensuring strong security features like HTTPS, CSRF protection, and penetration testing.

🔹 Features

✅ Student Management: Enrollment, fee payment, and course registration.
✅ Role-Based Access Control (RBAC): Different roles for students, instructors, and admins.
✅ Secure Authentication: Password hashing using Django’s built-in authentication.
✅ Assignment & Quiz System: Submission and evaluation for academic activities.
✅ Secure Email Notifications: Alerts for assignments, payments, and announcements.
✅ Security Features: HTTPS, CSRF protection, session timeout, and penetration testing.
✅ Logging & Monitoring: Basic logging setup for security monitoring.

🔹 Tech Stack
Backend: Python, Django, SQLite
Frontend: HTML, CSS, JavaScript
Security: SSL, RBAC, CSRF Protection, Session Timeout
Penetration Testing: OWASP ZAP, Nikto

🔹 SSL Setup (HTTPS) Using PowerShell
**Check Chocolatey Installation**
Set-ExecutionPolicy Bypass -Scope Process -Force
choco -v

**Install mkcert**
choco install mkcert

**Generate Local SSL Certificate**
mkcert -install
mkcert localhost

**Configure Django for HTTPS (Add in settings.py):**
SECURE_SSL_REDIRECT = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

🔹 Security Hardening Guide
To enhance the security of your Django application, implement the following:

**Time-out-session Implementation**
SESSION_EXPIRE_AT_BROWSER_CLOSE = TRUE
SESSION_COOKIE_AGE = 300
SESSION_SAVE_EVERY_REQUEST = TRUE
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

**Enable Clickjacking Protection**
X_FRAME_OPTIONS = 'Deny'

**Prevent Cross-Site-Scripting (XSS)**
SECURE_BROWSER_XSS_FILTER = TRUE
