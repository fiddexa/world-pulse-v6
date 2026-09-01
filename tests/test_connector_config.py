from pipeline.connector_config import (
    CONNECTOR_REGISTRY,
    configured_connectors,
    get_connector_registry,
)


def test_connector_registry_contains_core_sources():
    expected = {
        "reuters",
        "associated_press",
        "bbc",
        "afp",
        "un",
        "imf",
        "world_bank",
        "who",
        "iea",
        "opec",
    }

    assert expected.issubset(
        CONNECTOR_REGISTRY.keys()
    )


def test_un_is_the_only_enabled_production_connector():
    enabled = configured_connectors()

    assert enabled == {
        "un": {
            "type": "rss",
            "enabled": True,
        }
    }


def test_licensed_sources_are_disabled():
    assert CONNECTOR_REGISTRY["reuters"]["enabled"] is False
    assert CONNECTOR_REGISTRY["associated_press"]["enabled"] is False
    assert CONNECTOR_REGISTRY["afp"]["enabled"] is False


def test_registry_returns_copy():
    registry = get_connector_registry()

    registry["un"]["enabled"] = False

    assert CONNECTOR_REGISTRY["un"]["enabled"] is True
