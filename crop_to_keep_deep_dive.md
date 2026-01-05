# Deep Dive: Crop-to-Keep Feature

## Table of Contents

1. [Overview](#overview)
2. [Data Structures](#data-structures)
3. [Action Types Deep Dive](#action-types-deep-dive)
4. [Helper Functions](#helper-functions)
5. [Finalize Endpoint Extension](#finalize-endpoint-extension)
6. [Frontend Visual Behavior](#frontend-visual-behavior)
7. [Edge Cases](#edge-cases)
8. [Implementation Checklist](#implementation-checklist)

---

## Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CROP-TO-KEEP FEATURE                                 │
│                        (iLovePDF-Style Cropping)                             │
│                                                                              │
│  Purpose: Allow doctors to select essential PDF regions to KEEP,            │
│           with visual dimming of excluded areas. Each keep box becomes      │
│           a separate section in the output. Pages without keep boxes        │
│           are excluded entirely.                                            │
│                                                                              │
│  Integration: Extends existing endpoints, NO new endpoints required         │
│    • /session/{document_id}/actions  → handles ADD/REMOVE keep boxes        │
│    • /session/{document_id}/finalize → applies crop + redactions            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### User Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            User Workflow                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. Doctor uploads PDF → PHI detection runs (existing)                      │
│                                                                              │
│  2. Doctor switches to "Crop" mode (new toolbar button)                     │
│                                                                              │
│  3. Doctor draws keep boxes around important content:                       │
│     • Highlighted areas = content to KEEP                                   │
│     • Dimmed areas = content to DISCARD                                     │
│     • Can draw multiple boxes per page                                      │
│     • Can draw boxes on different pages                                     │
│                                                                              │
│  4. Doctor can still use redaction features:                                │
│     • View/Edit mode for redaction boxes                                    │
│     • Add manual redactions inside keep regions                             │
│     • Remove false positives                                                │
│                                                                              │
│  5. Doctor clicks "Apply & Export":                                         │
│     • Crop is applied FIRST (extract keep regions)                          │
│     • Redactions are applied SECOND (on cropped PDF)                        │
│     • Final PDF contains only kept + redacted content                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Structures

### KeepBox Dictionary Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  KeepBox Dictionary Structure                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  keep_box = {                                                                │
│      "box_id": "keep_a1b2c3d4e5f6",     # Unique identifier                 │
│      "page": 0,                          # 0-indexed page number             │
│      "x0": 50.0,                         # Left edge (PDF points)            │
│      "y0": 100.0,                        # Top edge (PDF points)             │
│      "x1": 400.0,                        # Right edge (PDF points)           │
│      "y1": 300.0,                        # Bottom edge (PDF points)          │
│      "is_removed": False,                # Soft-delete flag for undo/redo   │
│  }                                                                           │
│                                                                              │
│  Key differences from RedactionBox:                                         │
│    • NO entity_type (not PHI classification)                                │
│    • NO confidence (user-defined, always 100%)                              │
│    • NO overlay_text (content is preserved, not replaced)                   │
│    • NO is_auto (always user-drawn)                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### DocumentRecord Addition

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  DocumentRecord Addition (document_store.py)                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  @dataclass                                                                  │
│  class DocumentRecord:                                                       │
│      document_id: str                                                        │
│      original_filename: str                                                  │
│      input_path: Optional[Path]                                              │
│      detected_path: Optional[Path]                                           │
│      payload_type: str = "pdf"                                               │
│      stats: Optional[dict] = None                                            │
│      redaction_boxes: Optional[list] = None      # AI-detected              │
│      manual_boxes: Optional[list] = None         # User-drawn redactions    │
│      keep_boxes: Optional[list] = None           # ◄── NEW: Crop regions    │
│      text_spans: Optional[list] = None                                       │
│      history_past: list = field(default_factory=list)                        │
│      history_future: list = field(default_factory=list)                      │
│      final_path: Optional[Path] = None                                       │
│      ...                                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### KeepBox Model (models.py)

```python
class KeepBox(BaseModel):
    """Represents a region to KEEP during crop-to-keep finalization."""
    box_id: Optional[str] = None
    page: int
    x0: float
    y0: float
    x1: float
    y1: float
    is_removed: bool = False
```

### RedactionResponse Addition

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  RedactionResponse Addition (models.py)                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  class RedactionResponse(BaseModel):                                         │
│      document_id: str                                                        │
│      total_pages: int                                                        │
│      redaction_boxes: List[RedactionBox]                                     │
│      manual_boxes: List[RedactionBox]                                        │
│      keep_boxes: List[KeepBox] = []              # ◄── NEW                  │
│      page_previews: Dict[str, str]                                           │
│      stats: Dict[str, Any]                                                   │
│      can_undo: bool                                                          │
│      can_redo: bool                                                          │
│      ...                                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Action Types Deep Dive

### Action Type: `ADD_KEEP_BOX`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            ADD_KEEP_BOX                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  Purpose: Add a new crop region to preserve during finalization             │
│                                                                              │
│  Input:                                                                      │
│  {                                                                           │
│    "type": "ADD_KEEP_BOX",                                                  │
│    "box": {                                                                  │
│      "page": 0,                                                              │
│      "x0": 50, "y0": 100, "x1": 400, "y1": 300                              │
│    }                                                                         │
│  }                                                                           │
│                                                                              │
│  Algorithm:                                                                  │
│  ──────────                                                                  │
│                                                                              │
│  Step 1: Parse and validate                                                 │
│  ─────────────────────────                                                   │
│  box_payload = action.get("box") or {}                                      │
│  parsed = KeepBox(**box_payload)                                            │
│  new_id = parsed.box_id or f"keep_{uuid4().hex[:12]}"                       │
│                                                                              │
│  Step 2: Check if box_id already exists (update vs insert)                  │
│  ─────────────────────────────────────────────────────────                   │
│  existing = _find_keep_box(new_id)                                          │
│  if existing:                                                               │
│      # Update existing box                                                  │
│      existing.update(parsed.model_dump(exclude_none=True))                  │
│      existing["is_removed"] = False                                         │
│  else:                                                                      │
│      # Insert new box                                                       │
│      keep_boxes.append({                                                    │
│          **parsed.model_dump(exclude_none=True),                            │
│          "box_id": new_id,                                                  │
│          "is_removed": False,                                               │
│      })                                                                     │
│                                                                              │
│  Step 3: Set inverse for undo                                               │
│  ───────────────────────────                                                 │
│  inverse = {"type": "REMOVE_KEEP_BOX", "box_id": new_id}                    │
│                                                                              │
│  Visual:                                                                     │
│  ───────                                                                     │
│  ┌────────────────────────────────────────┐                                 │
│  │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│  ░ = Dimmed area               │
│  │░░░░┌─────────────────────┐░░░░░░░░░░░░░│                                 │
│  │░░░░│                     │░░░░░░░░░░░░░│  ┌─┐ = Keep box (highlighted)  │
│  │░░░░│  KEEP BOX (bright)  │░░░░░░░░░░░░░│                                 │
│  │░░░░│  Content preserved  │░░░░░░░░░░░░░│                                 │
│  │░░░░└─────────────────────┘░░░░░░░░░░░░░│                                 │
│  │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│                                 │
│  └────────────────────────────────────────┘                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Action Type: `REMOVE_KEEP_BOX`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          REMOVE_KEEP_BOX                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  Purpose: Soft-delete a keep box (mark as removed)                          │
│                                                                              │
│  Input: { "type": "REMOVE_KEEP_BOX", "box_id": "keep_abc123" }              │
│                                                                              │
│  Algorithm:                                                                  │
│  ──────────                                                                  │
│  1. Find box: found = _find_keep_box(target_id)                             │
│  2. If not found: raise HTTP 400                                            │
│  3. Store previous state: before = b.get("is_removed")                      │
│  4. Set: b["is_removed"] = True                                             │
│  5. Inverse:                                                                │
│     • If was removed: REMOVE_KEEP_BOX (no-op)                               │
│     • If was active: RESTORE_KEEP_BOX                                       │
│                                                                              │
│  Note: Box is NOT deleted from list, just flagged (enables undo)            │
│                                                                              │
│  Visual:                                                                     │
│  ───────                                                                     │
│  Before: keep_box = {"is_removed": False, ...}                              │
│  After:  keep_box = {"is_removed": True, ...}                               │
│                                                                              │
│  UI Effect: Dimming overlay now covers this area too                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Action Type: `RESTORE_KEEP_BOX`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RESTORE_KEEP_BOX                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  Purpose: Un-delete a previously removed keep box                           │
│                                                                              │
│  Input: { "type": "RESTORE_KEEP_BOX", "box_id": "keep_abc123" }             │
│                                                                              │
│  Same as REMOVE_KEEP_BOX but sets is_removed = False                        │
│                                                                              │
│  Visual:                                                                     │
│  ───────                                                                     │
│  Before: keep_box = {"is_removed": True, ...}                               │
│  After:  keep_box = {"is_removed": False, ...}                              │
│                                                                              │
│  UI Effect: Area becomes highlighted again (dimming removed)                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Action Type: `CLEAR_KEEP_BOXES`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CLEAR_KEEP_BOXES                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  Purpose: Remove ALL keep boxes at once (reset crop selection)              │
│                                                                              │
│  Input: { "type": "CLEAR_KEEP_BOXES" }                                      │
│                                                                              │
│  Algorithm:                                                                  │
│  ──────────                                                                  │
│  1. Collect all active keep boxes:                                          │
│     active = [b for b in keep_boxes if not b.get("is_removed")]             │
│                                                                              │
│  2. If none active: return None (no-op)                                     │
│                                                                              │
│  3. Store prior states for undo:                                            │
│     prior_states = [                                                        │
│         {"box_id": b["box_id"], "is_removed": False}                        │
│         for b in active                                                     │
│     ]                                                                       │
│                                                                              │
│  4. Mark all as removed:                                                    │
│     for b in active:                                                        │
│         b["is_removed"] = True                                              │
│                                                                              │
│  5. Set inverse and action for history:                                     │
│     inverse = {"type": "BULK_SET_KEEP_REMOVED", "states": prior_states}     │
│     action = {"type": "BULK_SET_KEEP_REMOVED", "states": desired_states}    │
│                                                                              │
│  Visual Effect:                                                              │
│  ──────────────                                                              │
│  All highlighted areas become dimmed                                        │
│  One Undo restores all keep boxes                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Action Type: `BULK_SET_KEEP_REMOVED`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       BULK_SET_KEEP_REMOVED                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  Purpose: Set is_removed for multiple keep boxes at once                    │
│                                                                              │
│  This is a LOW-LEVEL action used internally by:                             │
│    • CLEAR_KEEP_BOXES                                                       │
│    • Undo/Redo operations                                                   │
│                                                                              │
│  Input:                                                                      │
│  {                                                                           │
│    "type": "BULK_SET_KEEP_REMOVED",                                         │
│    "states": [                                                               │
│      {"box_id": "keep_001", "is_removed": true},                            │
│      {"box_id": "keep_002", "is_removed": true}                             │
│    ]                                                                         │
│  }                                                                           │
│                                                                              │
│  Algorithm:                                                                  │
│  ──────────                                                                  │
│  inverse_states = []                                                        │
│  for s in states:                                                           │
│      box_id = s["box_id"]                                                   │
│      found = _find_keep_box(box_id)                                         │
│      if not found: continue                                                 │
│                                                                              │
│      inverse_states.append({                                                │
│          "box_id": box_id,                                                  │
│          "is_removed": found["is_removed"]                                  │
│      })                                                                     │
│      found["is_removed"] = s["is_removed"]                                  │
│                                                                              │
│  inverse = {"type": "BULK_SET_KEEP_REMOVED", "states": inverse_states}      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Helper Functions

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        _find_keep_box(target_id)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  Purpose: Locate a keep box by its ID                                       │
│                                                                              │
│  Input: target_id (string)                                                  │
│  Output: tuple[index, box_dict] or None                                     │
│                                                                              │
│  Algorithm:                                                                  │
│  ──────────                                                                  │
│  for idx, b in enumerate(keep_boxes):                                       │
│      if b.get("box_id") == target_id:                                       │
│          return (idx, b)                                                    │
│  return None                                                                │
│                                                                              │
│  Note: Similar to _find_box() but only searches keep_boxes list             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Finalize Endpoint Extension

```
┌─────────────────────────────────────────────────────────────────────────────┐
│             POST /session/{document_id}/finalize (Extended)                  │
│                                                                              │
│  Purpose: Generate final PDF with BOTH cropping AND redactions              │
│                                                                              │
│  Existing behavior preserved; crop logic added as pre-processing step       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Detailed Algorithm

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 1: Load document and validate (EXISTING)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  record = get_record_or_404(document_id)                                    │
│                                                                              │
│  if record.payload_type != "pdf":                                           │
│      raise HTTPException(400, "Only PDF sessions can be finalized")         │
│                                                                              │
│  if not record.detected_path or not record.input_path:                      │
│      raise HTTPException(400, "No PDF detected for this document")          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 2: Check for active keep boxes (NEW)                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  keep_boxes = record.keep_boxes or []                                       │
│  active_keeps = [b for b in keep_boxes if not b.get("is_removed")]          │
│                                                                              │
│  has_crop = bool(active_keeps)                                              │
│                                                                              │
│  Decision Point:                                                            │
│  ────────────────                                                            │
│  if has_crop:                                                               │
│      → Apply crop-to-keep FIRST, then redactions                            │
│  else:                                                                      │
│      → Skip to existing redaction logic (unchanged behavior)                │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼ (if has_crop)
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 3: Group keep boxes by page (NEW)                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  by_page: dict[int, list[dict]] = {}                                        │
│                                                                              │
│  for box in active_keeps:                                                   │
│      page_num = int(box["page"])                                            │
│      by_page.setdefault(page_num, []).append(box)                           │
│                                                                              │
│  # Sort boxes within each page by y0 (top to bottom)                        │
│  for page_num in by_page:                                                   │
│      by_page[page_num].sort(key=lambda b: (b["y0"], b["x0"]))               │
│                                                                              │
│  Example:                                                                    │
│  ────────                                                                    │
│  by_page = {                                                                 │
│      0: [                                                                    │
│          {"box_id": "keep_001", "x0": 50, "y0": 100, ...},  # First         │
│          {"box_id": "keep_002", "x0": 50, "y0": 400, ...}   # Second        │
│      ],                                                                      │
│      2: [                                                                    │
│          {"box_id": "keep_003", "x0": 100, "y0": 50, ...}                   │
│      ]                                                                       │
│  }                                                                           │
│                                                                              │
│  Pages 1, 3, 4... have NO keep boxes → EXCLUDED from output                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 4: Generate cropped PDF (NEW)                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  src = fitz.open(record.detected_path)                                      │
│  cropped = fitz.open()  # New empty PDF for cropped content                 │
│                                                                              │
│  # Track coordinate mapping for redaction boxes                             │
│  box_mapping: list[dict] = []  # Maps old coords to new page/coords         │
│                                                                              │
│  output_page_idx = 0                                                        │
│  for src_page_num in sorted(by_page.keys()):                                │
│      if src_page_num >= src.page_count:                                     │
│          continue  # Skip invalid page numbers                              │
│                                                                              │
│      src_page = src.load_page(src_page_num)                                 │
│      page_rect = src_page.rect                                              │
│                                                                              │
│      for box in by_page[src_page_num]:                                      │
│          # Create clip rect and clamp to page bounds                        │
│          clip = fitz.Rect(box["x0"], box["y0"], box["x1"], box["y1"])       │
│          clip = clip & page_rect  # Intersection (clamp)                    │
│                                                                              │
│          if clip.is_empty or clip.width < 10 or clip.height < 10:           │
│              continue  # Skip invalid/tiny clips                            │
│                                                                              │
│          # Create new page sized to clip region                             │
│          new_page = cropped.new_page(                                       │
│              width=clip.width,                                              │
│              height=clip.height                                             │
│          )                                                                   │
│                                                                              │
│          # Copy clipped content from source                                 │
│          new_page.show_pdf_page(                                            │
│              new_page.rect,     # Fill entire new page                      │
│              src,               # Source document                           │
│              src_page_num,      # Source page                               │
│              clip=clip          # ◄── KEY: Only this region copied          │
│          )                                                                   │
│                                                                              │
│          # Record mapping for redaction box coordinate transform            │
│          box_mapping.append({                                               │
│              "src_page": src_page_num,                                      │
│              "clip": clip,                                                  │
│              "dst_page": output_page_idx,                                   │
│              "offset_x": clip.x0,                                           │
│              "offset_y": clip.y0,                                           │
│          })                                                                 │
│          output_page_idx += 1                                               │
│                                                                              │
│  src.close()                                                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Visual Example: Crop Process

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Visual Example: Crop-to-Keep Process                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Source PDF:                        Output PDF:                             │
│  ┌────────────────┐                 ┌─────────────┐                         │
│  │  Page 0        │                 │ Output pg 0 │ ← From keep_001         │
│  │  ┌──────────┐  │                 │ (cropped)   │                         │
│  │  │keep_001  │  │    ────────►    └─────────────┘                         │
│  │  └──────────┘  │                 ┌─────────────┐                         │
│  │  ┌──────────┐  │                 │ Output pg 1 │ ← From keep_002         │
│  │  │keep_002  │  │                 │ (cropped)   │                         │
│  │  └──────────┘  │                 └─────────────┘                         │
│  └────────────────┘                 ┌─────────────┐                         │
│  ┌────────────────┐                 │ Output pg 2 │ ← From keep_003         │
│  │  Page 1        │  (no keeps)     │ (cropped)   │                         │
│  │  (excluded)    │                 └─────────────┘                         │
│  └────────────────┘                                                         │
│  ┌────────────────┐                                                         │
│  │  Page 2        │                                                         │
│  │  ┌──────────┐  │                                                         │
│  │  │keep_003  │  │                                                         │
│  │  └──────────┘  │                                                         │
│  └────────────────┘                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Coordinate Transformation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 5: Transform redaction box coordinates (NEW)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  # Redaction boxes were drawn on ORIGINAL pages                             │
│  # Need to transform to CROPPED page coordinates                            │
│                                                                              │
│  def transform_box(box: dict, mapping: list[dict]) -> dict | None:          │
│      src_page = box["page"]                                                 │
│      box_rect = fitz.Rect(box["x0"], box["y0"], box["x1"], box["y1"])       │
│                                                                              │
│      for m in mapping:                                                      │
│          if m["src_page"] != src_page:                                      │
│              continue                                                       │
│                                                                              │
│          clip = m["clip"]                                                   │
│          intersection = box_rect & clip                                     │
│                                                                              │
│          if intersection.is_empty:                                          │
│              continue  # Box not in this clip region                        │
│                                                                              │
│          # Transform coordinates relative to clip origin                    │
│          return {                                                           │
│              **box,                                                         │
│              "page": m["dst_page"],                                         │
│              "x0": intersection.x0 - m["offset_x"],                         │
│              "y0": intersection.y0 - m["offset_y"],                         │
│              "x1": intersection.x1 - m["offset_x"],                         │
│              "y1": intersection.y1 - m["offset_y"],                         │
│          }                                                                  │
│                                                                              │
│      return None  # Box outside all keep regions → discarded                │
│                                                                              │
│  # Apply to all redaction boxes                                             │
│  transformed_ai = [transform_box(b, box_mapping) for b in stored_boxes]     │
│  transformed_ai = [b for b in transformed_ai if b is not None]              │
│                                                                              │
│  transformed_manual = [transform_box(b, box_mapping) for b in manual_boxes] │
│  transformed_manual = [b for b in transformed_manual if b is not None]      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Coordinate Transform Visual

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Visual: Coordinate Transformation                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Original Page:                     Cropped Page:                           │
│  ┌────────────────────┐             ┌──────────────┐                        │
│  │  (0,0)             │             │ (0,0)        │                        │
│  │    ┌─────────────┐ │             │ ┌─────────┐  │                        │
│  │    │ KEEP (50,100)│ │            │ │REDACT   │  │ ← Coords shifted       │
│  │    │  ┌───────┐  │ │   ───►     │ │(50,20)  │  │   by (-50, -100)       │
│  │    │  │REDACT │  │ │             │ └─────────┘  │                        │
│  │    │  │(100,120)│ │ │            └──────────────┘                        │
│  │    │  └───────┘  │ │                                                     │
│  │    └─────────────┘ │             New coords:                             │
│  └────────────────────┘             x0: 100-50=50, y0: 120-100=20           │
│                                                                              │
│  Formula:                                                                    │
│  ────────                                                                    │
│  new_x0 = old_x0 - clip.x0                                                  │
│  new_y0 = old_y0 - clip.y0                                                  │
│  new_x1 = old_x1 - clip.x0                                                  │
│  new_y1 = old_y1 - clip.y0                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Apply Redactions and Save

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 6: Apply redactions to cropped PDF (EXISTING, adapted)                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  # Now working with cropped PDF and transformed coordinates                 │
│                                                                              │
│  remove_indices = {i for i, b in enumerate(transformed_ai)                  │
│                    if b.get("is_removed")}                                  │
│                                                                              │
│  overlay_map = pipeline.build_overlay_map(transformed_ai)                   │
│  removed = remove_ai_boxes(cropped, remove_indices)                         │
│                                                                              │
│  manual_to_add = [RedactionBox(**b) for b in transformed_manual             │
│                   if not b.get("is_removed")]                               │
│  add_manual_boxes(cropped, manual_to_add)                                   │
│                                                                              │
│  # Apply redactions                                                         │
│  for page in cropped:                                                       │
│      page.apply_redactions()                                                │
│  apply_overlays(cropped, overlay_map)                                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Step 7: Save and return (EXISTING)                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  final_path = TEMP_DIR / f"{document_id}_FINAL.pdf"                         │
│  cropped.save(str(final_path), garbage=4, deflate=True, clean=True)         │
│  cropped.close()                                                            │
│                                                                              │
│  state.document_store.finalize(document_id, final_path)                     │
│                                                                              │
│  return {                                                                    │
│      "success": True,                                                        │
│      "document_id": document_id,                                             │
│      "final_filename": f"{stem}_REDACTED.pdf",                              │
│      "download_url": f"/download/{document_id}",                            │
│  }                                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Frontend Visual Behavior

### Dimming Overlay Implementation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     Frontend Dimming Overlay (Canvas)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  When in "Crop" mode, render dimming overlay using Canvas compositing:      │
│                                                                              │
│  Algorithm:                                                                  │
│  ──────────                                                                  │
│  1. Draw semi-transparent overlay on ENTIRE page                            │
│     ctx.fillStyle = "rgba(0, 0, 0, 0.5)"                                    │
│     ctx.fillRect(0, 0, pageWidth, pageHeight)                               │
│                                                                              │
│  2. For each active keep box, CUT OUT the region (make transparent)         │
│     ctx.globalCompositeOperation = "destination-out"                        │
│     ctx.fillStyle = "white"                                                 │
│     ctx.fillRect(box.x0, box.y0, box.width, box.height)                     │
│     ctx.globalCompositeOperation = "source-over"  // Reset                  │
│                                                                              │
│  3. Draw border around keep boxes                                           │
│     ctx.strokeStyle = "#2196F3"  // Blue                                    │
│     ctx.setLineDash([5, 5])      // Dashed                                  │
│     ctx.strokeRect(box.x0, box.y0, box.width, box.height)                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Visual Result

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Visual Result in Crop Mode                                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────┐                                 │
│  │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│  ▓ = Dimmed (50% opacity)      │
│  │▓▓▓▓┌┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┐▓▓▓▓▓▓▓▓▓▓▓▓▓│                                 │
│  │▓▓▓▓┊                     ┊▓▓▓▓▓▓▓▓▓▓▓▓▓│  ┌┄┐ = Keep box border (blue)   │
│  │▓▓▓▓┊   BRIGHT CONTENT    ┊▓▓▓▓▓▓▓▓▓▓▓▓▓│                                 │
│  │▓▓▓▓┊   (no dimming)      ┊▓▓▓▓▓▓▓▓▓▓▓▓▓│      = Clear area (original)   │
│  │▓▓▓▓┊                     ┊▓▓▓▓▓▓▓▓▓▓▓▓▓│                                 │
│  │▓▓▓▓└┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┘▓▓▓▓▓▓▓▓▓▓▓▓▓│                                 │
│  │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│                                 │
│  │▓▓▓▓┌┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┐▓▓▓▓▓▓▓▓▓▓▓▓▓│                                 │
│  │▓▓▓▓┊  ANOTHER KEEP BOX   ┊▓▓▓▓▓▓▓▓▓▓▓▓▓│                                 │
│  │▓▓▓▓└┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┘▓▓▓▓▓▓▓▓▓▓▓▓▓│                                 │
│  │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│                                 │
│  └────────────────────────────────────────┘                                 │
│                                                                              │
│  Interactions in Crop Mode:                                                 │
│  ─────────────────────────                                                   │
│  • Click + Drag: Draw new keep box                                          │
│  • Click on keep box border: Select for deletion                            │
│  • Zoom/Pan: Still works normally                                           │
│  • Redaction boxes: Visible and editable in highlighted areas               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Mode Switching

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Toolbar Mode Switching                                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────────────────┐             │
│  │  [View] [Edit] [Crop]    [Zoom+] [Zoom-]   [Undo] [Redo]   │             │
│  └────────────────────────────────────────────────────────────┘             │
│                    ▲                                                         │
│                    │                                                         │
│                 NEW BUTTON                                                   │
│                                                                              │
│  Mode Behaviors:                                                            │
│  ───────────────                                                             │
│  • View Mode: Read-only, no interactions                                    │
│  • Edit Mode: Draw redaction boxes (existing)                               │
│  • Crop Mode: Draw keep boxes (NEW)                                         │
│                                                                              │
│  type EditorMode = "view" | "edit" | "crop"                                 │
│                                                                              │
│  When switching modes:                                                       │
│  • Crop → Edit: Dimming overlay stays, can add redactions in kept areas    │
│  • Crop → View: Dimming overlay stays, read-only                            │
│  • Edit → Crop: Switch to drawing keep boxes                                │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Edge Cases

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Edge Cases                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. No keep boxes defined                                                   │
│     → Finalize uses existing behavior (full pages, no cropping)             │
│     → UI shows full pages without dimming                                   │
│                                                                              │
│  2. Keep box extends beyond page bounds                                     │
│     → Clamp to page dimensions using fitz.Rect intersection (&)             │
│     → No error, silently adjusted                                           │
│                                                                              │
│  3. Keep box on non-existent page                                           │
│     → Skip with warning in logs, continue processing valid pages            │
│                                                                              │
│  4. Very small keep box (< 10 pixels width or height)                       │
│     → Skip to prevent empty/corrupted output pages                          │
│     → Log warning for debugging                                             │
│                                                                              │
│  5. Redaction box partially inside keep region                              │
│     → Clip redaction box to intersection with keep region                   │
│     → Only the overlapping portion is redacted                              │
│                                                                              │
│  6. Redaction box spans multiple keep regions                               │
│     → Create separate transformed boxes for each keep region                │
│     → Each portion appears in its respective output page                    │
│                                                                              │
│  7. Redaction box completely outside all keep regions                       │
│     → Discarded (not included in output)                                    │
│     → Content was already excluded by crop                                  │
│                                                                              │
│  8. Undo after finalize                                                     │
│     → Keep boxes still in session history                                   │
│     → Can modify and re-finalize                                            │
│     → Previous final PDF is overwritten                                     │
│                                                                              │
│  9. All keep boxes removed (is_removed=True)                                │
│     → Same as no keep boxes: full pages, no cropping                        │
│     → Graceful fallback to existing behavior                                │
│                                                                              │
│  10. Overlapping keep boxes on same page                                    │
│      → Each box creates separate output page                                │
│      → Overlapping content appears in both output pages                     │
│      → Order determined by y0 (top to bottom), then x0                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Checklist

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Implementation Checklist                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Backend:                                                                    │
│  ─────────                                                                   │
│  □ document_store.py     → Add keep_boxes field to DocumentRecord           │
│  □ models.py             → Add KeepBox model, update RedactionResponse      │
│  □ session_actions.py    → Add keep box action handlers:                    │
│                            - ADD_KEEP_BOX                                   │
│                            - REMOVE_KEEP_BOX                                │
│                            - RESTORE_KEEP_BOX                               │
│                            - CLEAR_KEEP_BOXES                               │
│                            - BULK_SET_KEEP_REMOVED                          │
│  □ routes_session.py     → Return keep_boxes in get_session response        │
│  □ routes_apply.py       → Extend finalize with crop logic:                 │
│                            - Check for active keep boxes                    │
│                            - Group by page, sort by position                │
│                            - Generate cropped PDF                           │
│                            - Transform redaction coordinates                │
│                            - Apply redactions to cropped PDF                │
│                                                                              │
│  Frontend:                                                                   │
│  ──────────                                                                  │
│  □ types.ts              → Add KeepBox type                                 │
│                          → Add "crop" to EditorMode union                   │
│                          → Add keep box action types                        │
│  □ usePhiRedaction.ts    → Add keepBoxes state                              │
│                          → Add crop mode handling                           │
│                          → Add keep box action dispatchers                  │
│  □ HeaderControls.tsx    → Add "Crop" toolbar button                        │
│                          → Style active state for crop mode                 │
│  □ CanvasPage.tsx        → Dimming overlay rendering                        │
│                          → Keep box border rendering                        │
│                          → Crop mode mouse interactions                     │
│  □ api.ts                → Update RedactionResponse type                    │
│                          → (No new endpoints needed)                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## API Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API Summary                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Endpoints (NO new endpoints, existing ones extended):                      │
│  ──────────────────────────────────────────────────                          │
│                                                                              │
│  POST /session/{document_id}/actions                                        │
│    New action types:                                                        │
│    • { "type": "ADD_KEEP_BOX", "box": {...} }                               │
│    • { "type": "REMOVE_KEEP_BOX", "box_id": "..." }                         │
│    • { "type": "RESTORE_KEEP_BOX", "box_id": "..." }                        │
│    • { "type": "CLEAR_KEEP_BOXES" }                                         │
│                                                                              │
│  GET /session/{document_id}                                                 │
│    Response now includes:                                                   │
│    • keep_boxes: List[KeepBox]                                              │
│                                                                              │
│  POST /session/{document_id}/finalize                                       │
│    Extended behavior:                                                       │
│    • If keep_boxes exist → crop first, then redact                          │
│    • If no keep_boxes → existing behavior (full pages)                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```
