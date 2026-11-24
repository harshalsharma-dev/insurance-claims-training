import asyncio
import logging

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)


async def send_claim_notification(email: str, claim_id: int):
    print("BACKGROUND TASK STARTED", flush=True)

    message = (
        f"Your insurance claim with ID {claim_id} "
        "has been successfully submitted. "
        "Our team will review your claim."
    )

    await asyncio.sleep(2)

    logger.info("Claim notification sent to %s: %s", email, message)

    print("BACKGROUND TASK COMPLETED", flush=True)
