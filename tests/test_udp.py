import unittest
from osc_cr_converter.udp_driver.common import *


class TestUDP(unittest.TestCase):
    """Tests for using the UDP (import)."""

    def test_osi(self):
        OSIReceiver()
