from datetime import datetime, timezone
from pathlib import Path

import shutil
import threading
import traceback
import uuid

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    File,
    HTTPException,
    UploadFile,
)

from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import (
    Base,
    SessionLocal,
    engine,
    get_db,
)

from models import Document

from cv.preprocess import (
    preprocess_image_file,
    preprocess_pdf,
)

from ocr.ocr import (
    process_document,
    save_ocr_result,
)


# ==========================================================
# DATABASE
# ==========================================================

Base.metadata.create_all(
    bind=engine
)


# ==========================================================
# APP
# ==========================================================

app = FastAPI(
    title="Land Record Intelligence System",
    version="1.0.0",
)


# ==========================================================
# CORS
# ==========================================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],

    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================================
# DIRECTORIES
# ==========================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
)


ORIGINAL_DIR = (
    BASE_DIR
    / "original_documents"
)


DIGITALIZED_DIR = (
    BASE_DIR
    / "digitalized_documents"
)


CONCISE_DIR = (
    DIGITALIZED_DIR
    / "concise"
)


DETAILED_DIR = (
    DIGITALIZED_DIR
    / "detailed"
)


for directory in [

    ORIGINAL_DIR,
    DIGITALIZED_DIR,
    CONCISE_DIR,
    DETAILED_DIR,

]:

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )


# ==========================================================
# FILE TYPES
# ==========================================================

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
}


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}


# ==========================================================
# PROCESSING CONTROL
# ==========================================================

PROCESSING_LOCK = (
    threading.Lock()
)


ACTIVE_JOBS = set()


ACTIVE_JOBS_LOCK = (
    threading.Lock()
)


def add_active_job(
    document_id,
):

    with ACTIVE_JOBS_LOCK:

        if (
            document_id
            in ACTIVE_JOBS
        ):

            return False


        ACTIVE_JOBS.add(
            document_id
        )

        return True


def remove_active_job(
    document_id,
):

    with ACTIVE_JOBS_LOCK:

        ACTIVE_JOBS.discard(
            document_id
        )


def is_active_job(
    document_id,
):

    with ACTIVE_JOBS_LOCK:

        return (
            document_id
            in ACTIVE_JOBS
        )


# ==========================================================
# DATE
# ==========================================================

def utc_iso(value):

    if value is None:
        return None


    if value.tzinfo is None:

        value = (
            value.replace(
                tzinfo=timezone.utc
            )
        )


    return (
        value
        .astimezone(
            timezone.utc
        )
        .isoformat()
        .replace(
            "+00:00",
            "Z",
        )
    )


# ==========================================================
# SERIALIZER
# ==========================================================

def serialize_document(
    document,
):

    return {

        "document_id":
            document.document_id,

        "filename":
            document.original_filename,

        "stored_as":
            document.stored_filename,

        "status":
            document.status,

        "confidence":
            document.confidence,

        "uploaded_at":
            utc_iso(
                document.uploaded_at
            ),

        "original_path":
            document.original_path,

        "concise_path":
            document.concise_path,

        "detailed_path":
            document.detailed_path,
    }


# ==========================================================
# UPDATE DATABASE STATUS
# ==========================================================

def update_document(
    db,
    document,
    status,
    confidence=None,
):

    document.status = status


    if confidence is not None:

        document.confidence = (
            confidence
        )


    db.commit()

    db.refresh(
        document
    )


# ==========================================================
# CV
# ==========================================================

def run_cv(
    db,
    document,
    original_path,
    extension,
    processed_dir,
):

    update_document(
        db,
        document,
        "CV Processing",
        "—",
    )


    print(
        f"[CV] "
        f"{document.document_id} "
        f"processing..."
    )


    if extension == ".pdf":

        processed_files = (
            preprocess_pdf(
                original_path,
                processed_dir,
            )
        )


    elif (
        extension
        in IMAGE_EXTENSIONS
    ):

        processed_files = (
            preprocess_image_file(
                original_path,
                processed_dir,
            )
        )


    else:

        raise RuntimeError(
            f"Unsupported file type: "
            f"{extension}"
        )


    if not processed_files:

        raise RuntimeError(
            "CV produced no processed pages."
        )


    update_document(
        db,
        document,
        "CV Completed",
        "—",
    )


    print(
        f"[CV] "
        f"{document.document_id} "
        f"completed."
    )


# ==========================================================
# OCR
# ==========================================================

def run_ocr(
    db,
    document,
    processed_dir,
):

    update_document(
        db,
        document,
        "OCR Processing",
        "—",
    )


    print(
        f"[OCR] "
        f"{document.document_id} "
        f"processing..."
    )


    ocr_result = (
        process_document(
            processed_dir
        )
    )


    if not ocr_result:

        raise RuntimeError(
            "OCR returned no result."
        )


    if (
        ocr_result.get(
            "page_count",
            0,
        )
        <= 0
    ):

        raise RuntimeError(
            "OCR found no processed pages."
        )


    ocr_output_path = (
        processed_dir
        / "ocr_result.json"
    )


    save_ocr_result(
        ocr_result,
        ocr_output_path,
    )


    if (
        not
        ocr_output_path.exists()
    ):

        raise RuntimeError(
            "OCR JSON was not created."
        )


    confidence = float(

        ocr_result.get(
            "document_confidence",
            0,
        )
        or 0

    )


    update_document(
        db,
        document,
        "OCR Completed",
        f"{confidence:.2f}%",
    )


    print(
        f"[OCR] "
        f"{document.document_id} "
        f"completed."
    )

    # Needed downstream by the intelligence pipeline
    # (Layout/Extraction/etc all take ocr_result as input).
    return ocr_result


# ==========================================================
# INTELLIGENCE PIPELINE
# (Layout -> Composer -> Extraction -> Normalization ->
#  Validation -> Duplicate Detection -> Confidence ->
#  Human Verification -> Persistence)
#
# Each stage function is a pure function that takes the
# previous stage's dict output and returns its own dict
# output — this mirrors exactly how each module's own
# docstring describes its pipeline position and contract.
# See each module file for its full "DOES / DOES NOT" list.
# ==========================================================

def fetch_existing_records_for_duplicate_check():
    """
    Rebuild a list of {"fields": {...}} dicts (the shape
    duplicate_detector.detect_duplicates expects) from rows
    already persisted in Postgres land_record_fields.

    NOTE: this only works once at least one document has been
    fully persisted. Returns [] (no duplicates possible yet) if
    Postgres isn't reachable or has no rows — this is expected
    on your very first successful run.
    """

    try:
        from database.db_manager import DatabaseManager

        db_pg = DatabaseManager()

        rows = db_pg.fetch_all(
            "SELECT document_id, field_name, normalized_value, "
            "validation_status FROM land_record_fields"
        )

        db_pg.close()

    except Exception as error:
        print(
            f"[DUPLICATE CHECK] Could not reach Postgres, "
            f"treating as no existing records: {error}"
        )
        return []

    records_by_doc = {}

    for row in rows:
        doc_id = row["document_id"]
        records_by_doc.setdefault(doc_id, {"fields": {}})
        records_by_doc[doc_id]["fields"][row["field_name"]] = {
            "normalized_value": row["normalized_value"],
            "validation_status": row["validation_status"],
        }

    return list(records_by_doc.values())


def run_intelligence_pipeline(
    db,
    document,
    ocr_result,
):
    """
    Chains every stage after OCR. Any exception here marks the
    document "Pipeline Failed" and stops — it does NOT roll back
    OCR results, so you can retry just this stage without
    re-running CV/OCR (see the "pipeline" retry_mode you'll want
    to add to the /retry endpoint).
    """

    from layout.layout import build_layout
    from composer.composer import build_layout_with_text
    from extraction.extractor import extract_fields
    from normalization.normalizer import normalize_extraction
    from validation.validator import validate_normalization
    from duplicate_detection.duplicate_detector import detect_duplicates
    from confidence.confidence_scorer import calculate_confidence
    from human_verification.verification_engine import (
        create_verification,
        finalize_verification,
    )
    from database.db_persistence import DatabasePersistence

    document_id = document.document_id

    update_document(db, document, "Pipeline Processing", None)
    print(f"[PIPELINE] {document_id} processing...")

    layout_result = build_layout_with_text(ocr_result, document_id)

    extraction_result = extract_fields(
        ocr_result,
        layout_result,
        layout_result,  # composer output was merged into layout_result
    )

    normalization_result = normalize_extraction(extraction_result)

    validation_result = validate_normalization(normalization_result)

    existing_records = fetch_existing_records_for_duplicate_check()
    duplicate_result = detect_duplicates(validation_result, existing_records)

    confidence_result = calculate_confidence(
        validation_result,
        duplicate_result,
    )

    verification_result = create_verification(
        confidence_result,
        validation_result,
        duplicate_result,
    )

    # Save the verification artifact to disk regardless of whether
    # it can be auto-finalized — this is what a future review UI
    # would load to let a human act on pending fields.
    verification_path = (
        DIGITALIZED_DIR / document_id / "human_verification_result.json"
    )
    import json as _json
    verification_path.write_text(
        _json.dumps(verification_result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    pending_fields = verification_result.get("summary", {}).get(
        "fields_requiring_review", 0
    )

    if pending_fields == 0:
        final_result = finalize_verification(
            verification_result,
            reviewer="auto",
        )

        try:
            DatabasePersistence().persist(final_result)
        except Exception as error:
            # Persistence failure shouldn't erase a good pipeline
            # run — surface it clearly but keep the JSON artifact
            # above as the source of truth to retry persistence from.
            update_document(db, document, "Persistence Failed", None)
            print(f"[PERSIST ERROR] {document_id}: {error}")
            traceback.print_exc()
            return

        update_document(db, document, "Verified", None)
        print(f"[PIPELINE] {document_id} auto-verified and persisted.")

    else:
        update_document(db, document, "Pending Review", None)
        print(
            f"[PIPELINE] {document_id} has {pending_fields} "
            f"field(s) awaiting human review."
        )


# ==========================================================
# BACKGROUND PIPELINE
# ==========================================================

def process_document_background(
    document_id,
    retry_mode="full",
):

    db = SessionLocal()


    try:

        with PROCESSING_LOCK:

            document = (

                db.query(
                    Document
                )

                .filter(
                    Document.document_id
                    == document_id
                )

                .first()

            )


            if not document:

                print(
                    f"[ERROR] "
                    f"{document_id} "
                    f"not found."
                )

                return


            original_path = (
                Path(
                    document.original_path
                )
            )


            if (
                not
                original_path.exists()
            ):

                update_document(
                    db,
                    document,
                    "CV Failed",
                    "—",
                )

                print(
                    f"[ERROR] Original file "
                    f"missing for {document_id}"
                )

                return


            extension = (

                Path(
                    document.stored_filename
                )
                .suffix
                .lower()

            )


            processed_dir = (
                DIGITALIZED_DIR
                / document_id
            )


            processed_dir.mkdir(
                parents=True,
                exist_ok=True,
            )


            print(
                f"[PROCESSING] "
                f"{document_id} "
                f"mode={retry_mode}"
            )


            # ==============================================
            # FULL CV + OCR
            # ==============================================

            if (
                retry_mode
                == "full"
            ):

                try:

                    run_cv(
                        db,
                        document,
                        original_path,
                        extension,
                        processed_dir,
                    )


                except Exception as error:

                    update_document(
                        db,
                        document,
                        "CV Failed",
                        "—",
                    )


                    print(
                        f"[CV ERROR] "
                        f"{document_id}: "
                        f"{error}"
                    )


                    traceback.print_exc()

                    return


            # ==============================================
            # OCR RETRY
            # ==============================================

            elif (
                retry_mode
                == "ocr"
            ):

                existing_pages = [

                    file

                    for file
                    in processed_dir.iterdir()

                    if (
                        file.is_file()
                        and
                        file.suffix.lower()
                        in IMAGE_EXTENSIONS
                    )

                ]


                # If CV pages vanished,
                # automatically rebuild them.

                if not existing_pages:

                    try:

                        run_cv(
                            db,
                            document,
                            original_path,
                            extension,
                            processed_dir,
                        )


                    except Exception as error:

                        update_document(
                            db,
                            document,
                            "CV Failed",
                            "—",
                        )


                        print(
                            f"[CV RETRY ERROR] "
                            f"{document_id}: "
                            f"{error}"
                        )


                        traceback.print_exc()

                        return


            # ==============================================
            # OCR
            # ==============================================

            try:

                ocr_result = run_ocr(
                    db,
                    document,
                    processed_dir,
                )


            except Exception as error:

                update_document(
                    db,
                    document,
                    "OCR Failed",
                    "—",
                )


                print(
                    f"[OCR ERROR] "
                    f"{document_id}: "
                    f"{error}"
                )


                traceback.print_exc()

                return

            # ==============================================
            # INTELLIGENCE PIPELINE (Layout -> ... -> Persist)
            # ==============================================

            try:

                run_intelligence_pipeline(
                    db,
                    document,
                    ocr_result,
                )

            except Exception as error:

                update_document(
                    db,
                    document,
                    "Pipeline Failed",
                    None,
                )

                print(
                    f"[PIPELINE ERROR] "
                    f"{document_id}: "
                    f"{error}"
                )

                traceback.print_exc()

                return


    except Exception as error:

        db.rollback()


        print(
            f"[PIPELINE ERROR] "
            f"{document_id}: "
            f"{error}"
        )


        traceback.print_exc()


    finally:

        db.close()


        remove_active_job(
            document_id
        )


        print(
            f"[PROCESSING] "
            f"{document_id} finished."
        )


# ==========================================================
# HEALTH
# ==========================================================

@app.get("/")
def home():

    return {

        "system":
            "PS 26018",

        "message":
            (
                "Land Record Intelligence "
                "System API is running"
            ),

        "processing_mode":
            "background",

        "max_parallel_processing":
            1,
    }


# ==========================================================
# UPLOAD
# ==========================================================

@app.post(
    "/api/documents/upload",
    status_code=201,
)
async def upload_document(

    background_tasks:
        BackgroundTasks,

    file:
        UploadFile
        = File(...),

    db:
        Session
        = Depends(get_db),

):

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file selected.",
        )


    original_filename = (

        Path(
            file.filename
        )
        .name

    )


    extension = (

        Path(
            original_filename
        )
        .suffix
        .lower()

    )


    if (
        extension
        not in ALLOWED_EXTENSIONS
    ):

        raise HTTPException(

            status_code=400,

            detail=(
                "Only PDF, JPG, JPEG "
                "and PNG files are allowed."
            ),
        )


    document_id = (
        "DOC-"
        +
        uuid.uuid4()
        .hex[:8]
        .upper()
    )


    stored_filename = (
        f"{document_id}"
        f"{extension}"
    )


    original_path = (
        ORIGINAL_DIR
        / stored_filename
    )


    # ======================================================
    # SAVE
    # ======================================================

    try:

        with open(
            original_path,
            "wb",
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer,
            )


    except Exception as error:

        if original_path.exists():

            original_path.unlink()


        raise HTTPException(

            status_code=500,

            detail=(
                f"Could not save document: "
                f"{error}"
            ),
        )


    finally:

        await file.close()


    # ======================================================
    # DB
    # ======================================================

    document = Document(

        document_id=
            document_id,

        original_filename=
            original_filename,

        stored_filename=
            stored_filename,

        original_path=
            str(original_path),

        concise_path=
            None,

        detailed_path=
            None,

        status=
            "Queued",

        confidence=
            "—",

        uploaded_at=
            datetime.now(
                timezone.utc
            ).replace(
                tzinfo=None
            ),
    )


    try:

        db.add(
            document
        )

        db.commit()

        db.refresh(
            document
        )


    except Exception as error:

        db.rollback()


        if original_path.exists():

            original_path.unlink()


        raise HTTPException(

            status_code=500,

            detail=(
                f"Database error: "
                f"{error}"
            ),
        )


    # ======================================================
    # REGISTER JOB
    # ======================================================

    if (
        not
        add_active_job(
            document_id
        )
    ):

        raise HTTPException(

            status_code=409,

            detail=(
                "Document is already processing."
            ),
        )


    background_tasks.add_task(

        process_document_background,

        document_id,

        "full",
    )


    result = (
        serialize_document(
            document
        )
    )


    result.update({

        "processing_started":
            True,

        "message":
            (
                "Document uploaded successfully. "
                "Processing queued."
            ),
    })


    return result


# ==========================================================
# RETRY
# ==========================================================

@app.post(
    "/api/documents/{document_id}/retry",
    status_code=202,
)
def retry_document(

    document_id: str,

    background_tasks:
        BackgroundTasks,

    db:
        Session
        = Depends(get_db),

):

    document = (

        db.query(
            Document
        )

        .filter(
            Document.document_id
            == document_id
        )

        .first()

    )


    if not document:

        raise HTTPException(

            status_code=404,

            detail=(
                "Document not found."
            ),
        )


    if (
        document.status
        not in {
            "CV Failed",
            "OCR Failed",
        }
    ):

        raise HTTPException(

            status_code=400,

            detail=(
                "Retry is only available "
                "for failed documents."
            ),
        )


    if (
        is_active_job(
            document_id
        )
    ):

        raise HTTPException(

            status_code=409,

            detail=(
                "This document is "
                "already processing."
            ),
        )


    if (
        not
        document.original_path
    ):

        raise HTTPException(

            status_code=404,

            detail=(
                "Original document "
                "path is missing."
            ),
        )


    original_path = (
        Path(
            document.original_path
        )
    )


    if (
        not
        original_path.exists()
    ):

        raise HTTPException(

            status_code=404,

            detail=(
                "Original document "
                "file was not found."
            ),
        )


    previous_status = (
        document.status
    )


    retry_mode = (

        "ocr"

        if (
            previous_status
            == "OCR Failed"
        )

        else "full"

    )


    if (
        not
        add_active_job(
            document_id
        )
    ):

        raise HTTPException(

            status_code=409,

            detail=(
                "Document is already processing."
            ),
        )


    try:

        document.status = (
            "Queued"
        )

        document.confidence = (
            "—"
        )


        db.commit()

        db.refresh(
            document
        )


    except Exception as error:

        db.rollback()


        remove_active_job(
            document_id
        )


        raise HTTPException(

            status_code=500,

            detail=(
                f"Could not queue retry: "
                f"{error}"
            ),
        )


    background_tasks.add_task(

        process_document_background,

        document_id,

        retry_mode,
    )


    result = (
        serialize_document(
            document
        )
    )


    result.update({

        "retry_started":
            True,

        "retry_mode":
            retry_mode,

        "message":
            (
                "Document retry queued."
            ),
    })


    return result


# ==========================================================
# DOCUMENT LIST
# ==========================================================

@app.get(
    "/api/documents"
)
def get_documents(

    db:
        Session
        = Depends(get_db),

):

    documents = (

        db.query(
            Document
        )

        .order_by(
            Document.uploaded_at.desc()
        )

        .limit(100)

        .all()

    )


    return [

        serialize_document(
            document
        )

        for document
        in documents

    ]


# ==========================================================
# SINGLE DOCUMENT
# ==========================================================

@app.get(
    "/api/documents/{document_id}"
)
def get_document(

    document_id: str,

    db:
        Session
        = Depends(get_db),

):

    document = (

        db.query(
            Document
        )

        .filter(
            Document.document_id
            == document_id
        )

        .first()

    )


    if not document:

        raise HTTPException(

            status_code=404,

            detail=(
                "Document not found."
            ),
        )


    result = (
        serialize_document(
            document
        )
    )


    ocr_path = (

        DIGITALIZED_DIR

        / document_id

        / "ocr_result.json"

    )


    result[
        "ocr_result_exists"
    ] = (
        ocr_path.exists()
    )


    result[
        "ocr_result_path"
    ] = (

        str(ocr_path)

        if ocr_path.exists()

        else None

    )


    result[
        "processing_active"
    ] = (
        is_active_job(
            document_id
        )
    )


    result[
        "can_retry"
    ] = (

        document.status
        in {
            "CV Failed",
            "OCR Failed",
        }

        and

        not is_active_job(
            document_id
        )
    )


    return result