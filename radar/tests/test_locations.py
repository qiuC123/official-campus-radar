from django.test import SimpleTestCase

from radar.services.locations import is_target_location, normalized_target_locations


class LocationPolicyTests(SimpleTestCase):
    def test_recognizes_explicit_target_city_variants(self) -> None:
        self.assertTrue(is_target_location("北京市 / 深圳市"))
        self.assertEqual(normalized_target_locations("北京、深圳"), ["北京", "深圳"])

    def test_rejects_unknown_or_empty_location(self) -> None:
        self.assertFalse(is_target_location("杭州"))
        self.assertFalse(is_target_location(""))
