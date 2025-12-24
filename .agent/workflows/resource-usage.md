---
description: Static assets, media files, icons, fonts, and resource management guide
---

# Resource Usage Guide

Complete guide for managing static assets, media files, and resources in the project.

---

## Directory Structure

| Directory | Purpose | Example Files |
|-----------|---------|---------------|
| `static/` | Static assets (CSS, JS, images, fonts) | `static/css/style.css` |
| `static/img/` | Application images | `static/img/common/logo.png` |
| `static/js/` | JavaScript files | `static/js/main.js` |
| `static/css/` | Stylesheets | `static/css/colors.css` |
| `static/icons/` | Icon font files | `static/icons/bootstrap/` |
| `static/fonts/` | Custom fonts | `static/fonts/poppins/` |
| `media/` | User-uploaded & CMS images | `media/vehicles/car1.jpg` |

---

## Resource Classes

Resources are managed through the `R` object in [res/__init__.py](file:///d:/Dev/Python/CarRental/res/__init__.py):

### Files (`res/Files.py`)

Register CSS, JS, fonts, and icon files:

```python
class Files(utils.Files):
    css = utils.FileMaker(
        style='style',           # static/css/style.css
        admin='admin',           # static/css/admin.css
    )
    
    js = utils.FileMaker(
        main='main',             # static/js/main.js
        dataTable=('datatables.min', 1, 'util/vendor/tables/datatables'),
    )
    
    icon = utils.FileMaker(
        bootstrap='bootstrap/bootstrap-icons.min',
    )
```

### Images (`res/Images.py`)

Register commonly used images:

```python
class Images(utils.Images):
    common = utils.FileMaker(
        logo='common/logo',      # static/img/common/logo.png
        favicon='common/favicon',
    )
```

### Data (`res/Data.py`)

CMS settings and configuration data (fetched from database).

---

## Using Resources in Templates

```html
{% load static %}
{% load files %}

{# Static Images #}
<img src="{% static 'img/common/logo.png' %}" alt="Logo">

{# CSS Files #}
{% css R.files.css.style %}

{# JS Files #}
{% js R.files.js.main %}

{# Icon Fonts #}
{% icon R.files.icon.bootstrap %}

{# Font Files #}
{% font R.files.font.poppins %}

{# Registered Images #}
<img src="{{ R.images.common.logo }}" alt="Logo">
```

---

## Adding New Resources

### 1. Add Static Files

Place files in appropriate folders:
- CSS → `static/css/`
- JS → `static/js/`
- Images → `static/img/`
- Icons → `static/icons/`

### 2. Register in Files.py

```python
# In res/Files.py
css = utils.FileMaker(
    newStyle='path/to/your/style',
)
```

### 3. Include in Templates

```html
{% css R.files.css.newStyle %}
```

---

## Media Files

For user-uploaded or CMS-managed images:

```python
# In models
image = models.ImageField(upload_to='vehicles/')

# Creates: media/vehicles/filename.jpg
```

### Serving Media Files

Media files are served automatically in development. In templates:

```html
<img src="{{ vehicle.image.url }}" alt="{{ vehicle.name }}">
```

---

## Generating Images

You can generate images using AI and store them:

1. **Static Images** → `static/img/` (version controlled)
2. **Dynamic Images** → `media/` (user/CMS managed)

```bash
# Example: Hero background
static/img/common/hero-bg.webp

# Example: Vehicle image (CMS)
media/vehicles/toyota-prius.jpg
```

---

## Icon Fonts Available

| Icon Set | Class Prefix | Example |
|----------|--------------|---------|
| Bootstrap Icons | `bi bi-*` | `<i class="bi bi-car-front"></i>` |
| Phosphor Icons | `ph ph-*` | `<i class="ph ph-car"></i>` |
| Font Awesome | `fa fa-*` | `<i class="fa fa-car"></i>` |
| Icomoon | `icon-*` | `<i class="icon-car"></i>` |

---

## Best Practices

1. **Optimize Images**: Use WebP format, compress before adding
2. **Organize by Feature**: Group related images in subfolders
3. **Use FileMaker**: Always register files for easy reference
4. **Version Static**: Static assets are version-controlled
5. **Avoid Media for Static**: Don't use media/ for app images
