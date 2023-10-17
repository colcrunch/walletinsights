from . import __version__
from esi.clients import EsiClientProvider

REQUIRED_SCOPES = (
    "esi-wallet.read_corporation_wallets.v1",
    "esi-corporations.read_divisions.v1"
)

esi = EsiClientProvider(app_info_text=f"walletinsights v{__version__}")
