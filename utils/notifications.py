import asyncio
import logging
import time

from utils.celery_app import celery_app

logger = logging.getLogger(__name__)


async def send_claim_notification(email: str, claim_id: int):
    logger.info(
        "Claim notification started",
        extra={"claim_id": claim_id},
    )

    message = (
        f"Your insurance claim with ID {claim_id} "
        "has been successfully submitted. "
        "Our team will review your claim."
    )

    await asyncio.sleep(2)

    logger.info(
        "Claim notification completed: %s",
        message,
        extra={"claim_id": claim_id},
    )


@celery_app.task(name="send_welcome_notification")
def send_welcome_notification(email: str, name: str):
    logger.info("Welcome notification started")

    message = (
        f"Hello {name}, welcome to Insurance Claims Management! "
        "Your account has been successfully created."
    )

    time.sleep(2)

    logger.info("Welcome notification completed: %s", message)
