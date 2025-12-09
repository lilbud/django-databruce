from databruce import models


def get_band_members(band_id: int, event_id: str):
    return models.Onstage.objects.filter(event=event_id, band=band_id).select_related(
        "band", "event"
    )
