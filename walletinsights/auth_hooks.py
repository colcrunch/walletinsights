from allianceauth import hooks
from allianceauth.services.hooks import MenuItemHook, UrlHook

from . import urls


class WalletMenu(MenuItemHook):
    def __init__(self):
        MenuItemHook.__init__(
            self,
            "Corp Wallets",
            "fas fa-shekel-sign fa-fw",
            "walletinsights:dashboard",
            navactive=["walletinsights:"]
        )


@hooks.register("menu_item_hook")
def register_menu():
    return WalletMenu()


@hooks.register("url_hook")
def register_url():
    return UrlHook(urls, "walletinsights", "^walletinsights/")
