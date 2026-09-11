import uuid
from pathlib import Path

import magic
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import get_current_user
from app.database import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentOut

router = APIRouter(prefix="/api/documents", tags=["documents"])

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

# .docx/.xlsx sont des zip : libmagic ne voit que "application/zip" sur la
# seule signature binaire, sans inspecter le contenu interne du zip. On les
# accepte donc sur la déclaration du client dans ce seul cas précis — le
# vrai filtre pour tous les autres types (dont les exécutables déguisés en
# PDF) reste la signature réelle détectée ci-dessous, jamais le Content-Type.
_ZIP_BASED_OFFICE_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def _signature_correspond_au_type_declare(contenu: bytes, content_type: str) -> bool:
    detecte = magic.from_buffer(contenu, mime=True)
    if detecte == content_type:
        return True
    return detecte == "application/zip" and content_type in _ZIP_BASED_OFFICE_TYPES


def _user_dir(user_id: int) -> Path:
    directory = Path(settings.upload_dir) / f"user_{user_id}"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


@router.get("", response_model=list[DocumentOut])
def list_documents(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    document_type: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Document).filter(Document.user_id == current_user.id)
    if document_type is not None:
        query = query.filter(Document.document_type == document_type)
    return query.order_by(Document.uploaded_at.desc()).offset(skip).limit(limit).all()


async def save_uploaded_document(file: UploadFile, target_user_id: int, db: Session) -> Document:
    """Logique d'enregistrement partagée entre l'upload en self-service
    (client sur son propre compte) et l'upload admin (sur le compte d'un
    client, ex. dépôt d'un rapport d'intervention)."""
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Type de fichier non autorisé")

    suffix = Path(file.filename or "").suffix[:16]
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    dest = _user_dir(target_user_id) / stored_name

    size = 0
    first_chunk = True
    try:
        with dest.open("wb") as out:
            while chunk := await file.read(1024 * 1024):
                if first_chunk:
                    first_chunk = False
                    if not _signature_correspond_au_type_declare(chunk, file.content_type):
                        out.close()
                        dest.unlink(missing_ok=True)
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Le contenu du fichier ne correspond pas au type déclaré",
                        )
                size += len(chunk)
                if size > settings.max_file_size:
                    out.close()
                    dest.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="Fichier trop volumineux (50 Mo max)",
                    )
                out.write(chunk)
    except HTTPException:
        raise
    except OSError:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Échec de l'enregistrement du fichier")

    document = Document(
        user_id=target_user_id,
        filename=stored_name,
        original_filename=file.filename or stored_name,
        file_path=str(dest),
        file_size=size,
        mime_type=file.content_type or "application/octet-stream",
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.post("", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return await save_uploaded_document(file, current_user.id, db)


def _get_owned_document(document_id: int, current_user: User, db: Session) -> Document:
    document = db.get(Document, document_id)
    if document is None or document.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document introuvable")
    return document


@router.get("/{document_id}")
def download_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = _get_owned_document(document_id, current_user, db)
    path = Path(document.file_path)
    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fichier introuvable sur le disque")
    return FileResponse(
        path,
        media_type=document.mime_type,
        filename=document.original_filename,
    )


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = _get_owned_document(document_id, current_user, db)
    Path(document.file_path).unlink(missing_ok=True)
    db.delete(document)
    db.commit()
    return {"status": "deleted", "id": document_id}
