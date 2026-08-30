from dataclasses import dataclass
from datetime import date

from radar.services.locations import PROVINCE_NAMES, SPECIAL_LOCATIONS, province_locations


PREVIEW_COMPANY_TYPE_CHOICES = (
    ("state_owned", "央国企"),
    ("private", "民企"),
    ("public_institution", "事业单位"),
    ("bank", "银行"),
    ("foreign", "外资"),
    ("joint_venture", "中外合资"),
    ("social_organization", "社会机构"),
)

PREVIEW_RECRUITMENT_TYPE_CHOICES = (
    ("spring", "春招"),
    ("spring_supplement", "春招补录"),
    ("autumn", "秋招"),
    ("autumn_supplement", "秋招补录"),
    ("autumn_early", "秋招提前批"),
    ("campus_recruitment", "校园招聘"),
    ("internship", "实习"),
    ("special_program", "专项计划"),
    ("other", "其他"),
)

AUDIENCE_CHOICES = tuple((value, value) for value in (
    "2024届", "2025届", "2026届", "2027届", "2028届",
    "应届毕业生（届次未说明）", "应届毕业生/实习生（届次未说明）", "实习生",
))

PROVINCE_CHOICES = PROVINCE_NAMES
MAX_SELECTED_PROVINCES = 5


@dataclass(frozen=True)
class RecruitmentPositionVM:
    id: int | str
    title: str
    locations: tuple[str, ...]
    details: str
    application_url: str | None
    uses_batch_page: bool
    effective_updated_on: date
    is_current: bool = True
    kind: str = "position"


@dataclass(frozen=True)
class RecruitmentBatchVM:
    id: int | str
    company: str
    company_type: str
    industry: str
    title: str
    recruitment_type: str
    target_audience: str
    deadline: date | None
    status: str
    official_page_url: str
    progress_value: str
    progress_label: str
    positions: tuple[RecruitmentPositionVM, ...]
    announcement_url: str | None = None
    announcement_label: str = "公告"
    announcement_instructions: str = ""
    batch_application_urls: tuple[str, ...] = ()
    batch_application_notes: tuple[str, ...] = ()

    @property
    def preview_positions(self):
        return self.positions[:5]

    @property
    def remaining_count(self) -> int:
        return max(0, len(self.positions) - 5)

    @property
    def remaining_positions(self):
        return self.positions[5:]

    @property
    def hover_positions(self):
        return self.positions[:30]

    @property
    def hover_remaining_count(self) -> int:
        return max(0, len(self.positions) - 30)

    @property
    def position_summary(self) -> str:
        text = "、".join(position.title for position in self.preview_positions)
        if self.positions and all(position.kind == "direction" for position in self.positions):
            text = f"岗位方向：{text}"
        if self.remaining_count:
            text += f"，另有 {self.remaining_count} 个岗位"
        return text

    @property
    def location_summary(self) -> str:
        raw_locations = tuple(dict.fromkeys(
            location for position in self.positions for location in position.locations
        ))
        locations = province_locations(raw_locations)
        preview = "、".join(locations[:6])
        if len(locations) > 6:
            recognized = set(PROVINCE_NAMES) | SPECIAL_LOCATIONS | {"海外"}
            unit = "个省级地区" if set(locations) <= recognized else "个地点"
            preview += f"，另有 {len(locations) - 6} {unit}"
        return preview

    @property
    def primary_application_url(self) -> str | None:
        direct = next(
            (position.application_url for position in self.positions if not position.uses_batch_page),
            None,
        )
        return direct or next(iter(self.batch_application_urls), None)

    @property
    def primary_application_uses_batch_page(self) -> bool:
        return self.primary_application_url is None

    @property
    def primary_application_note(self) -> str:
        return "" if self.primary_application_url else next(iter(self.batch_application_notes), "")

    @property
    def company_badge_class(self) -> str:
        if self.company_type == "民企":
            return "private"
        if self.company_type in {"央国企", "央企/国企", "央企", "国企"}:
            return "state"
        if self.company_type in {"外资", "中外合资"}:
            return "foreign"
        if self.company_type == "银行":
            return "bank"
        return "other"

    @property
    def effective_updated_on(self) -> date:
        return max(position.effective_updated_on for position in self.positions)


@dataclass(frozen=True)
class DashboardSummaryVM:
    active_positions: int
    changed_in_3_days: int
    deadline_in_7_days: int
    applications_in_progress: int
    today_updated_companies: int = 0
    updated_companies_in_3_days: int = 0
    deadline_companies_in_1_day: int = 0
    deadline_companies_in_3_days: int = 0
