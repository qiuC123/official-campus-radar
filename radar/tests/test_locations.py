from django.test import SimpleTestCase

from radar.services.locations import (
    is_target_location,
    matches_selected_cities,
    normalized_target_locations,
)


class LocationPolicyTests(SimpleTestCase):
    def test_recognizes_explicit_target_city_variants(self) -> None:
        self.assertTrue(is_target_location("北京市 / 深圳市"))
        self.assertEqual(normalized_target_locations("北京、深圳"), ["北京", "深圳"])

    def test_retains_any_named_location_but_empty_remains_unknown(self) -> None:
        self.assertTrue(is_target_location("杭州"))
        self.assertEqual(normalized_target_locations("杭州市、火星基地"), ["杭州", "火星基地"])
        self.assertFalse(is_target_location(""))

    def test_splits_beisen_province_city_locations_and_accepts_arrays(self) -> None:
        self.assertEqual(
            normalized_target_locations(
                ["广东省·东莞市/深圳市", "浙江省·杭州市"]
            ),
            ["广东", "东莞", "深圳", "浙江", "杭州"],
        )

    def test_special_location_filters_are_exact_unless_a_city_is_selected(self) -> None:
        self.assertTrue(matches_selected_cities(["远程"], ["远程"]))
        self.assertFalse(matches_selected_cities(["全国"], ["远程"]))
        self.assertFalse(matches_selected_cities(["远程"], ["全国"]))
        self.assertTrue(matches_selected_cities(["远程"], ["北京"]))
        self.assertTrue(matches_selected_cities(["全国"], ["北京"]))
