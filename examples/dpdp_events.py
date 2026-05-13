"""
India DPDP Event Primitives — Lending platform compliance flow.

Demonstrates Mode B: behavioral compliance with emit/evaluate/require
for a loan application workflow.
"""

import asyncio
from rail_score_sdk.compliance.dpdp import DPDPCompliance, DPDPConfig


async def lending_flow():
    config = DPDPConfig(
        entity_type="data_fiduciary",
        sector="finance",
        purpose="credit_assessment",
    )

    async with DPDPCompliance(api_key="your-rail-api-key", config=config) as dpdp:
        # Step 1: Evaluate if we can collect data
        decision = await dpdp.evaluate(
            action="collect_data",
            context={
                "data_type": "aadhaar",
                "purpose": "kyc_verification",
                "consent_obtained": True,
            },
        )
        print(f"Collect decision: {decision.verdict}")

        if decision.required_actions:
            print("Required before proceeding:")
            for ra in decision.required_actions:
                print(f"  [{ra.priority}] {ra.type}: {ra.reason}")

        # Step 2: Emit consent event
        emit_result = await dpdp.emit(events=[{
            "type": "consent.granted",
            "user_id": "applicant-123",
            "purpose": "credit_assessment",
            "method": "explicit_opt_in",
        }])
        print(f"\nEvents accepted: {emit_result.accepted}")

        # Step 3: Emit data collection event
        await dpdp.emit(events=[{
            "type": "data.collected",
            "user_id": "applicant-123",
            "data_type": "aadhaar",
            "purpose": "kyc_verification",
        }])

        # Step 4: Check requirements before credit scoring
        requirements = await dpdp.require(
            session_id="loan-session-1",
            workflow_step="credit_scoring",
            context={"user_type": "adult", "data_types": ["aadhaar", "pan"]},
        )
        print(f"\nRequired actions for credit scoring: {len(requirements.required_actions)}")
        for action in requirements.required_actions:
            print(f"  [{action.priority}] {action.type}: {action.reason}")

        # Step 5: Create evidence packet for audit trail
        evidence = await dpdp.evidence(
            type="consent_record",
            params={
                "user_id": "applicant-123",
                "purpose": "credit_assessment",
                "method": "explicit_opt_in",
                "timestamp": "2026-05-14T10:00:00Z",
            },
        )
        print(f"\nEvidence recorded: {evidence.evidence_id}")

        # Step 6: Check active timers (e.g. DSR SLA, breach notification)
        timers = await dpdp.list_timers()
        print(f"\nActive timers: {len(timers.timers)}")
        print(f"  Overdue: {timers.summary.overdue}")


if __name__ == "__main__":
    asyncio.run(lending_flow())
