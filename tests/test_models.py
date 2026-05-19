"""Tests for the models for the resumes app."""

from __future__ import annotations

from datetime import date

import pytest

from resumes.models import Education, Experience, Profile


@pytest.mark.django_db
def test_profile_contact_complete():
    complete = Profile(
        full_name="Ada",
        email="ada@example.com",
        phone="555",
        location="London",
    )
    incomplete = Profile(full_name="Ada")

    assert complete.contact_complete()
    assert not incomplete.contact_complete()


@pytest.mark.django_db
def test_experience_date_range_variants():
    current = Experience(
        company="Acme",
        title="Engineer",
        start_date=date(2022, 1, 1),
        current_role=True,
    )
    bounded = Experience(
        company="Acme",
        title="Engineer",
        start_date=date(2020, 1, 1),
        end_date=date(2021, 12, 1),
        current_role=False,
    )
    empty = Experience()

    assert "Present" in current.date_range()
    assert "Jan 2020" in bounded.date_range()
    assert bounded.date_range().endswith("Dec 2021")
    assert empty.date_range() == ""


@pytest.mark.django_db
def test_education_date_range():
    item = Education(start_date=date(2018, 9, 1), end_date=date(2022, 5, 1))

    assert item.date_range() == "Sep 2018 - May 2022"


@pytest.mark.django_db
def test_education_date_range_partial_dates():
    start_only = Education(start_date=date(2020, 1, 1))
    end_only = Education(end_date=date(2022, 6, 1))

    assert start_only.date_range() == "Jan 2020"
    assert end_only.date_range() == "Jun 2022"


@pytest.mark.django_db
def test_experience_date_range_start_only():
    experience = Experience(start_date=date(2021, 3, 1), current_role=False)

    assert experience.date_range() == "Mar 2021"
