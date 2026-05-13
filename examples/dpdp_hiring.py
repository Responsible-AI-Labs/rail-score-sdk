"""
India DPDP — Hiring system compliance flow.

Demonstrates DPDP compliance for an AI-powered hiring platform
that processes candidate personal data (Aadhaar, PAN, mobile).
"""

import asyncio
from rail_score_sdk.compliance.dpdp import DPDPCompliance, DPDPConfig


async def hiring_flow():
    config = DPDPConfig(
        entity_type="data_fiduciary",
        sector="employment",
        purpose="recruitment",
    )

    async with DPDPCompliance(api_key="your-rail-api-key", config=config) as dpdp:
        # Gate: Can we process this candidate's resume?
        decision = await dpdp.evaluate(
            action="process_resume",
            context={
                "data_type": "personal_data",
                "purpose": "candidate_screening",
                "consent_obtained": True,
                "data_principal_category": "job_applicant",
            },
        )
        print(f"Resume processing: {decision.verdict}")
        if decision.required_actions:
            for ra in decision.required_actions:
                print(f"  Required: {ra.type} — {ra.reason}")

        # Scan resume text for PII (server-side)
        resume_text = (
            "Name: Priya Sharma, Aadhaar: 2234 5678 9012, "
            "Mobile: +91 9876543210, PAN: ABCDE1234F"
        )
        scan = await dpdp.scan(content=resume_text)
        print(f"\nResume scan: {'compliant' if scan.compliant else 'non-compliant'}")
        print(f"PII items: {len(scan.pii_found)}")
        for item in scan.pii_found:
            print(f"  {item.type}: detected")

        # Client-side scan (zero latency, no API call)
        local_scan = dpdp.scan_local(resume_text)
        print(f"\nLocal scan PII: {len(local_scan.pii_found)}")
        for pii in local_scan.pii_found:
            print(f"  {pii.type}: {pii.value} -> {pii.masked_value}")

        # Record processing event
        await dpdp.emit(events=[{
            "type": "data.processed",
            "user_id": "candidate-456",
            "purpose": "candidate_screening",
            "data_types": ["name", "aadhaar", "mobile"],
        }])
        print("\nProcessing event recorded.")

        # Check requirements before shortlisting
        reqs = await dpdp.require(
            session_id="hiring-session-1",
            workflow_step="shortlisting",
            context={"decision_type": "automated_screening"},
        )
        print(f"\nShortlisting requirements: {len(reqs.required_actions)}")
        for action in reqs.required_actions:
            print(f"  [{action.priority}] {action.type}: {action.reason}")


if __name__ == "__main__":
    asyncio.run(hiring_flow())
