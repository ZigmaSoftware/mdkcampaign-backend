"""
Shared utilities for bulk CSV / XLSX import across all ViewSets.

Usage in a ViewSet:
    from campaign_os.core.utils.bulk_upload import parse_upload, BulkResult

    @action(detail=False, methods=['POST'], url_path='bulk-upload',
            parser_classes=[MultiPartParser])
    def bulk_upload(self, request):
        rows, err = parse_upload(request)
        if err:
            return Response({'detail': err}, status=400)
        result = BulkResult()
        for i, row in enumerate(rows, start=2):
            try:
                ... # create / get_or_create
                result.ok()
            except Exception as e:
                result.fail(i, str(e))
        return Response(result.summary())
"""
import csv
import io
from typing import Optional


# ── file parsing ─────────────────────────────────────────────────────────────

def parse_upload(request) -> tuple[list[dict], Optional[str]]:
    """
    Extract and parse the uploaded file from a DRF request.
    Returns (rows, error_message).  rows is [] on error.
    """
    file_obj = request.FILES.get('file')
    if not file_obj:
        return [], 'No file provided. Send multipart/form-data with a "file" field.'

    name = file_obj.name.lower()
    try:
        if name.endswith('.xlsx') or name.endswith('.xls'):
            rows = _parse_xlsx(file_obj)
        else:
            rows = _parse_csv(file_obj)
    except Exception as exc:
        return [], f'Could not parse file: {exc}'

    return rows, None


def _parse_csv(file_obj) -> list[dict]:
    content = file_obj.read().decode('utf-8-sig')          # strip BOM if present
    reader  = csv.DictReader(io.StringIO(content))
    return [_normalise_row(row) for row in reader]


def _parse_xlsx(file_obj) -> list[dict]:
    import openpyxl
    wb   = openpyxl.load_workbook(file_obj, read_only=True, data_only=True)
    ws   = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []

    headers = [
        str(h).strip().lower().replace(' ', '_') if h is not None else f'col_{i}'
        for i, h in enumerate(rows[0])
    ]

    result = []
    for row in rows[1:]:
        if all(v is None for v in row):
            continue                                        # skip blank rows
        d = {
            headers[i]: (str(v).strip() if v is not None else '')
            for i, v in enumerate(row)
            if i < len(headers)
        }
        result.append(d)
    return result


def _normalise_row(row: dict) -> dict:
    """Lower-case keys, strip whitespace, replace spaces with underscores."""
    return {
        k.strip().lower().replace(' ', '_'): (v.strip() if isinstance(v, str) else (v or ''))
        for k, v in row.items()
        if k
    }


# ── FK resolution helpers ─────────────────────────────────────────────────────

def resolve_by_code(model, code_value: str, code_field: str = 'code'):
    """Return pk of model instance whose `code_field` == code_value, or None."""
    if not code_value:
        return None
    return (
        model.objects
             .filter(**{code_field: code_value.strip()})
             .values_list('id', flat=True)
             .first()
    )


def resolve_by_name(model, name_value: str):
    """Case-insensitive name lookup; returns pk or None."""
    if not name_value:
        return None
    return (
        model.objects
             .filter(name__iexact=name_value.strip())
             .values_list('id', flat=True)
             .first()
    )


# ── type coercions ────────────────────────────────────────────────────────────

def to_int(value) -> Optional[int]:
    try:
        return int(str(value).strip()) if value not in ('', None) else None
    except (ValueError, TypeError):
        return None


def to_bool(value) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ('true', '1', 'yes', 'y')
    return None


def to_str(value, default: str = '') -> str:
    return str(value).strip() if value not in ('', None) else default


# ── result accumulator ────────────────────────────────────────────────────────

class BulkResult:
    def __init__(self):
        self._created  = 0
        self._skipped  = 0
        self._errors: list[dict] = []

    def ok(self, created: bool = True):
        if created:
            self._created += 1
        else:
            self._skipped += 1

    def fail(self, row_number: int, reason: str):
        self._errors.append({'row': row_number, 'reason': reason})

    def summary(self) -> dict:
        return {
            'created': self._created,
            'skipped': self._skipped,
            'errors':  self._errors,
        }
