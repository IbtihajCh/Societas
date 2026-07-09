"""Tests for shared/types/enums.py — verify enum value counts and access."""

from shared.types.enums import (
    ActionType,
    CrimeType,
    Culture,
    EducationLevel,
    EmotionType,
    EmploymentStatus,
    Gender,
    JobType,
    NeedType,
    PolicyCategory,
    WealthClass,
)


class TestActionType:
    def test_has_15_values(self) -> None:
        assert len(list(ActionType)) == 15

    def test_work_exists(self) -> None:
        assert ActionType.WORK == "work"

    def test_buy_food_exists(self) -> None:
        assert ActionType.BUY_FOOD == "buy_food"

    def test_idle_exists(self) -> None:
        assert ActionType.IDLE == "idle"

    def test_steal_exists(self) -> None:
        assert ActionType.STEAL == "steal"

    def test_protest_exists(self) -> None:
        assert ActionType.PROTEST == "protest"


class TestNeedType:
    def test_has_13_values(self) -> None:
        assert len(list(NeedType)) == 13

    def test_food_exists(self) -> None:
        assert NeedType.FOOD == "food"

    def test_water_exists(self) -> None:
        assert NeedType.WATER == "water"

    def test_sleep_exists(self) -> None:
        assert NeedType.SLEEP == "sleep"

    def test_safety_exists(self) -> None:
        assert NeedType.SAFETY == "safety"

    def test_social_connection_exists(self) -> None:
        assert NeedType.SOCIAL_CONNECTION == "social_connection"

    def test_self_esteem_exists(self) -> None:
        assert NeedType.SELF_ESTEEM == "self_esteem"

    def test_reputation_exists(self) -> None:
        assert NeedType.REPUTATION == "reputation"


class TestEmotionType:
    def test_has_5_values(self) -> None:
        assert len(list(EmotionType)) == 5

    def test_happy_exists(self) -> None:
        assert EmotionType.HAPPY == "happy"

    def test_normal_exists(self) -> None:
        assert EmotionType.NORMAL == "normal"

    def test_sad_exists(self) -> None:
        assert EmotionType.SAD == "sad"

    def test_angry_exists(self) -> None:
        assert EmotionType.ANGRY == "angry"

    def test_despair_exists(self) -> None:
        assert EmotionType.DESPAIR == "despair"


class TestWealthClass:
    def test_has_3_values(self) -> None:
        assert len(list(WealthClass)) == 3

    def test_poor_exists(self) -> None:
        assert WealthClass.POOR == "poor"

    def test_middle_exists(self) -> None:
        assert WealthClass.MIDDLE == "middle"

    def test_rich_exists(self) -> None:
        assert WealthClass.RICH == "rich"


class TestNewEnums:
    def test_gender_has_2_values(self) -> None:
        assert len(list(Gender)) == 2

    def test_culture_has_3_values(self) -> None:
        assert len(list(Culture)) == 3

    def test_education_level_has_4_values(self) -> None:
        assert len(list(EducationLevel)) == 4

    def test_education_level_values(self) -> None:
        assert EducationLevel.NONE == 0
        assert EducationLevel.PRIMARY == 1
        assert EducationLevel.SECONDARY == 2
        assert EducationLevel.HIGHER == 3

    def test_job_type_has_12_values(self) -> None:
        assert len(list(JobType)) == 12

    def test_job_type_engineer_exists(self) -> None:
        assert JobType.ENGINEER == "engineer"

    def test_job_type_unemployed_exists(self) -> None:
        assert JobType.UNEMPLOYED == "unemployed"


class TestPreservedEnums:
    def test_policy_category_has_8_values(self) -> None:
        assert len(list(PolicyCategory)) == 8

    def test_crime_type_has_7_values(self) -> None:
        assert len(list(CrimeType)) == 7

    def test_employment_status_has_5_values(self) -> None:
        assert len(list(EmploymentStatus)) == 5
