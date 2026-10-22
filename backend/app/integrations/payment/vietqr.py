"""VietQR payment utility for dynamic Napas 247 QR code generation.

Generates standard VietQR images and structured bank transfer details
that can be scanned by any Vietnamese Mobile Banking application.
"""

from decimal import Decimal
from typing import Any, Dict
from urllib.parse import quote

# Default banking credentials for Novelia Books
DEFAULT_BANK_ID = "TCB"  # Techcombank (also supports MB, VCB, ICB, etc.)
DEFAULT_BANK_NAME = "Techcombank (Napas 247)"
DEFAULT_ACCOUNT_NO = "7979798950"
DEFAULT_ACCOUNT_NAME = "NOVELIA BOOKS VIETNAM"


def get_vietqr_url(
    order_code: str,
    amount: Decimal | float | int,
    bank_id: str = DEFAULT_BANK_ID,
    account_no: str = DEFAULT_ACCOUNT_NO,
    account_name: str = DEFAULT_ACCOUNT_NAME,
    template: str = "compact2",
) -> str:
    """Generate dynamic VietQR image URL with embedded amount and order memo.

    Format: https://img.vietqr.io/image/{bank_id}-{account_no}-{template}.png
    """
    int_amount = int(amount)
    memo = order_code.strip()
    encoded_memo = quote(memo)
    encoded_name = quote(account_name)

    return (
        f"https://img.vietqr.io/image/{bank_id}-{account_no}-{template}.png"
        f"?amount={int_amount}&addInfo={encoded_memo}&accountName={encoded_name}"
    )


def get_vietqr_info(
    order_code: str,
    amount: Decimal | float | int,
    bank_id: str = DEFAULT_BANK_ID,
    bank_name: str = DEFAULT_BANK_NAME,
    account_no: str = DEFAULT_ACCOUNT_NO,
    account_name: str = DEFAULT_ACCOUNT_NAME,
) -> Dict[str, Any]:
    """Return complete bank transfer metadata for display in chat or invoice."""
    return {
        "bank_id": bank_id,
        "bank_name": bank_name,
        "account_no": account_no,
        "account_name": account_name,
        "amount": int(amount),
        "transfer_content": order_code,
        "memo": order_code,
        "qr_image_url": get_vietqr_url(
            order_code=order_code,
            amount=amount,
            bank_id=bank_id,
            account_no=account_no,
            account_name=account_name,
        ),
    }
