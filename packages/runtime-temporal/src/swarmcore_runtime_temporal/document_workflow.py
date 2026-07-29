from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import Any, cast

from temporalio import workflow
from temporalio.common import RetryPolicy


@workflow.defn(name="DocumentProcessingWorkflow")
class DocumentProcessingWorkflow:
    @workflow.run
    async def run(self, input_value: dict[str, Any]) -> dict[str, Any]:
        plan = await workflow.execute_activity(
            "plan_document_processing",
            input_value,
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=RetryPolicy(
                maximum_attempts=2,
                initial_interval=timedelta(seconds=2),
                maximum_interval=timedelta(minutes=1),
            ),
            result_type=dict[str, Any],
        )
        groups = [
            dict(value)
            for value in plan.get("groups") or []
            if isinstance(value, dict)
        ]
        group_results: list[dict[str, Any]] = []
        for offset in range(0, len(groups), 4):
            tasks = [
                workflow.execute_activity(
                    "process_document_group",
                    {**input_value, "group": group},
                    start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=RetryPolicy(
                        maximum_attempts=2,
                        initial_interval=timedelta(seconds=2),
                        maximum_interval=timedelta(minutes=2),
                    ),
                    result_type=dict[str, Any],
                )
                for group in groups[offset : offset + 4]
            ]
            group_results.extend(await asyncio.gather(*tasks))
        return cast(
            dict[str, Any],
            await workflow.execute_activity(
                "finalize_document_processing",
                {**input_value, "plan": plan, "groups": group_results},
                start_to_close_timeout=timedelta(minutes=90),
                retry_policy=RetryPolicy(
                    maximum_attempts=2,
                    initial_interval=timedelta(seconds=5),
                    maximum_interval=timedelta(minutes=2),
                ),
                result_type=dict[str, Any],
            ),
        )
