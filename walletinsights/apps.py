from django.apps import AppConfig
from . import __version__


class WalletConfig(AppConfig):
    name = 'walletinsights'
    verbose_name = f"Wallet Insights v{__version__}"