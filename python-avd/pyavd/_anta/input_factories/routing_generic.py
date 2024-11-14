# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
from __future__ import annotations

from typing import TYPE_CHECKING

from pyavd._anta.utils import LogMessage

if TYPE_CHECKING:
    from anta.tests.routing.generic import VerifyRoutingTableEntry

    from pyavd._anta.utils import ConfigManager, TestLoggerAdapter


class VerifyRoutingTableEntryInputFactory:
    """Input factory class for the VerifyRoutingTableEntry test.

    This factory creates test inputs specifically for VTEPs while excluding WAN VTEPs.

    It collects routes that should be present in the routing table for:
      - Loopback0 IPs of all fabric nodes
      - VXLAN source interface IPs of other VTEPs

    The factory ensures:
      - Tests only run on VTEP devices (presence of `vxlan_interface`), excluding WAN VTEPs (DPS interface)
      - Duplicate IP addresses are filtered out (e.g., in MLAG VTEP scenarios)
      - Only routes for available peers (`is_deployed: true`) are included
      - Route collection is skipped if no routes are found
    """

    @classmethod
    def create(cls, test: type[VerifyRoutingTableEntry], manager: ConfigManager, logger: TestLoggerAdapter) -> VerifyRoutingTableEntry.Input | None:
        """Create Input for the VerifyRoutingTableEntry test."""
        # Skip the test if the device is not a VTEP or is a WAN VTEP
        if not manager.is_vtep() or manager.is_wan_vtep():
            logger.debug(LogMessage.NOT_VTEP)
            return None

        # Using a set to avoid duplicate tests for the same IP address (e.g. MLAG VTEPs)
        processed_ips = set()

        # Here we use the combined_mapping (Loopback0 IP + VXLAN source interface IP) to get all routes to check
        for peer, ips in manager.fabric_data.combined_mapping.items():
            if not manager.is_peer_available(peer):
                entity = ", ".join([str(ip) for ip in ips])
                logger.debug(LogMessage.UNAVAILABLE_PEER, entity=entity, peer=peer)
                continue

            processed_ips.update(ips)

        return test.Input(routes=list(processed_ips), collect="all") if processed_ips else None