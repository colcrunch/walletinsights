from . import __version__
from esi.clients import EsiClientProvider

esi = EsiClientProvider(app_info_text=f"walletinsights v{__version__}")
