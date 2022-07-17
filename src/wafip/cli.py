import fire
from .ipset import WafIp, WafRepository


class Cli:
    def __init__(self, ipset: str, profile: str = "default", region: str = "ap-northeast-1") -> None:
        self._wafrepo = WafRepository(profile_name=profile, region=region)
        self._wafip = WafIp(ipset_name=ipset)

    def add(self, ips: str):
        _ips = ips.split(",")
        try:
            self._wafip.add(_ips, self._wafrepo)
        except Exception as e:
            print(e)

    def delete(self, ips: str):
        _ips = ips.split(",")
        try:
            self._wafip.delete(_ips, self._wafrepo)
        except Exception as e:
            print(e)


def cli():
    fire.Fire(Cli)
