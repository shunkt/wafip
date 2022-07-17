class IpsetNotFoundError(Exception):
    def __init__(self, ipset: str, *args: object) -> None:
        super().__init__(*args)
        self._ipset = ipset

    def __str__(self) -> str:
        return f"IPsetの中に{self._ipset}が存在しません"


class NonexistentIpError(Exception):
    def __init__(self, ip: str,  *args: object) -> None:
        super().__init__(*args)
        self._ip = ip

    def __str__(self) -> str:
        return f"{self._ip}は登録されていません"


class DuplicateIpError(Exception):
    def __init__(self, ip: str, *args: object) -> None:
        super().__init__(*args)
        self._ip = ip

    def __str__(self) -> str:
        return f"{self._ip}は既に登録されています"
