import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_org, get_current_staff
from app.database import get_db
from app.models.organization import Organization
from app.services.clients import get_client_or_404
from app.services.export import construire_rapport, generer_excel, generer_pdf, nom_fichier_sur
from app.services.periode import periode_courante, trouver_periode
from app.services.rapports_documents import deposer_rapport

router = APIRouter(prefix="/api/rapports", tags=["rapports"], dependencies=[Depends(get_current_staff)])
logger = logging.getLogger("app.rapports")


def _get_client_et_rapport(client_id: int, periode: str, org: Organization, db: Session) -> dict:
    client = get_client_or_404(client_id, org, db)

    if periode == "courante":
        periode_dates = periode_courante(client.date_debut_contrat)
    else:
        trouvee = trouver_periode(client.date_debut_contrat, periode)
        if trouvee is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Periode introuvable (attendu 'courante' ou 'yyyy-mm')",
            )
        _, debut, fin = trouvee
        periode_dates = (debut, fin)

    return construire_rapport(db, client, periode_dates)


@router.get("/{client_id}/pdf")
def get_rapport_pdf(
    client_id: int,
    periode: str = "courante",
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    data = _get_client_et_rapport(client_id, periode, org, db)
    pdf_bytes = generer_pdf(data)
    filename = f"rapport_{nom_fichier_sur(data['client'].nom)}_{data['periode_debut']}.pdf"

    try:
        deposer_rapport(
            db,
            data["client"],
            (data["periode_debut"], data["periode_fin"]),
            filename,
            pdf_bytes,
        )
    except Exception:
        # Best-effort : le dépôt sur le compte client ne doit jamais faire
        # échouer le téléchargement du rapport.
        logger.exception("Échec du dépôt du rapport %s sur le compte client", filename)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{client_id}/xlsx")
def get_rapport_xlsx(
    client_id: int,
    periode: str = "courante",
    org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    data = _get_client_et_rapport(client_id, periode, org, db)
    xlsx_bytes = generer_excel(data)
    filename = f"rapport_{nom_fichier_sur(data['client'].nom)}_{data['periode_debut']}.xlsx"
    return Response(
        content=xlsx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
