"""Reserve conservative call ceilings and record provider-reported usage."""

import os
import json
import uuid
from contextvars import ContextVar
from decimal import Decimal, InvalidOperation
from langchain_core.callbacks import BaseCallbackHandler

active_usage = ContextVar("active_usage", default=None)


class UsageCallback(BaseCallbackHandler):
    raise_error = True

    def __init__(self, store, job):
        self.store = store
        self.job = job
        self.reservations = {}
        self.billing_reservations = {}

    def on_chat_model_start(self, serialized, messages, *, run_id, **kwargs):
        try:
            input_rate = Decimal(os.environ.get("MODEL_INPUT_USD_PER_MILLION") or "0")
            output_rate = Decimal(os.environ.get("MODEL_OUTPUT_USD_PER_MILLION") or "0")
        except InvalidOperation as exc:
            raise RuntimeError("Model prices must be valid decimal numbers") from exc
        model = os.environ.get("PRICED_MODEL", "")
        from config import OPENAI_MODEL

        if model != OPENAI_MODEL or not input_rate.is_finite() or not output_rate.is_finite():
            raise RuntimeError("Configure pricing for the exact active model before paid calls")
        if input_rate <= 0 or output_rate <= 0:
            raise RuntimeError("Positive model input/output pricing is required")
        params = kwargs.get("invocation_params", {})
        max_output = params.get("max_tokens") or params.get("max_completion_tokens")
        if type(max_output) is not int or max_output <= 0:
            raise RuntimeError("Explicit output token ceiling required")
        # UTF-8 byte count overbounds text tokens; add envelope overhead.
        inputs = sum(len(str(msg.content).encode()) + 64 for batch in messages for msg in batch)
        inputs += 1024 + len(json.dumps(params, default=str).encode())
        reserved = inputs + max_output
        cost = float((inputs * input_rate + max_output * output_rate) / 1_000_000)
        from services.billing_service import billing_service

        reference = None
        if billing_service.enabled():
            reference = f"{self.job['id']}:{uuid.uuid4().hex}"
            billing_service.reserve(self.job["owner"], reference, cost)
        try:
            self.store.reserve(self.job, reserved, cost)
        except Exception:
            if reference:
                billing_service.settle(reference, 0)
            raise
        if reference:
            self.billing_reservations[run_id] = reference
        self.reservations[run_id] = (reserved, cost, input_rate, output_rate)

    def settle_billing(self, run_id, cost):
        reference = self.billing_reservations.pop(run_id, None)
        if reference:
            from services.billing_service import billing_service

            billing_service.settle(reference, cost)

    def on_llm_end(self, response, *, run_id, **kwargs):
        reserved, ceiling, input_rate, output_rate = self.reservations.pop(run_id)
        usage = (response.llm_output or {}).get("token_usage")
        if not usage:
            generation = response.generations[0][0]
            usage = getattr(getattr(generation, "message", None), "usage_metadata", None)
        if not usage:
            self.settle_billing(run_id, ceiling)
            raise RuntimeError("Provider usage missing; reservation retained and job stopped")
        inputs = usage.get("prompt_tokens", usage.get("input_tokens"))
        outputs = usage.get("completion_tokens", usage.get("output_tokens"))
        if not all(type(value) is int and value >= 0 for value in (inputs, outputs)):
            self.settle_billing(run_id, ceiling)
            raise RuntimeError("Invalid provider token usage; job stopped")
        cost = float((inputs * input_rate + outputs * output_rate) / 1_000_000)
        self.settle_billing(run_id, cost)
        self.store.settle(self.job, reserved, ceiling, inputs + outputs, cost)

    def on_llm_error(self, error, *, run_id, **kwargs):
        # Billing can be uncertain on a transport failure; do not release its ceiling.
        reservation = self.reservations.pop(run_id, None)
        if reservation:
            self.settle_billing(run_id, reservation[1])


def usage_callbacks():
    callback = active_usage.get()
    return [callback] if callback else []
