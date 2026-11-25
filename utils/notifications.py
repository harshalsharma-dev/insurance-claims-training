import asyncio
import logging
import time

from utils.celery_app import celery_app

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


# async def send_welcome_notification(email: str, name: str):
#     message = (
#         f"Hello {name}, welcome to Insurance Claims Management! "
#         "Your account has been successfully created."
#     )

#     print("WELCOME NOTIFICATION STARTED", flush=True)

#     # Simulate email processing delay
#     await asyncio.sleep(2)

#     logger.info("Welcome notification sent to %s: %s", email, message)

#     print("WELCOME NOTIFICATION COMPLETED", flush=True)


@celery_app.task(name="send_welcome_notification")
def send_welcome_notification(email: str, name: str):
    message = (
        f"Hello {name}, welcome to Insurance Claims Management! "
        "Your account has been successfully created."
    )

    print("WELCOME NOTIFICATION STARTED", flush=True)

    # Simulate email processing delay

    time.sleep(2)

    logger.info("Welcome notification sent to %s: %s", email, message)

    print("WELCOME NOTIFICATION COMPLETED", flush=True)
