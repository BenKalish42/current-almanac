"""
Pydantic schemas matching the Pinia appStore serializeForApi payload.
Contract for frontend-backend data bridge.
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field


# --- Moment ---
class LocalWeather(BaseModel):
    temp_f: float | None = None
    precip: float | None = None
    wind: float | None = None
    notes: str | None = None


class MomentInput(BaseModel):
    timestamp_iso: str
    timezone: str
    location: str
    local_weather: LocalWeather


# --- Calendar ---
class JieQi(BaseModel):
    current: str | None = None
    days_to_next: int | None = None


class LunarDate(BaseModel):
    lunar_month: int | None = None
    lunar_day: int | None = None
    is_leap_month: bool | None = None


class GanzhiMoment(BaseModel):
    year: str | None = None
    month: str | None = None
    day: str | None = None
    hour: str | None = None


class CalendarInput(BaseModel):
    jieqi: JieQi
    lunar_date: LunarDate
    ganzhi_moment: GanzhiMoment


# --- User ---
class BaziNatal(BaseModel):
    year: str | None = None
    month: str | None = None
    day: str | None = None
    hour: str | None = None
    day_master: str | None = None
    dayun_current: str | None = None


class NineStar(BaseModel):
    year_star: str | None = None
    month_star: str | None = None
    day_star: str | None = None


class UserState(BaseModel):
    capacity_0_10: float | None = None
    load_0_10: float | None = None
    sleep_quality_0_10: float | None = None
    cognitive_noise_0_10: float | None = None
    social_load_0_10: float | None = None
    emotional_tone: str | None = None


class UserIntent(BaseModel):
    domain: str
    goal_constraint: str


class UserInput(BaseModel):
    bazi_natal: BaziNatal
    nine_star: NineStar
    state: UserState
    intent: UserIntent


# --- Optional systems ---
class Tongshu(BaseModel):
    day_quality: str | None = None
    avoid_tags: list[str] = Field(default_factory=list)
    do_tags: list[str] = Field(default_factory=list)


class QimenChartData(BaseModel):
    """Flexible schema for Qimen chart (palaces/grid structure varies)."""

    method: str
    scope: str
    solar: dict[str, Any]
    lunar: dict[str, Any]
    zhiRun: dict[str, Any]
    palaces: dict[str, Any] = Field(default_factory=dict)
    grid: list[list[int]] = Field(default_factory=list)


class QimenCharts(BaseModel):
    hour: QimenChartData | None = None
    day: QimenChartData | None = None


class Qimen(BaseModel):
    chart: QimenCharts
    primary: str = "hour"
    notes: str = ""


class OptionalSystems(BaseModel):
    tongshu: Tongshu
    qimen: Qimen


# --- Output contract ---
class OutputStyle(BaseModel):
    tone: str = "neutral_descriptive"
    no_prediction: bool = True
    no_moralizing: bool = True
    no_destiny: bool = True
    max_length_words: int = 260


class OutputContract(BaseModel):
    format: Literal["json"] = "json"
    fields: list[str]
    style: OutputStyle


# --- Full request ---
class InterpretationInputs(BaseModel):
    moment: MomentInput
    calendar: CalendarInput
    user: UserInput
    optional_systems: OptionalSystems


class InterpretationRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    schema_version: Literal["current_v1"] = "current_v1"
    inputs: InterpretationInputs
    output_contract: OutputContract
    # Hidden AI context: full Lunar/EightChar firehose + Zi Wei Dou Shu
    advanced_astro: dict[str, Any] | None = None
    zwds: dict[str, Any] | None = None


# --- Response schemas ---
class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    version: str = "current_v1"


class InterpretationResponse(BaseModel):
    """Placeholder response until Phase 4 AI integration."""

    current_summary: str | None = None
    shi: str | None = None
    shun: str | None = None
    ji: str | None = None
    load_capacity: str | None = None
    misalignment_signals: str | None = None
    recommended_modes: str | None = None
    avoid: str | None = None
    self_check: str | None = None


# --- Herb & Formula (Phase 3: GraphRAG seed data) ---


class HerbProperties(BaseModel):
    """Nested properties: temperature, flavor, meridians."""

    temperature: str
    flavor: list[str] = Field(default_factory=list)
    meridians: list[str] = Field(default_factory=list)


class Herb(BaseModel):
    """Herb schema matching seed_herbs.json."""

    id: str
    pinyin_name: str
    common_name: str
    safety_tier: int
    properties: HerbProperties
    actions: list[str] = Field(default_factory=list)
    contraindications: str = ""


class FormulaArchitecture(BaseModel):
    """King-Minister-Assistant-Envoy role with herb link and dosage."""

    role: str
    herb_id: str
    pinyin_name: str
    dosage_percentage: float
    purpose: str


class Formula(BaseModel):
    """Formula schema matching seed_formulas.json with nested architecture."""

    id: str
    pinyin_name: str
    common_name: str
    primary_pattern: str
    actions: list[str] = Field(default_factory=list)
    architecture: list[FormulaArchitecture] = Field(default_factory=list)
    safety_note: str = ""


# --- Phase 5: Cauldron API request/response ---


class FormulaRequest(BaseModel):
    """Request for recommended formula (astro + user state)."""

    astro: dict[str, Any] = Field(default_factory=dict)
    user: dict[str, Any] = Field(default_factory=dict)


class OverrideCheckRequest(BaseModel):
    """Request to check herb addition safety."""

    formula_id: str
    herb_id: str


class OverrideCheckResponse(BaseModel):
    """Response from override safety check."""

    allowed: bool
    message: str


class MergeFormulasRequest(BaseModel):
    """Request to merge two formulas."""

    formula_a_id: str
    formula_b_id: str
    primary_formula_id: str


class MergeFormulasResponse(BaseModel):
    """Response with merged architecture."""

    architecture: list[dict[str, Any]]


# --- Nei Dan (Internal Alchemy) - Dual Cultivation ---


class NeiDanPractice(BaseModel):
    """Internal alchemy practice matching seed_neidan.json."""

    id: str
    name: str
    type: str
    target_pattern: list[str] = Field(default_factory=list)
    instructions: list[str] = Field(default_factory=list)
    safety_note: str = ""


class Prescription(BaseModel):
    """Dual Cultivation: Wei Dan (herbal) + Nei Dan (internal practice)."""

    wei_dan: list[dict[str, Any]] = Field(default_factory=list)  # herbal formula architecture
    nei_dan: NeiDanPractice | None = None  # matched internal practice
    # Formula metadata (for display)
    formula_id: str = ""
    pinyin_name: str = ""
    common_name: str = ""
    primary_pattern: str = ""
    actions: list[str] = Field(default_factory=list)
    safety_note: str = ""

    @computed_field
    @property
    def architecture(self) -> list[dict[str, Any]]:
        """Alias for wei_dan (backward compatibility with frontend)."""
        return self.wei_dan

    @computed_field
    @property
    def id(self) -> str:
        """Alias for formula_id (backward compatibility)."""
        return self.formula_id


# --- Phase 8: Practitioner Pantry (Inventory Management) ---


class PantryItem(BaseModel):
    """Herb inventory item for user pantry."""

    herb_id: str
    in_stock: bool


class PantryToggleRequest(BaseModel):
    """Request to add/remove an herb from inventory."""

    herb_id: str
    user_id: str = "default"
