# Phase 1: Dashboard Settings & API Key Authentication

## Overview
This phase establishes the foundational security and user interface for generating, inspecting, rotating, and validating API keys. Only **Staff** (`is_staff=True`) and **Superadmin** (`is_superuser=True`) users can access these capabilities.

---

## 1. Database Model: `ApiKey`

### Location: `authentication/models/ApiKey.py`
The `ApiKey` model represents a personal API credential associated with a User. To maintain strict security:
- **Plaintext keys are never stored in the database.**
- Keys are stored as a **SHA-256 cryptographic hash** (`key_hash`).
- A prefix (e.g. `biom_live_a1b2...`) is retained (`key_prefix`) so users can recognize which key is active on their dashboard.

```python
import hashlib
import secrets
from django.db import models
from django.utils import timezone
from authentication.models import User

class ApiKey(models.Model):
    PREFIX = 'biom_live_'
    
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='api_keys', verbose_name='User'
    )
    name = models.CharField(max_length=100, default='Default API Key', verbose_name='Key Name')
    key_prefix = models.CharField(max_length=16, verbose_name='Key Prefix')
    key_hash = models.CharField(max_length=64, unique=True, db_index=True, verbose_name='Key Hash')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    last_used_at = models.DateTimeField(null=True, blank=True, verbose_name='Last Used At')
    revoked_at = models.DateTimeField(null=True, blank=True, verbose_name='Revoked At')
    is_active = models.BooleanField(default=True, verbose_name='Is Active')

    class Meta:
        verbose_name = 'API Key'
        verbose_name_plural = 'API Keys'
        ordering = ['-created_at']

    @classmethod
    def generate_token(cls) -> tuple[str, str, str]:
        """
        Returns (raw_key, key_prefix, key_hash).
        Format: biom_live_<32 hex chars>
        """
        random_part = secrets.token_hex(16)
        raw_key = f"{cls.PREFIX}{random_part}"
        key_prefix = raw_key[:14] + '...'
        key_hash = hashlib.sha256(raw_key.encode('utf-8')).hexdigest()
        return raw_key, key_prefix, key_hash

    @classmethod
    def create_for_user(cls, user: User, name: str = 'Default API Key') -> tuple['ApiKey', str]:
        """Deactivates any previous active keys and generates a new one."""
        cls.objects.filter(user=user, is_active=True).update(
            is_active=False, revoked_at=timezone.now()
        )
        raw_key, key_prefix, key_hash = cls.generate_token()
        instance = cls.objects.create(
            user=user,
            name=name,
            key_prefix=key_prefix,
            key_hash=key_hash,
            is_active=True
        )
        return instance, raw_key
```

### Migration Plan
- Generate migration `0003_apikey.py` inside `authentication/migrations/` using `python main.py makemigrations authentication`.
- Execute migration via `python main.py migrate`.

---

## 2. Authentication Layer

### Location: `authentication/auth/ApiKeyAuthentication.py`
A custom Django REST Framework authentication provider:
1. Inspects request headers:
   - `X-API-Key: <token>` (primary)
   - `Authorization: Bearer biom_live_...`
   - `Authorization: Api-Key biom_live_...`
2. Hashes incoming raw token using SHA-256.
3. Looks up active record in `ApiKey`:
   ```python
   api_key = ApiKey.objects.select_related('user').filter(
       key_hash=incoming_hash,
       is_active=True,
       revoked_at__isnull=True
   ).first()
   ```
4. Verifies `user.is_active` and (`user.is_staff` or `user.is_superuser`).
5. Updates `api_key.last_used_at = timezone.now()` asynchronously / throttled.
6. Returns `(api_key.user, api_key)`.

### Settings Integration: `core/settings.py`
Register `authentication.auth.ApiKeyAuthentication` in `REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']`.

### Middleware: `authentication/middleware.py`
A lightweight Django middleware (`ApiKeyMiddleware`) to authenticate incoming requests on non-DRF views if header is present, ensuring `request.user` is properly attached across all pipeline stages.

---

## 3. Web Dashboard Settings View

### Location: `admins/views/SettingsView.py`
Mapped to `dashboard/settings`:
- `@GetMapping('/')` with `@Authenticated(staff=True)`:
  - Fetches existing active `ApiKey` for `request.user`.
  - Displays masked prefix (`biom_live_a1b2...`), creation date, and last used date.
  - Renders `admins/templates/dashboard/settings.html`.
- `@PostMapping('/api-key/generate')`:
  - Generates or rotates key for `request.user`.
  - Revokes old key automatically.
  - Returns JSON with `raw_key`, `key_prefix`, `created_at`.
- `@PostMapping('/api-key/revoke')`:
  - Revokes active key, marking `is_active=False` and `revoked_at=now()`.

### Template: `admins/templates/dashboard/settings.html`
Designed with Limitless theme guidelines:
- **Card**: Dark/Light mode theme compliant using CSS variables (`var(--card-bg)`, `var(--card-border)`).
- **Status Indicator**: Green pill badge for "Active", Muted badge for "No Active Key".
- **Details Row**:
  - Masked Key display with mono-font badge.
  - "Created on" and "Last used" timestamps.
- **Action Buttons**:
  - `Generate Key` / `Regenerate / Rotate Key` button.
  - `Revoke Key` button.
- **One-Time Key Modal**:
  - Triggered immediately upon generation/rotation.
  - Displays full plaintext token.
  - One-click "Copy to Clipboard" button with icon state change.
  - Security warning banner: *"Make sure to copy your API key now as you won't be able to see it again."*
  - Quick-start code snippet for Jupyter Notebook & Google Colab.
- **Rotation Confirmation Modal**:
  - Warning: *"Rotating your API key will immediately invalidate your existing key. Any active scripts, notebooks, or pipelines using the old key will stop working."*

### Navigation Updates
1. **Sidebar (`res/Data.py`)**:
   Add a "Settings" entry to `R.data.aside['admin'].content['main']` or a new section `system` with icon `ph-gear` or `bi-gear-fill`.
2. **User Dropdown (`admins/templates/admin_includes/navigator.html`)**:
   Update dropdown menu to include direct link to `Settings`:
   ```html
   <a href="{% url 'dashboard/settings' %}" class="dropdown-item">
       <i class="ph-gear me-2"></i>
       Settings & API Keys
   </a>
   ```

---

## 4. Acceptance Criteria for Phase 1
- [x] Staff and superadmin users can access `/dashboard/settings`.
- [x] Non-staff / unauthorized users receive 403 or redirect to login.
- [x] Key can be generated and plaintext is shown once.
- [x] Key can be rotated: old key is deactivated immediately, new key works.
- [x] Key can be revoked.
- [x] Requests sent with `X-API-Key: <key>` authenticate correctly in DRF endpoints.
- [x] Database records store only hashes, never plaintext keys.
