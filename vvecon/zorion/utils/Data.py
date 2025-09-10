from dataclasses import dataclass

__all__ = ['Aside', 'Data', 'Dictionary', 'Footer', 'Header', 'Meta', 'Navigator', 'Settings', 'Tracking']



@dataclass
class Settings:
    head: str
    app_name: str
    app_icon: str
    site_name: str
    logo: str = NotImplemented
    mobileNumber: str = NotImplemented
    site: str = NotImplemented
    address: str = NotImplemented
    email: str = NotImplemented


@dataclass
class Meta:
    description: str
    keywords: list


@dataclass
class Tracking:
    enabled: bool = False
    google: str = NotImplemented
    hotjar: int = NotImplemented
    facebook: int = NotImplemented


@dataclass
class Navigator:
    enabled: bool = True
    navType: int = 1
    activeTab: str = 'home'


@dataclass
class Header:
    enabled: bool = True
    headerType: int = 1
    listProduct: bool = False

    def setKey(self, key, value):
        setattr(self, key, value)


@dataclass
class Aside:
    enabled: bool = True
    asideType: int = 1
    activeSlug: str = 'home'
    content: dict = NotImplemented


@dataclass
class Footer:
    enabled: bool = True
    footerType: int = 1

    def setKey(self, key, value):
        setattr(self, key, value)


class Data:
    settings: dict[Settings] = NotImplemented
    meta: dict[Meta] = NotImplemented
    tracking: Tracking = NotImplemented

    header: dict[Header] = NotImplemented
    navigator: dict[Navigator] = NotImplemented
    aside: dict[Aside] = NotImplemented
    footer: dict[Footer] = NotImplemented


class Dictionary:

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.__dict__ = kwargs

    def __str__(self):
        return str(self.__dict__)

    def setKey(self, key, value):
        setattr(self, key, value)
        self.__dict__[key] = value
