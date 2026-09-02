"""
AROUND THE MAIN v6 - Edition Slots

Defines the fixed daily AROUND THE MAIN publication slots.

This module does not schedule or execute editions.
It only provides the canonical production slot configuration.
"""

from pipeline.edition_id import DEFAULT_TIMEZONE


EDITION_SLOTS = (
    "07:00",
    "13:00",
    "20:00",
)

EDITION_TIMEZONE = DEFAULT_TIMEZONE


def get_edition_slots():
    """
    Return the canonical daily edition slots.
    """

    return EDITION_SLOTS


def is_valid_edition_time(edition_time):
    """
    Return True when the supplied time is a configured edition slot.
    """

    return edition_time in EDITION_SLOTS
