from dataclasses import dataclass
from datetime import date


OPTIONAL_COLUMN_CHOICES = (
    ("company-type", "公司类型"),
    ("industry", "行业"),
    ("recruitment-type", "招聘类型"),
    ("target-audience", "招聘对象"),
    ("updated", "更新时间"),
    ("deadline", "截止时间"),
    ("official-page", "官方页"),
)

FILTER_FIELD_SPECS = (
    ("company", "公司关键词", "text", "例如：腾讯"),
    ("company_type", "公司类型", "select", ""),
    ("industry", "行业", "text", ""),
    ("recruitment_type", "招聘类型", "select", ""),
    ("target_audience", "招聘对象", "text", ""),
    ("position", "岗位关键词", "text", ""),
    ("deadline_before", "截止日期", "date", ""),
)

MULTI_FILTER_LABELS = (("city", "城市（可多选）"), ("progress", "进度（可多选）"))


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

    @property
    def preview_positions(self):
        return self.positions[:3]

    @property
    def remaining_count(self) -> int:
        return max(0, len(self.positions) - 3)

    @property
    def remaining_positions(self):
        return self.positions[3:]

    @property
    def effective_updated_on(self) -> date:
        return max(position.effective_updated_on for position in self.positions)


@dataclass(frozen=True)
class DashboardSummaryVM:
    active_positions: int
    changed_in_3_days: int
    deadline_in_7_days: int
    applications_in_progress: int
