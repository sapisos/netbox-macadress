"""
GraphQL schema for NetBox macadress.
"""

import strawberry
import strawberry_django
from netbox.graphql.types import NetBoxObjectType

from .models import MACVendor


@strawberry_django.type(MACVendor, fields="__all__")
class MACVendorType(NetBoxObjectType):
    pass


@strawberry.type(name="Query")
class MacadressQuery:
    mac_vendor: MACVendorType = strawberry_django.field()
    mac_vendor_list: list[MACVendorType] = strawberry_django.field()


schema = [MacadressQuery]
