import pytest

# OAuth routes are implemented and tested within FastMCP's OAuthProxy. This
# package relies on that implementation, so we skip legacy route tests here.
pytestmark = pytest.mark.skip("OAuth routes exercised in FastMCP upstream")
