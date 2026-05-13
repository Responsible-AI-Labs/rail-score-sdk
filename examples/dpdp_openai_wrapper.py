"""
India DPDP — OpenAI wrapper with PII masking.

Demonstrates RAILOpenAI with DPDP content scanning that automatically
masks Indian PII in LLM responses.
"""

import asyncio
from rail_score_sdk.integrations import RAILOpenAI
from rail_score_sdk.compliance.dpdp import DPDPConfig


async def main():
    config = DPDPConfig(
        entity_type="data_fiduciary",
        sector="finance",
        pii_action="mask",
    )

    client = RAILOpenAI(
        openai_api_key="sk-...",
        rail_api_key="your-rail-api-key",
        rail_threshold=7.0,
        rail_policy="log_only",
        dpdp=config,
    )

    response = await client.chat_completion(
        model="gpt-4o",
        messages=[{
            "role": "user",
            "content": "Generate a sample KYC record for testing",
        }],
    )

    print(f"Content: {response.content}")
    print(f"RAIL Score: {response.rail_score}")
    print(f"Threshold met: {response.threshold_met}")

    if response.dpdp:
        print(f"\nDPDP Results:")
        print(f"  Compliant: {response.dpdp.compliant}")
        print(f"  PII found: {len(response.dpdp.pii_found)}")
        for pii in response.dpdp.pii_found:
            print(f"    {pii.type}: {pii.value} -> {pii.masked_value}")
        print(f"  Violations: {len(response.dpdp.violations)}")
        if response.dpdp.masked_content:
            print(f"  Masked output applied: yes")


if __name__ == "__main__":
    asyncio.run(main())
