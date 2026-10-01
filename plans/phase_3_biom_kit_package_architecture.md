# Phase 3: `biom-kit` Python Package Architecture & Premade Tools

## Overview
This phase details the architecture and implementation of the **`biom-kit`** client package. Designed specifically for Google Colab, Jupyter Notebooks, and Python data pipelines, it abstracts the underlying HTTP API and gives data scientists an intuitive interface for data discovery, type-aware filtering, data cleaning, statistical analysis, and publication-quality visualization.

---

## 1. Package Configuration & Setup

### Directory: `d:\Dev\Python\BIOM\biom-kit`
The package is structured following modern Python packaging standards (PEP 517 / PEP 621) using `hatchling`:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "biom-kit"
version = "0.1.0"
description = "Intuitive Python client and data science toolkit for the BIOM platform"
readme = "README.md"
license = { file = "LICENSE" }
requires-python = ">=3.9"
dependencies = [
    "requests>=2.28.0",
    "pandas>=1.5.0",
    "matplotlib>=3.6.0",
    "seaborn>=0.12.0",
    "tabulate>=0.9.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "responses>=0.23.0"
]
plotly = [
    "plotly>=5.14.0"
]

[tool.hatch.build.targets.wheel]
packages = ["src/biom"]
```

### Installation Options
- Direct pip install: `pip install biom-kit`
- Direct from repository / Colab: `pip install git+https://github.com/Sasindu99-ai/BIOM.git#subdirectory=biom-kit`
- Local development install: `pip install -e ./biom-kit`

---

## 2. Directory Structure

```
biom-kit/
├── pyproject.toml
├── README.md
├── LICENSE
├── src/
│   └── biom/
│       ├── __init__.py           # Top-level exports: login, datasets, fields, variables, query, F, Dataset, tools
│       ├── config.py             # Config & Environment Variables (BIOM_API_KEY, BIOM_BASE_URL)
│       ├── client.py             # BiomClient HTTP communication, session, header management
│       ├── exceptions.py         # BiomError, BiomAuthError, BiomFilterError, BiomNotFoundError
│       ├── discovery.py          # Schema inspection: fields(), datasets(), variables(), search_variables()
│       ├── query.py              # Query, F expressions, filter compiler, pagination
│       ├── dataset.py            # Dataset wrapper with fluent chaining (.filter().to_dataframe())
│       ├── models.py             # Schema containers (FieldInfo, VariableInfo, DatasetInfo)
│       └── tools/
│           ├── __init__.py       # Tools entrypoint (biom.tools)
│           ├── cleaning.py       # clean_dataset, impute_missing, detect_outliers, summarize_health
│           ├── analysis.py       # summarize, correlation_matrix, distribution_stats, group_summary
│           └── plotting.py       # plot_distribution, plot_correlation_matrix, plot_comparison, plot_missingness
└── tests/
    ├── conftest.py
    ├── test_client.py
    ├── test_discovery.py
    ├── test_query_builder.py
    ├── test_cleaning.py
    ├── test_analysis.py
    └── test_plotting.py
```

---

## 3. Core User Experience (UX) Flow

### 3.1 Authentication
```python
import biom

# Option 1: Direct login in notebook/script (defaults to https://biom.arceion.com)
biom.login(api_key="biom_live_a1b2c3d4...")

# Option 2: Environment variables (automatically detected)
# os.environ["BIOM_API_KEY"] = "biom_live_..."
# os.environ["BIOM_BASE_URL"] = "https://biom.arceion.com"
```

---

### 3.2 Discovery: Exploring Fields and Datasets
When a user does not know what variables exist or what operators they support:

```python
# 1. Discover all patient profile variables
fields = biom.fields()
# In Jupyter/Colab, displays as an interactive DataFrame:
# | key         | label        | type   | operators                                              |
# | patientId   | Patient ID   | NUMBER | equals, gt, gte, lt, lte, between, is_empty...        |
# | age         | Age          | NUMBER | equals, gt, gte, lt, lte, between...                  |
# | gender      | Gender       | TEXT   | equals, contains, is_empty...                          |

# 2. List available datasets
datasets = biom.datasets()
# Displays: id, name, category, records, variables, createdAt

# 3. Inspect dataset variables
variables = biom.variables(dataset=1)  # by ID or by name "Cardiovascular Cohort"
# Displays: name, type, field, operators, notes (e.g. units: mg/dL)

# 4. Search variables across all datasets
results = biom.search_variables("glucose")
```

---

### 3.3 Intuitive Data Filtering & Extraction

#### Style A: Fluent Method Chaining
```python
# Fluent, Django-like query syntax
df = (
    biom.dataset(1)
    .filter(age__gte=18, age__lte=65)
    .filter(gender="Female")
    .filter("Fasting Glucose", gt=100)
    .filter(testedDate__between=("2024-01-01", "2024-12-31"))
    .sort_by("age", ascending=True)
    .to_dataframe()
)
```

#### Style B: Declarative `F` Expressions
```python
from biom import F

df = biom.query(
    dataset=1,
    filters=[
        F("age") >= 18,
        F("age") <= 65,
        F("gender") == "Female",
        F("Fasting Glucose") > 100,
        F("testedDate").between("2024-01-01", "2024-12-31"),
    ],
).to_dataframe()
```

#### Style C: Multi-Dataset Harmonized Querying
```python
df = biom.query(
    datasets=[1, 2],
    filters=[
        F("age") >= 40,
        F("Hypertension") == True
    ]
).to_dataframe()
```

---

## 4. Premade Tools Suite (`biom.tools`)

### 4.1 Cleaning Tools (`biom.tools.cleaning`)
- **`clean_dataset(df, ...)`**:
  - Automatically identifies and converts numeric strings to numeric types (`pd.to_numeric`).
  - Converts ISO date strings to proper `datetime64[ns]` objects.
  - Strips extraneous whitespace from categorical text fields.
  - Standardizes boolean columns (`True`/`False`/`None`).
  - Optionally removes completely empty columns or rows.
- **`summarize_health(df)`**:
  - Computes missingness percentage per column.
  - Identifies duplicate patient references.
  - Summarizes column types and memory usage.
- **`detect_outliers(df, columns=None, method='iqr')`**:
  - Flags rows with biomarker values beyond $Q_1 - 1.5 \times \text{IQR}$ or $Q_3 + 1.5 \times \text{IQR}$.
- **`impute_missing(df, columns=None, strategy='median')`**:
  - Imputes missing continuous data using `median`/`mean` or categorical with `mode`.

---

### 4.2 Analysis Tools (`biom.tools.analysis`)
- **`summarize(df, columns=None)`**:
  - Produces enhanced summary statistics: count, missing, mean, std, median, IQR, skewness, min, max.
- **`correlation_matrix(df, columns=None, method='pearson')`**:
  - Extracts numeric biomarkers and patient variables (age, etc.) and computes correlation matrix.
- **`group_summary(df, group_by='gender', metrics=['mean', 'std', 'median'])`**:
  - Aggregates biomarkers across demographic cohorts.
- **`compare_groups(df, group_col, value_col)`**:
  - Performs 2-sample t-test / Mann-Whitney U or ANOVA across patient subgroups.

---

### 4.3 Plotting Tools (`biom.tools.plotting`)
Built with modern styling (Seaborn / Matplotlib styling, crisp DPI, high aesthetic palette):
- **`plot_distribution(df, column, hue=None, kde=True)`**:
  - Beautiful histogram with density estimate and quartile lines.
- **`plot_correlation_matrix(df, columns=None, annot=True)`**:
  - Professional heatmap showing correlation coefficients with masked upper triangle.
- **`plot_comparison(df, category_col, value_col, kind='box')`**:
  - Box plot / violin plot with overlaid jitter points for comparing biomarkers across patient cohorts.
- **`plot_missingness(df)`**:
  - Visual matrix and bar chart showing pattern of missing data across variables.
- **`plot_time_series(df, date_col, value_col, group_by=None)`**:
  - Longitudinal trend plot of biomarker values over time.

---

## 5. Acceptance Criteria for Phase 3
- [x] Package installable via `pip` into a fresh Python environment.
- [x] Clear error messages if API key is missing or invalid.
- [x] `biom.fields()` and `biom.variables()` return easy-to-read tables with operator hints.
- [x] Queries support numeric, text, date, and boolean operators.
- [x] Results directly convert to `pd.DataFrame`.
- [x] Cleaning, analysis, and plotting tools execute cleanly without crashes.
