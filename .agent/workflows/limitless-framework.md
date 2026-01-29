---
description: Limitless Admin Dashboard Framework - Premium UI components and templates for the admin panel
---

# Limitless Admin Dashboard Framework

Reference framework for building the **admin dashboard UI** in the `admins` app. This is a premium Bootstrap-based admin template used for design reference only.

## Directory Structure

| Location | Purpose |
|----------|---------|
| `./limitless/` | Root folder of the Limitless template |
| `./limitless/demo/html/layout_1/full/` | Main HTML templates for reference |
| `./static/css/` | Project CSS files (extracted from Limitless) |
| `./static/js/util/` | Project JS utilities (extracted from Limitless) |
| `./static/icons/` | Icon fonts (Bootstrap Icons, Phosphor, etc.) |

---

## Important Rules

> [!CAUTION]
> **DO NOT** link any file directly from the `limitless/` folder to the project. This folder is **reference only**.

> [!IMPORTANT]
> All required assets must be copied to `static/` folder and registered in `res/Files.py`.

---

## Including Assets

Assets are managed through the `R` (Resources) object in [Files.py](file:///d:/Dev/Python/CarRental/res/Files.py):

```python
# In res/Files.py
class Files(utils.Files):
    css = utils.FileMaker(
        admin='admin',  # static/css/admin.css
    )
    
    js = utils.FileMaker(
        dataTable=('datatables.min', 1, 'util/vendor/tables/datatables'),
    )
    
    icon = utils.FileMaker(
        bootstrap='bootstrap/bootstrap-icons.min',
        phosphor='phosphor/styles.min',
    )
```

In templates, use the template tags:

```html
{% load files %}

{# Include CSS #}
{% css R.files.css.admin %}

{# Include JS #}
{% js R.files.js.dataTable %}

{# Include Icon fonts #}
{% icon R.files.icon.bootstrap %}
```

---

## Theme Support (Light/Dark)

All dashboard UI **must** support both light and dark themes. Theme handling:

1. **CSS Variables**: Defined in admin `header.html`
2. **Data Attribute**: `data-theme="light"` or `data-theme="dark"` on `<html>`
3. **Color Theme**: `data-color-theme` for accent colors

```html
<html data-theme="dark" data-color-theme="blue">
```

---

## Component Usage with Django Cotton

Use [django-cotton](https://github.com/wrabit/django-cotton) for reusable UI components:

```html
{# Create component in admins/templates/cotton/card.html #}
<div class="card">
    <div class="card-header">{{ title }}</div>
    <div class="card-body">{{ slot }}</div>
</div>

{# Use in templates #}
<c-card title="Dashboard">
    <p>Card content here</p>
</c-card>
```

---

## Key Limitless UI Components

| Component | Location in Limitless | Usage |
|-----------|----------------------|-------|
| Cards | `components_cards.html` | Data display containers |
| DataTables | `datatable_*.html` | Data listing with pagination |
| Forms | `form_layouts.html` | Input forms with validation |
| Modals | `components_modals.html` | Popup dialogs |
| Alerts | `components_notifications.html` | Sweet Alert notifications |
| Sidebar | `layout_1/full/index.html` | Admin aside navigation |

---

## Admin Templates Structure

```
admins/templates/
├── admin_base.html         # Base template with sidebar
├── admin_includes/
│   ├── header.html         # CSS, theme vars, meta
│   ├── navigator.html      # Top navbar
│   ├── aside.html          # Sidebar navigation
│   └── footer.html         # Scripts, utilities
├── admin/
│   ├── dashboard.html      # Main dashboard
│   ├── car-rental.html     # Car rental bookings
│   └── ...
└── cotton/                 # Reusable components
```

---

## Best Practices

1. **Consistency**: Match Limitless styling exactly
2. **Responsiveness**: All UIs must be mobile-friendly
3. **Accessibility**: Use proper ARIA labels
4. **Performance**: Lazy-load DataTables, use pagination
5. **Theme**: Test all UI in both light and dark modes