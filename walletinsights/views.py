from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from esi.decorators import token_required
from allianceauth.eveonline.models import EveCharacter
from allianceauth.services.hooks import get_extension_logger

from .providers import REQUIRED_SCOPES
from .models import Owner, OwnerCharacter


logger = get_extension_logger(__name__)


@login_required()
@permission_required("walletinsights.access_walletinsights")
def dashboard(request):
    pass


@login_required()
@token_required(scopes=REQUIRED_SCOPES)
@permission_required("walletinsights.add_wallet_owner")
def add_owner(request, token):
    """
    View for adding an owner character. If an owner does not already exist for the character,
    also creates an owner.

    TODO: Once task is written to pull data, initiate it when adding a new character.
    :param request:
    :param token:
    :return:
    """
    eve_char = EveCharacter.objects.get(character_id=token.character_id)
    if not OwnerCharacter.objects.filter(character=eve_char).exists():
        # Check for Owner
        owner = Owner.objects.get_or_create_owner(corp_id=eve_char.corporation_id)
        o = OwnerCharacter(
            owner=owner,
            character=eve_char
        )
        o.save()
        messages.success(request, _("Success! Owner added."))
    else:
        messages.info(request, _("Owner character already exists."))
    return redirect("walletinsights:dashboard")