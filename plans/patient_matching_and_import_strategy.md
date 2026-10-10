# Patient Matching & Data Import Strategy

## 1. Overview & Principles
This document defines the strict patient identification and data import strategy across BIOM:
- **`patient_id`**: The database primary key (`Patient.id`) representing an already existing patient in the system.
- **`reference`**: The doctor or dataset assigned code name/reference (`Patient.reference`), such as `P-1001` or `MRN-9021`.
- **Location & Demographics**: Fallback heuristic matching for anonymized or unreferenced records.

---

## 2. Three-Tier Patient Matching Priority
When matching an incoming row to an existing patient in the database (in `DataImportService`, `PatientService._findBestMatchingPatient`, and patient matching wizards):

```
1. patient_id (Database PK)
   │── Found? ──► [MATCH 100%]
   └── Not provided / Not found
         ▼
2. reference (Patient.reference)
   │── Found? ──► [MATCH 100%]
   └── Not provided / Not found
         ▼
3. Location + Confirmed Demographics (Mandatory Location Prerequisite)
   │── Has Lat & Lng AND Distance <= ~1.1km (0.01°)
   │   AND Demographics Confirmed (Names + DOB + Gender match)?
   │       ├── Yes ──► [MATCH]
   │       └── No  ──► [NO MATCH - Reject Heuristic]
   └── No Lat/Lng ────► [NO MATCH - Never match on Name + DOB alone]
```

### Strict Rules:
1. **Never match on Name + Birthday alone**: Different individuals can share names and birthdays across different cities, clinics, or countries. Pure demographic matching without location leads to false identification and is strictly prohibited.
2. **Never match on Location alone**: Multiple distinct individuals can share identical or close GPS coordinates (e.g. hospitals, clinics, apartment complexes). Close coordinates must be verified by matching demographics.
3. **Mandatory Location Prerequisite for Heuristics**: If neither `patient_id` nor `reference` is provided, location (`latitude` and `longitude`) is required. If location is absent or beyond $\approx 1.1\,\text{km}$, no match is made and a new patient is created.

---

## 3. Date of Birth Calculation from Age & Tested Date
When importing patients or datasets:
1. **Date of Birth Available**: If `dateOfBirth` is provided as a field, parse and use it directly.
2. **Date of Birth Not Available, but Age Given**:
   - Check if `testedDate` (test / study collection date) is present.
   - If `testedDate` is present:
     $$\text{reference\_year} = \text{tested\_date.year}$$
   - If `testedDate` is NOT present:
     $$\text{reference\_year} = \text{current\_date.year} \quad (\text{timezone.now().year})$$
     And set `tested_date = timezone.now().date()` so the record retains accurate date context.
   - Calculate back to the birth year:
     $$\text{birth\_year} = \text{reference\_year} - \text{age}$$
   - Date of birth is set to January 1 of that year:
     $$\text{dateOfBirth} = \text{date}(\text{birth\_year}, 1, 1)$$

---

## 4. Templates & Data Export Architecture
1. **Patient Import Template (`/api/v1/patient/template`)**:
   - Columns: `PatientId`, `Reference`, `FirstName`, `LastName`, `DateOfBirth`, `Age`, `Gender`, `Latitude`, `Longitude`, `Notes`.
   - `PatientId`: Optional existing database ID (leave blank for new patients).
   - `Reference`: Doctor or study reference code (e.g. `P-1001`).
2. **Dataset Import Template (`/api/v1/dataset/<id>/template`)**:
   - Columns: `PatientId`, `PatientReference`, `FirstName`, `LastName`, `DateOfBirth`, `Age`, `Gender`, `Latitude`, `Longitude`, `TestedDate`, `[Variables...]`.
   - Clear distinction between system `PatientId` and doctor `PatientReference`.
3. **Patient Match Output**:
   - Includes `matched_patient_id` containing the matched database ID `#101`.
   - Includes `matched_reference` containing the doctor's reference code.
