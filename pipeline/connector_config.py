"""
AROUND THE MAIN v6 - Connector Configuration

Defines which source connector types are enabled in production.

This configuration controls ingestion only.

Source reputation, verification, intelligence, ranking and
editorial decisions remain outside this module.
"""

from pipeline.source_connectors import (
    CONNECTOR_API,
    CONNECTOR_LICENSED,
    CONNECTOR_RSS,
)


CONNECTOR_REGISTRY = {
    "reuters": {
        "type": CONNECTOR_LICENSED,
        "enabled": False,
    },

    "associated_press": {
        "type": CONNECTOR_LICENSED,
        "enabled": False,
    },

    "bbc": {
        "type": CONNECTOR_RSS,
        "enabled": False,
    },

    "afp": {
        "type": CONNECTOR_LICENSED,
        "enabled": False,
    },

    "un": {
        "type": CONNECTOR_RSS,
        "enabled": True,
    },

    "imf": {
        "type": CONNECTOR_API,
        "enabled": False,
    },

    "world_bank": {
        "type": CONNECTOR_API,
        "enabled": False,
    },

    "who": {
        "type": CONNECTOR_API,
        "enabled": False,
    },

    "iea": {
        "type": CONNECTOR_API,
        "enabled": False,
    },

    "opec": {
        "type": CONNECTOR_API,
        "enabled": False,
    },
}


def get_connector_registry():
    """
    Return a defensive copy of the production connector registry.
    """

    return {
        source: dict(config)
        for source, config in CONNECTOR_REGISTRY.items()
    }


def configured_connectors():
    """
    Return connector configurations currently enabled.
    """

    return {
        source: dict(config)
        for source, config in CONNECTOR_REGISTRY.items()
        if config.get("enabled") is True
    }
