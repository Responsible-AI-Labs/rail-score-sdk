"""
India DPDP — Healthcare chatbot with child detection.

Demonstrates RAILSession with DPDP integration for a healthcare
chatbot that must detect and protect child data across turns.
"""

import asyncio
from rail_score_sdk import RAILSession
from rail_score_sdk.compliance.dpdp import DPDPConfig


async def healthcare_chatbot():
    config = DPDPConfig(
        entity_type="data_fiduciary",
        sector="healthcare",
        purpose="health_advisory",
        processes_children=True,
        child_content_action="block",
        pii_action="mask",
    )

    async with RAILSession(
        api_key="your-rail-api-key",
        threshold=7.0,
        policy="regenerate",
        mode="basic",
        domain="healthcare",
        dpdp=config,
    ) as session:
        # Turn 1: Adult patient query
        result1 = await session.evaluate_turn(
            user_message="What are common cold symptoms?",
            assistant_response=(
                "Common cold symptoms include runny nose, sore throat, "
                "coughing, sneezing, and mild fever. Rest and fluids are "
                "recommended. Consult a doctor if symptoms persist beyond 10 days."
            ),
        )
        print(f"Turn 1 score: {result1.score}")

        # Turn 2: Child detected in conversation
        result2 = await session.evaluate_turn(
            user_message="My 8 year old daughter has a fever of 102F",
            assistant_response=(
                "For a child with 102F fever, give age-appropriate ibuprofen "
                "and ensure hydration. Consult a pediatrician if fever persists "
                "beyond 24 hours or if the child shows signs of dehydration."
            ),
        )
        print(f"Turn 2 score: {result2.score}")

        # Turn 3: Follow-up — session now knows about child
        result3 = await session.evaluate_turn(
            user_message="Should I give her antibiotics?",
            assistant_response=(
                "Do not give antibiotics without a doctor's prescription. "
                "Antibiotics are only effective against bacterial infections, "
                "not viral ones. Please consult your pediatrician first."
            ),
        )
        print(f"Turn 3 score: {result3.score}")

        # Check DPDP compliance summary
        summary = session.dpdp_summary()
        print(f"\nDPDP Session Summary:")
        print(f"  Child data detected: {summary['child_data_detected']}")
        print(f"  Child age: {summary.get('child_age')}")
        print(f"  PII found total: {summary['pii_found_total']}")
        print(f"  Violations: {summary['violations']}")
        print(f"  Actions taken: {len(summary['actions_taken'])}")
        for action in summary["actions_taken"]:
            print(f"    Turn {action['turn']}: {action['check']} -> {action['action']}")

        # Session-level scores
        scores = session.scores_summary()
        print(f"\nSession Scores:")
        print(f"  Average: {scores['average_score']}")
        print(f"  Lowest: {scores['lowest_score']}")
        print(f"  Turns below threshold: {scores['turns_below_threshold']}")


if __name__ == "__main__":
    asyncio.run(healthcare_chatbot())
