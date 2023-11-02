from django.db import models

from allianceauth.eveonline.models import EveCorporationInfo
from allianceauth.services.hooks import get_extension_logger


logger = get_extension_logger(__name__)


class OwnerManager(models.Manager):
    def get_or_create_owner(self, corp_id):
        o = self.filter(corp__corporation_id=corp_id)
        if not o.exists():
            return self.create_owner(corp_id)
        return o.first()

    def create_owner(self, corp_id):
        """
        Creates owner object.
        :param corp_id:
        :return:
        """

        # Ensure a corp info model exists.
        if not EveCorporationInfo.objects.filter(corporation_id=corp_id).exists():
            EveCorporationInfo.objects.create_corporation(corp_id)

        corp = EveCorporationInfo.objects.get(corporation_id=corp_id)
        return self.create(
            corp=corp,
        )
