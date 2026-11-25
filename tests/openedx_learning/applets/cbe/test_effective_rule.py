"""Tests for get_effective_rule(): the rule a criterion is graded against, and where it comes from."""
import pytest

from openedx_learning.api import EffectiveRule, get_effective_rule
from openedx_learning.models import CompetencyCriteriaGroup, CompetencyCriterion, CompetencyRuleProfile, RuleType
from openedx_tagging.models import ObjectTag

pytestmark = pytest.mark.django_db

_OVERRIDE_PAYLOAD = {"op": "gte", "value": 0.9, "scale": "percent"}


def test_profile_sourced_rule_is_the_profiles_rule(
    group: CompetencyCriteriaGroup, object_tag: ObjectTag, default_rule_profile: CompetencyRuleProfile
) -> None:
    criterion = CompetencyCriterion.objects.create(
        group=group, object_tag=object_tag, rule_profile=default_rule_profile
    )

    assert get_effective_rule(criterion) == EffectiveRule(
        rule_type=default_rule_profile.rule_type,
        rule_payload=default_rule_profile.rule_payload,
        source="profile",
        rule_profile_id=default_rule_profile.id,
    )


def test_override_sourced_rule_is_the_criterions_own_rule(
    group: CompetencyCriteriaGroup, object_tag: ObjectTag
) -> None:
    criterion = CompetencyCriterion.objects.create(
        group=group, object_tag=object_tag, rule_type_override=RuleType.GRADE, rule_payload_override=_OVERRIDE_PAYLOAD
    )

    assert get_effective_rule(criterion) == EffectiveRule(
        rule_type=RuleType.GRADE,
        rule_payload=_OVERRIDE_PAYLOAD,
        source="override",
        rule_profile_id=None,
    )


def test_profile_sourced_rule_follows_a_change_to_the_profile(
    group: CompetencyCriteriaGroup, object_tag: ObjectTag, default_rule_profile: CompetencyRuleProfile
) -> None:
    """Changing the profile's rule changes the criterion's effective rule, with no write to the criterion."""
    criterion = CompetencyCriterion.objects.create(
        group=group, object_tag=object_tag, rule_profile=default_rule_profile
    )
    default_rule_profile.rule_payload = {"op": "gte", "value": 0.7, "scale": "percent"}
    default_rule_profile.save()

    reloaded = CompetencyCriterion.objects.select_related("rule_profile").get(pk=criterion.pk)

    assert get_effective_rule(reloaded).rule_payload == {"op": "gte", "value": 0.7, "scale": "percent"}


def test_needs_no_query_when_the_profile_is_already_loaded(
    group: CompetencyCriteriaGroup,
    object_tag: ObjectTag,
    default_rule_profile: CompetencyRuleProfile,
    django_assert_num_queries,
) -> None:
    criterion = CompetencyCriterion.objects.create(
        group=group, object_tag=object_tag, rule_profile=default_rule_profile
    )
    loaded = CompetencyCriterion.objects.select_related("rule_profile").get(pk=criterion.pk)

    with django_assert_num_queries(0):
        get_effective_rule(loaded)
