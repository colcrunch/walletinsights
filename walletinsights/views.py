from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from esi.decorators import token_required
from allianceauth.eveonline.models import EveCharacter
from allianceauth.services.hooks import get_extension_logger

from .providers import REQUIRED_SCOPES
from .models import Owner, OwnerCharacter
from .tasks import update_owner


logger = get_extension_logger(__name__)


@login_required()
@permission_required("walletinsights.access_walletinsights")
def dashboard(request):
    main_corp_id = request.user.profile.main_character.corporation_id
    select_criteria = {
        "master_division_id": (
            "SELECT id FROM walletinsights_walletdivision "
            "WHERE walletinsights_walletdivision.corp_id = walletinsights_owner.id "
            "AND walletinsights_walletdivision.division_id = 1"
        ),
        "master_wallet_balance": (
            "SELECT balance FROM walletinsights_walletbalancerecord "
            "WHERE walletinsights_walletbalancerecord.division_id = master_division_id "
            "ORDER BY time DESC LIMIT 1"
        )
    }

    main_owner = Owner.objects.filter(corp__corporation_id=main_corp_id).extra(select=select_criteria).first()

    if request.user.has_perm("walletinsights.all_corp_access"):
        owners = Owner.objects.all().exclude(corp__corporation_id=main_corp_id).extra(select=select_criteria)
    else:
        owners = Owner.objects.none()

    ctx = {
        'main_corp': main_owner,
        "owners": owners,
    }
    return render(request, 'walletinsights/dash.html', ctx)


@login_required()
@token_required(scopes=REQUIRED_SCOPES)
@permission_required("walletinsights.add_wallet_owner")
def add_owner(request, token):
    """
    View for adding an owner character. If an owner does not already exist for the character,
    also creates an owner.
    :param request:
    :param token:
    :return:
    """
    eve_char = EveCharacter.objects.get(character_id=token.character_id)
    if not OwnerCharacter.objects.filter(character=eve_char).exists():
        # Check for Owner
        owner, owner_created = Owner.objects.get_or_create_owner(corp_id=eve_char.corporation_id)
        o = OwnerCharacter(
            owner=owner,
            character=eve_char
        )
        o.save()
        if owner_created:
            update_owner.delay(owner.corp.corporation_id)
            messages.success(request, _("Success! Owner added."))
        else:
            messages.success(request, _("Owner character added!"))
    elif OwnerCharacter.objects.filter(character=eve_char, is_valid=False).exists():
        # Update the inactive OwnerCharacter to be marked as active.
        char = OwnerCharacter.objects.get(character=eve_char)
        char.is_valid = True
        char.save()
        messages.success(request, _("Success! Existing owner character reactivated."))
    else:
        messages.info(request, _("Owner character already exists."))
    return redirect("walletinsights:dashboard")