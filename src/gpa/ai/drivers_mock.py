"""The mock driver (roadmap B-036).

Schema-valid canned output, produced by *reading the schema*:
``complete_json`` synthesises the smallest instance the schema
allows (required object properties only, arrays empty, strings
empty), so the result always parses and always validates — and
for the extraction schemas that means "no items", i.e. the
pipeline runs end to end and drafts nothing. That is exactly the
point of a mock: the machinery is exercised, the model is not
pretended at.

The whole test suite and the whole demo run on this driver with
no network and no API key (B-036's acceptance). Usage is estimated
from character counts; cost is zero — a mock spends nothing, and
the ledger says so.
"""

from typing import Any

from gpa.ai.client import ModelResult, estimate_tokens


def synthesize(schema: dict, root: dict | None = None) -> Any:
    """The smallest schema-valid instance of ``schema``.

    Handles the subset of JSON Schema our prompt library uses:
    ``$ref`` into ``$defs``, objects (required properties only),
    arrays (empty), strings/numbers/booleans (neutral values),
    and ``type`` lists (first non-null type wins).
    """
    root = root if root is not None else schema
    if "$ref" in schema:
        # "#/$defs/field" — the only ref shape the library uses.
        name = schema["$ref"].rsplit("/", 1)[-1]
        return synthesize(root.get("$defs", {})[name], root)
    schema_type = schema.get("type")
    if isinstance(schema_type, list):
        schema_type = next((t for t in schema_type if t != "null"), "string")
    if schema_type == "object" or "properties" in schema:
        properties = schema.get("properties", {})
        return {
            name: synthesize(properties[name], root)
            for name in schema.get("required", [])
            if name in properties
        }
    if schema_type == "array":
        return []
    if schema_type == "integer":
        return 0
    if schema_type == "number":
        return 0.0
    if schema_type == "boolean":
        return False
    return ""


class MockDriver:
    """A MetaModelClient that answers from the schema, not a model."""

    driver_name = "mock"

    def __init__(self, *, model_spark: str = "muse-spark", model_wonder: str = "muse-wonder"):
        self._models = {"spark": model_spark, "wonder": model_wonder}

    def _result(self, *, prompt: str, tier: str, text: str, data: Any = None) -> ModelResult:
        return ModelResult(
            text=text,
            data=data,
            model_id=f"{self._models.get(tier, self._models['spark'])} (mock)",
            tier=tier,
            input_tokens=estimate_tokens(prompt),
            output_tokens=estimate_tokens(text),
            cost_micros=0,
        )

    def complete_text(self, *, prompt: str, tier: str = "spark") -> ModelResult:
        return self._result(prompt=prompt, tier=tier, text="(mock response)")

    def complete_json(self, *, prompt: str, schema: dict, tier: str = "spark") -> ModelResult:
        data = synthesize(schema)
        import json

        return self._result(prompt=prompt, tier=tier, text=json.dumps(data), data=data)

    def read_image(
        self, *, prompt: str, image_bytes: bytes, schema: dict | None = None,
        tier: str = "wonder",
    ) -> ModelResult:
        data = synthesize(schema) if schema else None
        return self._result(prompt=prompt, tier=tier, text="", data=data)

    def transcribe(self, *, audio_bytes: bytes, mime: str = "audio/wav", tier: str = "spark") -> ModelResult:
        # Honest canned words: the mock does not listen, and its
        # transcript says so — nobody should mistake it for speech.
        return self._result(
            prompt="", tier=tier,
            text="Mock transcript: the mock driver does not listen to audio.",
        )
