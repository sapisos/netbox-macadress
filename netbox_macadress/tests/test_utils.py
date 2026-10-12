from django.test import SimpleTestCase

from ..utils import candidate_keys, format_prefix, key_for_result, local_status, lookup_key, normalize


class NormalizeTestCase(SimpleTestCase):
    def test_formats(self):
        for value in ("00:03:93:ab:12:34", "00-03-93-AB-12-34", "0003.93ab.1234", "000393AB1234"):
            self.assertEqual(normalize(value), "000393AB1234")

    def test_invalid(self):
        for value in (None, "", "00:03:93", "00:03:93:ab:12:34:56"):
            self.assertIsNone(normalize(value))


class ClassifyTestCase(SimpleTestCase):
    def test_local_status(self):
        self.assertIsNone(local_status("000393AB1234"))
        self.assertEqual(local_status("01005E000001"), "multicast")
        self.assertEqual(local_status("020000000001"), "locally_administered")
        self.assertEqual(local_status("DA1B2C3D4E5F"), "locally_administered")


class KeyTestCase(SimpleTestCase):
    def test_candidate_keys_most_specific_first(self):
        self.assertEqual(candidate_keys("70B3D5F00001"), ["70B3D5F00", "70B3D5F", "70B3D5"])

    def test_lookup_key(self):
        self.assertEqual(lookup_key("000393AB1234"), "000393")
        # 70:B3:D5 is subdivided into MA-S blocks, so the OUI alone is not enough.
        self.assertEqual(lookup_key("70B3D5F00001"), "70B3D5F00")

    def test_key_for_result(self):
        self.assertEqual(key_for_result("000393AB1234", None, "Apple, Inc."), "000393")
        self.assertEqual(key_for_result("000393AB1234", 24, "Apple, Inc."), "000393")
        self.assertEqual(key_for_result("70B3D5F00001", 36, "Aplex Technology Inc."), "70B3D5F00")
        self.assertEqual(key_for_result("70B3D5F00001", 28, "Someone"), "70B3D5F")
        # The MA-L fallback inside a subdivided OUI only covers the 36-bit block.
        self.assertEqual(key_for_result("70B3D5000001", 24, "IEEE Registration Authority"), "70B3D5000")
        # An OUI subdivided after this release is recognized by its assignee name.
        self.assertEqual(key_for_result("ABCDEF000001", None, "IEEE Registration Authority"), "ABCDEF000")

    def test_format_prefix(self):
        self.assertEqual(format_prefix("000393"), "00:03:93/24")
        self.assertEqual(format_prefix("70B3D5F"), "70:B3:D5:F/28")
        self.assertEqual(format_prefix("70B3D5F00"), "70:B3:D5:F0:0/36")
