---
description: Vvecon Zorion - Custom Django MVC framework with decorators, services, and utilities
---

# Vvecon Zorion Framework

Custom Django-based framework providing MVC patterns, decorators, and utilities for rapid development.

> [!CAUTION]
> **DO NOT** modify any files in `./vvecon/zorion/` without explicit user supervision, even with auto-run permissions.

---

## Framework Location

```
./vvecon/zorion/
├── views/          # View, API base classes
├── db/             # Model utilities
├── serializers/    # Request/Response handling
├── auth/           # JWT, permissions
├── utils/          # Utilities, data classes
├── templatetags/   # Custom template tags
└── app/            # Django settings
```

---

## Core Components

### Views

Use `View` for HTML pages and `API` for REST endpoints:

```python
from vvecon.zorion.views import View, API, GetMapping, PostMapping, Mapping

# HTML View
@Mapping()
class HomeView(View):
    R: R = R()
    
    @GetMapping()
    def home(self, request):
        return self.render(request, context={}, template='home')

# REST API
@Mapping('api/v1/cars')
class V1Cars(API):
    
    @GetMapping()
    def list(self, request):
        return Return.ok(data)
    
    @PostMapping()
    def create(self, request, data: CarRequest):
        return Return.created(result)
```

### Route Decorators

| Decorator | HTTP Method | Usage |
|-----------|-------------|-------|
| `@GetMapping('path')` | GET | Fetch data |
| `@PostMapping('path')` | POST | Create data |
| `@PutMapping('path')` | PUT | Update data |
| `@DeleteMapping('path')` | DELETE | Remove data |
| `@Mapping('base')` | - | Set base URL |

---

## Services

Services handle business logic and database operations:

```python
from vvecon.zorion.core import Service

class VehicleService(Service):
    model = Vehicle
    searchableFields = ('name', 'brand__name')
    filterableFields = ('category', 'price')
    
    def getAvailable(self):
        return self.model.objects.filter(status='available')
```

Built-in methods: `getAll()`, `getById()`, `create()`, `update()`, `delete()`, `filter()`

---

## Serializers

### Request Serializers

```python
from vvecon.zorion import serializers

class CarRequest(serializers.Request):
    name = serializers.CharField(max_length=100)
    price = serializers.FloatField()
```

### Response Serializers

```python
class CarResponse(serializers.Response):
    id = serializers.IntegerField()
    name = serializers.CharField()
    price = serializers.FloatField()
```

### Model Responses

```python
class CarResponse(serializers.ModelResponse):
    model = Car
    fields = ('id', 'name', 'price', 'image')
```

---

## Data Classes

Located in `vvecon/zorion/utils/Data.py`:

```python
@dataclass
class Navigator:
    enabled: bool = True
    navigatorType: int = 1
    activeTab: str = 'home'

@dataclass
class Footer:
    enabled: bool = True
    footerType: int = 1
    social: dict = None
```

Used in `res/Data.py` for site configuration.

---

## Return Utilities

Standard API responses:

```python
from vvecon.zorion.serializers import Return

Return.ok(data)           # 200 OK
Return.created(data)      # 201 Created
Return.badRequest(msg)    # 400 Bad Request
Return.notFound(msg)      # 404 Not Found
Return.forbidden(msg)     # 403 Forbidden
```

---

## Template Tags

Custom tags in `vvecon/zorion/templatetags/`:

```html
{% load files %}
{% load util %}

{# Include CSS/JS/Icons #}
{% css R.files.css.style %}
{% js R.files.js.main %}
{% icon R.files.icon.bootstrap %}

{# JSON serialization #}
{{ data|jsonify }}
{{ queryset|toJson }}
```

---

## Authentication

JWT authentication with `JWTProvider`:

```python
from vvecon.zorion.auth import JWTProvider

tokens = JWTProvider().generateTokens(user)
# Returns: {'token': '...', 'refresh': '...'}
```

---

## R (Resources) Object

Central resource accessor passed to all templates:

```python
from res import R

class MyView(View):
    R: R = R()
    
    def home(self, request):
        # Access settings
        self.R.data.navigator.site1.enabled = True
        
        # Access images
        logo = self.R.images.common.logo
        
        return self.render(request, {}, 'home')
```

In templates: `{{ R.data.settings.site1.app_name }}`

---

## Key Files

| File | Purpose |
|------|---------|
| [views/View.py](file:///d:/Dev/Python/CarRental/vvecon/zorion/views/View.py) | HTML view base class |
| [views/API.py](file:///d:/Dev/Python/CarRental/vvecon/zorion/views/API.py) | REST API base class |
| [core/Service.py](file:///d:/Dev/Python/CarRental/vvecon/zorion/core/Service.py) | Service layer base |
| [serializers/Response.py](file:///d:/Dev/Python/CarRental/vvecon/zorion/serializers/Response.py) | Response utilities |
| [utils/Data.py](file:///d:/Dev/Python/CarRental/vvecon/zorion/utils/Data.py) | Data classes |

---

## Best Practices

1. **Use Framework Classes**: Always extend `View`, `API`, `Service`
2. **Follow Patterns**: Use decorators for routes, services for logic
3. **Don't Modify**: Never change framework code without supervision
4. **Type Hints**: Use request/response serializers for validation
5. **R Object**: Access all resources through `R` for consistency