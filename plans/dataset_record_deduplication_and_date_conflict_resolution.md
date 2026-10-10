# Dataset Record Deduplication and Date Conflict Resolution Plan

## Background & Objectives
In bulk dataset imports, records represent clinical study observations (`UserStudy` instances and their associated `StudyResult` values).
Previously, when rows lacked a `tested_date` column, the system defaulted every row to `timezone.now().date()`.
This created critical bugs:
1. **Multiple Records in the Same CSV Collapsed**: If a CSV contained multiple test records for the same patient, subsequent rows either updated/overwrote the first row or were skipped as in-file duplicates.
2. **Multiple Files Collapsed**: If two CSV files were imported on the same day for the same patient without tested dates, the second file's records overwrote the first file's records.
3. **Unintended Updates**: Existing records were updated even when the import file didn't specify a test date.

## Approved Strategy & Requirements
1. **Conditional Updates**:
   - Only update an existing `UserStudy` if the `tested_date` column is explicitly mapped and provided in that row.
   - If `tested_date` is absent, unmapped, or empty, **never update an existing record**; always create a new `UserStudy`.
2. **Date Conflict Resolution**:
   - For rows without an explicit `tested_date`, assign an available date around current date:
     - Check `today` (`timezone.now().date()`).
     - If `today` is already used by this patient in this study, sequentially check past days (`today - 1 day`, `today - 2 days`, etc.) until an unused date is found.
   - For rows with an explicit `tested_date`:
     - If the date matches an existing record in the database, the **first occurrence** in the file updates that record.
     - Any **subsequent rows** in the same file for that patient with the same date are assigned unique offset past dates (`date - 1 day`, `date - 2 days`, etc.) so each row is imported as a distinct record.
3. **No Dropping of Multiple Patient Visits**:
   - In dataset import, multiple rows for the same patient must not be skipped as in-file duplicates. Every valid row must be imported with its own `UserStudy`.
4. **Study Preview Accuracy**:
   - `StudyService.previewDataImport` must accurately reflect this logic:
     - A row is only marked `'update'` if `tested_date` is explicitly specified and matches an existing record.
     - In-file multiple records for the same patient are counted and previewed as distinct `'new'` entries.

## Implementation Steps
1. **`DataImportService.py`**:
   - Add robust date parser `_parse_date(date_str)`.
   - Add `_get_available_date(patient_id, target_date, used_dates)` helper (sequential past days).
   - Pre-cache `patient_used_dates` and `existing_user_studies_by_patient_date`.
   - Update `_process_row_optimized` to apply the conditional update and offset date resolution.
   - Remove duplicate row dropping for multi-record patients.
2. **`StudyService.py`**:
   - Update `previewDataImport` to track `patient_used_dates` and only assign `'update'` to explicit `tested_date` matches on first occurrence.
   - Ensure patient grouping in `_createPatientSignature` groups patient rows without dropping multi-record observations.
3. **Testing**:
   - Write comprehensive tests in `test/test_patient_reference.py` and `test/test_dataset_import_conflict.py`:
     - Test multi-record CSV for same patient without tested_date creates distinct UserStudy records with offset dates.
     - Test multi-record CSV for same patient with identical tested_date: first updates existing, second creates new with offset date.
     - Test subsequent import file creates new records without overwriting earlier import.
   - Run full test suite via `uv run python manage.py test test`.
