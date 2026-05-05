from __future__ import annotations

import os


# Keep the regular test suite deterministic even when a developer has a real
# watsonx.ai .env file on the machine. The dedicated watsonx smoke test covers
# live IBM model calls.
os.environ["MODEL_PROVIDER"] = "mock"
