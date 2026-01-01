import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import demo_entrypoint, health  # noqa: E402


def test_health_returns_status_key():
    import asyncio

    data = asyncio.run(health())
    assert "status" in data


def test_demo_endpoints_return_html():
    import asyncio

    response = asyncio.run(demo_entrypoint())
    assert response.status_code == 200
    content_type = response.headers.get("content-type", "")
    assert content_type.startswith("text/html")
