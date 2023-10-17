from allianceauth.eveonline.models import EveCorporationInfo, EveCharacter
from django.db import models
from django.utils.translation import gettext_lazy as _
from esi.models import Token

from .providers import REQUIRED_SCOPES
from .managers import OwnerManager


class General(models.Model):
    """
    This class exists purely for permissions.

    By default, anyone with access to the module can see the data for their own corp (based on main)
    """
    class Meta:
        managed = False
        default_permissions = (())
        permissions = (
            ("access_walletinsights", "Allows access to the WalletInsights module."),
            ("all_corp_access", "Allows access to wallet data for all corps."),
            ("add_wallet_owner", "Can add a wallet owner.")
        )


class Owner(models.Model):
    """
    Owning corporation of a wallet.
    """

    objects = OwnerManager()

    corp = models.ForeignKey(
        to=EveCorporationInfo,
        on_delete=models.CASCADE,
        related_name="wallet_owner",
        verbose_name=_("corporation"),
        help_text=_("Corporation that owns wallets.")
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("is active"),
        help_text=_("Determines if the corp wallets for this owner will be updated in the sync task.")
    )

    balances_last_updated = models.DateTimeField(
        null=True,
        default=None,
        blank=True,
        verbose_name=_("balances last updated"),
        help_text=_("the last date and time that wallet balances were updated.")
    )

    journals_last_updated = models.DateTimeField(
        null=True,
        default=None,
        blank=True,
        verbose_name=_("journals last updated"),
        help_text=_("the last date and time that the journals were updated")
    )

    class Meta:
        default_permissions = (())
        verbose_name = _("owner")
        verbose_name_plural = _("owners")


class OwnerCharacter(models.Model):
    """
    Character to be used to sync data for related owner.
    """
    owner = models.ForeignKey(
        to=Owner,
        on_delete=models.CASCADE,
        related_name="characters",
        verbose_name=_("owner")
    )

    character = models.ForeignKey(
        to=EveCharacter,
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name=_("character"),
        help_text=_("character used for syncing")
    )

    last_used = models.DateTimeField(
        null=True,
        default=None,
        editable=False,
        db_index=True,
        verbose_name=_("last used"),
        help_text=_("the last time this character was used for syncing")
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def valid_token(self):
        """
        Provide a token, or return None if one can not be found.
        """
        return (
            Token.objects.filter(character_id=self.character.character_id)
            .require_scopes(REQUIRED_SCOPES)
            .require_valid()
            .first()
        )

    class Meta:
        default_permissions = (())
        verbose_name = _("owner character")
        verbose_name_plural = _("owner characters")


class WalletDivision(models.Model):
    """
    Supplied by /corporations/{corporation_id}/divisions/
    """
    corp = models.ForeignKey(to=Owner, on_delete=models.CASCADE)
    division_id = models.SmallIntegerField()
    division_name = models.CharField(max_length=100)

    class Meta:
        default_permissions = (())
        unique_together = ["corp_id", "division_id"]
        indexes = [
            models.Index(fields=["corp_id", "division_id"], name="corp_division_id_idx"),
            models.Index(fields=["division_id", "division_name"], name="division_division_name_idx"),
            models.Index(fields=["corp_id", "division_name"], name="corp_division_name_idx"),
            models.Index(fields=["corp_id"], name="corp_id_idx")
        ]
        verbose_name = _("wallet division")
        verbose_name_plural = _("wallet divisions")


class WalletBalanceRecord(models.Model):
    """
    Supplied by /corporations/{corporation_id}/wallets/
    """
    division = models.ForeignKey(to=WalletDivision, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=20, decimal_places=2, null=False)
    time = models.DateTimeField(auto_now_add=True)

    class Meta:
        default_permissions = (())
        verbose_name = _("wallet balance record")
        verbose_name_plural = _("wallet balance records")


class WalletJournalEntry(models.Model):
    """
    Supplied by /corporations/{corporation_id}/wallets/{division}/journal/
    """
    division = models.ForeignKey(to=WalletDivision, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    balance = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    context_id = models.BigIntegerField(null=True)
    context_id_type = models.CharField(null=True)
    date = models.DateTimeField(null=False)
    description = models.CharField(max_length=500, null=False)
    first_party_id = models.IntegerField(null=True)
    entry_id = models.BigIntegerField(null=False)
    reason = models.CharField(max_length=500, null=True)
    ref_type = models.CharField(max_length=72, null=False)
    second_party_id = models.IntegerField(null=True)
    tax = models.DecimalField(max_digits=20, decimal_places=2, null=True)
    tax_receiver_id = models.IntegerField(null=True)

    class Meta:
        default_permissions = (())
        verbose_name = _("wallet journal entry")
        verbose_name_plural = _("wallet journal entries")
