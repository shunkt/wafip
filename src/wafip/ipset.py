from dataclasses import dataclass
from typing import Literal, TypedDict
from boto3.session import Session
import botocore.exceptions
from ipaddress import IPv4Interface
from . import utils
from .exceptions import IpsetNotFoundError, NonexistentIpError, DuplicateIpError


class IpSetInList(TypedDict):
    Name: str
    Id: str
    Description: str
    LockToken: str
    ARN: str


class ListIpSetResponseOptional(TypedDict, total=False):
    NextMarker: str


class ListIpSetResponse(ListIpSetResponseOptional):
    IPSets: list[IpSetInList]


class IpSetInGet(TypedDict):
    Name: str
    Id: str
    ARN: str
    Description: str
    IPAddressVersion: Literal["IPV4", "IPV6"]
    Addresses: list[str]


class GetIpSetResponse(TypedDict):
    IPSet: IpSetInGet
    LockToken: str


@dataclass
class IpSet:
    name: str
    id: str
    arn: str
    desc: str
    addresses: list[str]
    ip_address_version: Literal["IPV4", "IPV6"]
    lock_token: str
    scope: Literal["CLOUDFRONT", "REGIONAL"]

    def add_ip(self, ips: list[IPv4Interface]):
        for ip in ips:
            if str(ip.network) in self.addresses:
                raise DuplicateIpError(str(ip.network))
        self.addresses.extend([str(ip.network) for ip in ips])

    def remove_ip(self, ips: list[IPv4Interface]):
        for ip in ips:
            if str(ip.network) not in self.addresses:
                raise NonexistentIpError(str(ip.network))
        for ip in ips:
            self.addresses.remove(str(ip.network))

    def to_update_request_params(self):
        return {
            "Name": self.name,
            "Scope": self.scope,
            "Id": self.id,
            "Addresses": self.addresses,
            "LockToken": self.lock_token
        }


class WafRepository:
    SCOPE: Literal['CLOUDFRONT', 'REGIONAL'] = "REGIONAL"

    def __init__(self, profile_name: str, region: str) -> None:
        sess = Session(
            profile_name=profile_name,
            region_name=region,
        )
        self.client = sess.client("wafv2")

    def get_ipset_repr(self, ipset_name: str) -> IpSet:
        is_continue = True
        marker = None
        while is_continue:
            params = {
                "Scope": self.__class__.SCOPE
            }
            if marker:
                params["NextMarker"] = marker

            response: ListIpSetResponse = self.client.list_ip_sets(
                **params
            )

            for ipset in response["IPSets"]:
                if ipset_name == ipset["Name"]:
                    ipset_detail: GetIpSetResponse = self.client.get_ip_set(
                        Name=ipset["Name"],
                        Scope=self.__class__.SCOPE,
                        Id=ipset["Id"]
                    )

                    return IpSet(
                        id=ipset_detail["IPSet"]["Id"],
                        name=ipset_name,
                        arn=ipset_detail["IPSet"]["ARN"],
                        desc=ipset_detail["IPSet"]["Description"],
                        addresses=ipset_detail["IPSet"]["Addresses"],
                        ip_address_version=ipset_detail["IPSet"]["IPAddressVersion"],
                        lock_token=ipset_detail["LockToken"],
                        scope=self.__class__.SCOPE,
                    )
        raise IpsetNotFoundError(ipset=ipset_name)

    def update_regional_ipset(self, ipset_name: str, ips: list[IPv4Interface], op: Literal["ADD", "DEL"]):
        ipset = self.get_ipset_repr(ipset_name)
        if op == "ADD":
            ipset.add_ip(ips=ips)
            self.client.update_ip_set(**ipset.to_update_request_params())
        elif op == "DEL":
            ipset.remove_ip(ips)
            self.client.update_ip_set(**ipset.to_update_request_params())

    def exsits_in_ipset(self, ipset_name: str, ip: IPv4Interface) -> bool:
        try:
            ipset = self.get_ipset_repr(ipset_name)
            return str(ip.network) in ipset.addresses
        except:
            return False


class WafIp:
    def __init__(self, ipset_name: str) -> None:
        self._ipset_name = ipset_name
        self._exponential_backoff = None

    def add(self, ips: list[str], waf_repo: WafRepository) -> None:
        """
        Raises:
            ipaddress.AddressValueError: アドレスに関する不正な値
            ipaddress.NetmaskValueError: ネットマスクに関する不正な値
            wafip.exceptions.IpsetNotFoundError: IP setが存在しない
            WAFV2.Client.exceptions.WAFInternalErrorException
            WAFV2.Client.exceptions.WAFInvalidParameterException
            WAFV2.Client.exceptions.WAFNonexistentItemException
            WAFV2.Client.exceptions.WAFDuplicateItemException
            WAFV2.Client.exceptions.WAFOptimisticLockException
            WAFV2.Client.exceptions.WAFLimitsExceededException
            WAFV2.Client.exceptions.WAFInvalidOperationException
        """
        for _ in utils.exponential_backoff(3):
            try:
                waf_repo.update_regional_ipset(
                    self._ipset_name, [IPv4Interface(ip) for ip in ips], "ADD"
                )
                break
            except botocore.exceptions.ClientError as e:
                if e.response["Error"]["Code"] in ["WAFOptimisticLockException", "WAFLimitsExceededException"]:
                    continue
                if e.response["Error"]["Code"] in ["WAFDuplicateItemException"]:
                    break
                raise e

    def delete(self, ips: list[str], waf_repo: WafRepository) -> None:
        """
        Raises:
            ipaddress.AddressValueError: アドレスに関する不正な値
            ipaddress.NetmaskValueError: ネットマスクに関する不正な値
            wafip.exceptions.IpsetNotFoundError: IP setが存在しない
            WAFV2.Client.exceptions.WAFInternalErrorException
            WAFV2.Client.exceptions.WAFInvalidParameterException
            WAFV2.Client.exceptions.WAFNonexistentItemException
            WAFV2.Client.exceptions.WAFDuplicateItemException
            WAFV2.Client.exceptions.WAFOptimisticLockException
            WAFV2.Client.exceptions.WAFLimitsExceededException
            WAFV2.Client.exceptions.WAFInvalidOperationException
        """
        for _ in utils.exponential_backoff(3):
            try:
                waf_repo.update_regional_ipset(
                    self._ipset_name, [IPv4Interface(ip) for ip in ips], "DEL"
                )
                break
            except botocore.exceptions.ClientError as e:
                if e.response["Error"]["Code"] in ["WAFOptimisticLockException", "WAFLimitsExceededException"]:
                    continue
                if e.response["Error"]["Code"] in ["WAFNonexistentItemException"]:
                    break
                raise e
