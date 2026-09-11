import uuid
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.api.documents import _user_dir
from app.models.client import Client
from app.models.document import Document


def deposer_rapport(db: Session, client: Client, periode: tuple[date, date], nom_fichier: str, contenu_pdf: bytes) -> Optional[Document]:
    """Dépose le rapport PDF généré directement sur le compte du client, s'il en a un.

    Remplace l'ancien pont HTTP ForfaitFlow -> espace-client : tout se passe
    ici en base et sur le disque de stockage partagé, dans le même process,
    plus besoin d'appel réseau ni d'identifiants de service.

    Ne fait rien si le client n'a pas de compte de connexion (`user_id` NULL)
    — reproduit le comportement de l'ancien pont, qui ignorait silencieusement
    les clients sans compte espace-client plutôt que d'échouer.
    """
    if client.user_id is None:
        return None

    periode_debut, _ = periode
    stored_name = f"{uuid.uuid4().hex}.pdf"
    dest = _user_dir(client.user_id) / stored_name
    dest.write_bytes(contenu_pdf)

    document = Document(
        user_id=client.user_id,
        client_id=client.id,
        document_type="rapport_intervention",
        period_label=f"{periode_debut.year:04d}-{periode_debut.month:02d}",
        filename=stored_name,
        original_filename=nom_fichier,
        file_path=str(dest),
        file_size=len(contenu_pdf),
        mime_type="application/pdf",
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document
