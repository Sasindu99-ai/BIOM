# Phase 2: BIOM Backend Discovery & Query Engine API

## Overview
This phase provides the secured REST API surface consumed by `biom-kit`. The user does not need to construct raw HTTP URLs directly—`biom-kit` wraps these endpoints transparently. The API endpoints provide self-describing metadata (discovery) and type-aware filtering and data extraction.

---

## 1. API Controller: `V1Kit`

### Location: `main/views/V1Kit.py`
Mapped to `api/v1/kit/`:
All endpoints require authentication via `@Authorized(True, permissions=['main.view_study'])`.

```python
from vvecon.zorion.auth import Authorized
from vvecon.zorion.serializers import Return
from vvecon.zorion.views import API, GetMapping, Mapping, PostMapping
from main.services import StudyService, PatientService

@Mapping('api/v1/kit')
class V1Kit(API):
    studyService: StudyService = StudyService()
    patientService: PatientService = PatientService()
```

---

## 2. Discovery Endpoints Specification

### 2.1 Credentials Verification & Ping
- **Endpoint**: `GET /api/v1/kit/auth/verify`
- **Purpose**: Verify that the provided API key is valid and retrieve the authenticated user profile and permissions.
- **Response**:
  ```json
  {
    "status": "success",
    "user": {
      "id": 12,
      "username": "dr_smith",
      "fullName": "Dr. Alice Smith",
      "isStaff": true,
      "isSuperuser": false
    }
  }
  ```

---

### 2.2 Patient / Profile Variables Discovery
- **Endpoint**: `GET /api/v1/kit/fields`
- **Purpose**: Return the full schema of filterable patient profile fields (known fields) with data types, human-readable labels, and supported operators.
- **Response**:
  ```json
  {
    "fields": [
      {
        "key": "patientId",
        "label": "Patient ID",
        "type": "NUMBER",
        "operators": ["equals", "gt", "gte", "lt", "lte", "between", "is_empty", "is_not_empty"],
        "description": "Unique system patient identifier"
      },
      {
        "key": "age",
        "label": "Age",
        "type": "NUMBER",
        "operators": ["equals", "gt", "gte", "lt", "lte", "between", "is_empty", "is_not_empty"],
        "description": "Calculated patient age in years"
      },
      {
        "key": "gender",
        "label": "Gender",
        "type": "TEXT",
        "operators": ["equals", "contains", "is_empty", "is_not_empty"],
        "choices": ["MALE", "FEMALE", "OTHER", "PREFER_NOT_TO_SAY"],
        "description": "Patient biological sex / gender"
      },
      {
        "key": "dateOfBirth",
        "label": "Date of Birth",
        "type": "DATE",
        "operators": ["equals", "before", "after", "between", "is_empty", "is_not_empty"]
      },
      {
        "key": "testedDate",
        "label": "Tested Date",
        "type": "DATE",
        "operators": ["equals", "before", "after", "between", "is_empty", "is_not_empty"]
      }
    ]
  }
  ```

---

### 2.3 Datasets Discovery
- **Endpoint**: `GET /api/v1/kit/datasets`
- **Purpose**: Return the catalog of available datasets (studies) with summary statistics.
- **Response**:
  ```json
  {
    "datasets": [
      {
        "id": 1,
        "name": "Cardiovascular Health Cohort 2024",
        "reference": "CV-2024-A",
        "category": "OBSERVATIONAL",
        "status": "ACTIVE",
        "version": 2,
        "recordCount": 1420,
        "variableCount": 38,
        "createdAt": "2024-03-15T08:30:00Z"
      }
    ]
  }
  ```

---

### 2.4 Dataset Variables Discovery
- **Endpoint**: `GET /api/v1/kit/datasets/<int:dataset_id>/variables`
- **Purpose**: Return all variables defined inside a specific dataset, their types, and applicable filtering operators.
- **Response**:
  ```json
  {
    "dataset": {
      "id": 1,
      "name": "Cardiovascular Health Cohort 2024"
    },
    "variables": [
      {
        "id": 105,
        "name": "Fasting Glucose",
        "type": "NUMBER",
        "field": "NUMBER",
        "isRange": false,
        "isSearchable": true,
        "operators": ["equals", "gt", "gte", "lt", "lte", "between", "is_empty", "is_not_empty"],
        "notes": "mg/dL"
      },
      {
        "id": 106,
        "name": "Hypertension Diagnosis",
        "type": "BOOLEAN",
        "field": "BOOLEAN",
        "operators": ["equals", "is_empty", "is_not_empty"]
      }
    ]
  }
  ```

---

### 2.5 Cross-Dataset Variable Search
- **Endpoint**: `GET /api/v1/kit/variables/search?q=<query>&datasets=<optional_ids>`
- **Purpose**: Search for variable names across all or selected datasets.

---

## 3. Query & Data Extraction Endpoint

### Endpoint: `POST /api/v1/kit/query`
- **Purpose**: Execute filtered queries across one or multiple datasets with type-aware rules and return a clean, flat table format optimized for conversion to a pandas `DataFrame`.

### Request Payload:
```json
{
  "dataset": 1,
  "datasets": [1, 2],
  "filters": [
    {
      "field": "age",
      "operator": "gte",
      "value": 18,
      "scope": "known"
    },
    {
      "field": "gender",
      "operator": "equals",
      "value": "Female",
      "scope": "known"
    },
    {
      "field": "Fasting Glucose",
      "operator": "gt",
      "value": 100,
      "scope": "variable"
    },
    {
      "field": "testedDate",
      "operator": "between",
      "value": "2024-01-01",
      "valueTo": "2024-12-31",
      "scope": "known"
    }
  ],
  "filterLogic": "AND",
  "fields": ["patientId", "reference", "age", "gender", "Fasting Glucose", "testedDate"],
  "sortField": "age",
  "sortDirection": "asc",
  "limit": 5000,
  "page": 1
}
```

### Response Format:
```json
{
  "status": "success",
  "meta": {
    "totalRecords": 342,
    "returnedRecords": 342,
    "page": 1,
    "limit": 5000,
    "filterLogic": "AND"
  },
  "columns": [
    {"name": "patientId", "type": "NUMBER", "source": "profile"},
    {"name": "reference", "type": "TEXT", "source": "profile"},
    {"name": "age", "type": "NUMBER", "source": "profile"},
    {"name": "gender", "type": "TEXT", "source": "profile"},
    {"name": "Fasting Glucose", "type": "NUMBER", "source": "variable"},
    {"name": "testedDate", "type": "DATE", "source": "profile"}
  ],
  "records": [
    {
      "patientId": 451,
      "reference": "PAT-00451",
      "age": 42,
      "gender": "Female",
      "Fasting Glucose": 118.5,
      "testedDate": "2024-05-12"
    }
  ]
}
```

---

## 4. Service Layer Extension: `KitService`
To maintain the core rule: **"Keep Logic in Services"**:
- Create `main/services/KitService.py`.
- Integrates with `StudyService` methods (`getAdvancedFilteredData`, `getMultiStudyAdvancedFilteredData`).
- Flattens row values from nested `{valuesByName: {...}}` into flat dictionaries matching the column schema.
- Handles type casting (e.g. string numbers to float/int, dates to ISO strings, null values).

---

## 5. Acceptance Criteria for Phase 2
- [x] All endpoints require staff/superuser authentication with API key or active session.
- [x] `fields` endpoint returns all known profile fields and their valid operators.
- [x] `datasets` endpoint lists all studies with row/variable counts.
- [x] `query` endpoint correctly executes multi-rule filters with AND/OR logic.
- [x] Flattened `records` format effortlessly parses into `pandas.DataFrame(response['records'])`.
