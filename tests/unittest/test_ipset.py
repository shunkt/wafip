from src.wafip.ipset import IpSet
from src.wafip.exceptions import NonexistentIpError, DuplicateIpError
from ipaddress import IPv4Interface
import pytest
ipset_name = "testipset"
ipset_id = "xxxx"
ipset_arn = f"arn:aws:waf:ap-northeast-1:123456890:{ipset_name}"
ipset_desc = "description"


class TestIpSet:
    def test_add_one_new_ip(self):
        """
        """
        ip = "10.0.0.1/32"
        ipset = IpSet(
            ipset_name,
            ipset_id,
            ipset_arn,
            ipset_desc,
            [ip],
            "IPV4",
            "xxx",
            "REGIONAL"
        )
        new_ip = IPv4Interface("10.0.0.2/32")
        ipset.add_ip([new_ip])
        assert ipset.addresses == [ip, str(new_ip)]

    def test_add_two_new_ip(self):
        ip = "10.0.0.1/32"
        ipset = IpSet(
            ipset_name,
            ipset_id,
            ipset_arn,
            ipset_desc,
            [ip],
            "IPV4",
            "xxx",
            "REGIONAL"
        )
        new_ip_1 = IPv4Interface("10.0.0.2/32")
        new_ip_2 = IPv4Interface("10.0.0.3/32")
        ipset.add_ip([new_ip_1, new_ip_2])
        assert ipset.addresses == [ip, str(new_ip_1), str(new_ip_2)]

    def test_add_exist_ip(self):
        ip = "10.0.0.1/32"
        ipset = IpSet(
            ipset_name,
            ipset_id,
            ipset_arn,
            ipset_desc,
            [ip],
            "IPV4",
            "xxx",
            "REGIONAL"
        )

        exsited_ip = IPv4Interface(ip)
        with pytest.raises(DuplicateIpError):
            ipset.add_ip([exsited_ip])
        assert ipset.addresses == [ip]

    def test_add_ip_without_networkmask(self):
        ipset = IpSet(
            ipset_name,
            ipset_id,
            ipset_arn,
            ipset_desc,
            [],
            "IPV4",
            "xxx",
            "REGIONAL"
        )

        ip = "10.0.0.1"
        ipset.add_ip([IPv4Interface(ip)])

        assert ipset.addresses == [f"{ip}/32"]

    def test_remove_one_ip(self):
        ip = "10.0.0.1/32"
        ipset = IpSet(
            ipset_name,
            ipset_id,
            ipset_arn,
            ipset_desc,
            [ip],
            "IPV4",
            "xxx",
            "REGIONAL"
        )
        ipset.remove_ip([IPv4Interface(ip)])
        assert ipset.addresses == []

    def test_remove_two_ip(self):
        ip1 = "10.0.0.1/32"
        ip2 = "10.0.0.2/32"
        ip3 = "10.0.0.3/32"
        ipset = IpSet(
            ipset_name,
            ipset_id,
            ipset_arn,
            ipset_desc,
            [ip1, ip2, ip3],
            "IPV4",
            "xxx",
            "REGIONAL"
        )

        ipset.remove_ip([IPv4Interface(ip1), IPv4Interface(ip2)])
        assert ipset.addresses == [ip3]

    def test_remove_non_exist_ip(self):
        ip = "10.0.0.1/32"
        ipset = IpSet(
            ipset_name,
            ipset_id,
            ipset_arn,
            ipset_desc,
            [ip],
            "IPV4",
            "xxx",
            "REGIONAL"
        )

        with pytest.raises(NonexistentIpError):
            ipset.remove_ip([IPv4Interface("10.0.0.2/32")])

        assert ipset.addresses == [ip]

    def test_to_update_request_params(self):
        ip = "10.0.0.1/32"
        ipset = IpSet(
            ipset_name,
            ipset_id,
            ipset_arn,
            ipset_desc,
            [ip],
            "IPV4",
            "xxx",
            "REGIONAL"
        )
        assert ipset.to_update_request_params() == {
            "Name": ipset_name,
            "Scope": "REGIONAL",
            "Id": ipset_id,
            "Description": ipset_desc,
            "Addresses": [ip],
            "LockToken": "xxx"
        }
