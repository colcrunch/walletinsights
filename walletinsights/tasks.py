from datetime import timedelta

from allianceauth.services.hooks import get_extension_logger
from celery import shared_task, chain
from django.utils.timezone import now
from esi.models import Token

from .providers import esi
from .models import Owner, OwnerCharacter, WalletDivision, WalletBalanceRecord, WalletJournalEntry

logger = get_extension_logger(__name__)


def __get_least_recently_used_token(owner_corp_id):
    """
    Returns the token for the owner that has been used least recently.
    :param owner_corp_id:
    :return:
    """
    chars = (
        OwnerCharacter
        .objects
        .filter(owner__corp__corporation_id=owner_corp_id)
        .exclude(is_valid=False)
        .order_by("last_used")
    )

    token = None
    for char in chars:
        token = char.valid_token()
        if token:
            break
        else:
            # If we find no valid tokens for this char, mark it as invalid.
            char.is_valid = False
            char.save()

    return token


@shared_task()
def update_all_owners():
    """
    Update wallet data for all owners.
    :return:
    """
    logger.debug("Update all owners task started!")
    owners = Owner.objects.all()
    for owner in owners:
        update_owner.delay(owner.corp.corporation_id)


@shared_task()
def update_owner(owner_corp_id):
    """
    Update wallet data for a specific owner.
    :param owner_corp_id:
    :return:
    """
    logger.debug(f"Updating wallet data for owner {owner_corp_id}")
    owner = Owner.objects.get(corp__corporation_id=owner_corp_id)
    if not owner.is_active:
        logger.debug(f"{owner_corp_id} marked as not active. Skipping.")
        return
    token = __get_least_recently_used_token(owner_corp_id)
    chain(update_owner_divisions.si(owner_corp_id, token.pk), update_owner_journals.si(owner_corp_id, token.pk)).delay()


@shared_task()
def update_owner_divisions(owner_corp_id, token_id=None):
    """
    Update wallet divisions for an owner
    :param owner_corp_id:
    :param token_id: default: None
    :return:
    """
    owner = Owner.objects.get(corp__corporation_id=owner_corp_id)
    if not token_id:
        token = __get_least_recently_used_token(owner_corp_id)
    else:
        token = Token.objects.get(pk=token_id)

    if owner.balances_last_updated is None or owner.balances_last_updated + timedelta(hours=1) <= now():
        # Only request new division name data if the cache is expired. (Division names are cached for 3600s)
        division_data = esi.client.Corporation.get_corporations_corporation_id_divisions(
            corporation_id=owner_corp_id,
            token=token.valid_access_token()
        ).result()

        for division in division_data["wallet"]:
            # 1st division never returns a name and is always the master wallet.
            if division["division"] == 1:
                division["name"] = "Master Wallet"
            elif "name" not in list(division.keys()) or division["name"] is None:
                division["name"] = f"Division {division['division']}"
            WalletDivision.objects.update_or_create(
                corp=owner,
                division_id=division["division"],
                division_name=division["name"]
            )

    update_division_balances.delay(owner_corp_id, token.pk)


@shared_task()
def update_division_balances(owner_corp_id, token_id=None):
    """
    Updates the balances for wallet divisions.
    :param owner_corp_id:
    :param token_id: default: None
    :return:
    """
    if not token_id:
        token = __get_least_recently_used_token(owner_corp_id)
    else:
        token = Token.objects.get(pk=token_id)
    divisions = WalletDivision.objects.filter(corp__corp__corporation_id=owner_corp_id).order_by("division_id")

    data = esi.client.Wallet.get_corporations_corporation_id_wallets(
        corporation_id=owner_corp_id,
        token=token.valid_access_token()
    ).result()

    for d in data:
        division = divisions[d["division"]-1]
        balance = d["balance"]
        WalletBalanceRecord.objects.create(
            division=division,
            balance=balance
        )

    owner = divisions[1].corp
    owner.balances_last_updated = now()
    owner.save()

    update_ownerchar_last_used.delay(token.character_id)


@shared_task()
def update_owner_journals(owner_corp_id, token_id=None):
    """
    Updates journal data for all divisions of a corp wallet.
    :param owner_corp_id:
    :param token_id:
    :return:
    """
    if not token_id:
        token = __get_least_recently_used_token(owner_corp_id)
    else:
        token = Token.objects.get(pk=token_id)

    divisions = WalletDivision.objects.filter(corp__corp__corporation_id=owner_corp_id)

    if len(divisions) == 0:
        logger.warning(f"Divisions not loaded for {owner_corp_id}, run the division update task first, and try again!")
        return

    for division in divisions:
        update_owner_division_journal.delay(owner_corp_id, division.pk, token.pk)


@shared_task()
def update_owner_division_journal(owner_corp_id, division_pk, token_id=None):
    """
    Updates journal data for a specific division
    :param owner_corp_id:
    :param division:
    :param token_id:
    :return:
    """
    if not token_id:
        token = __get_least_recently_used_token(owner_corp_id)
    else:
        token = Token.objects.get(pk=token_id)

    division = WalletDivision.objects.get(pk=division_pk)

    entries = esi.client.Wallet.get_corporations_corporation_id_wallets_division_journal(
        corporation_id=owner_corp_id,
        division=division.division_id,
        token=token.valid_access_token()
    ).results()

    for entry in entries:
        entry_id = entry.pop("id")
        WalletJournalEntry.objects.update_or_create(
            division=division,
            entry_id=entry_id,
            **entry
        )

    division.journal_last_updated = now()
    division.save()
    update_ownerchar_last_used.delay(token.character_id)


@shared_task()
def update_ownerchar_last_used(character_id):
    OwnerCharacter.objects.filter(character__character_id=character_id).update(last_used=now())
    return
