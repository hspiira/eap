"""
Mint a new key-encryption key (KEK) wrapped by AWS KMS, for
ENCRYPTION_KEY_PROVIDER=aws-kms. Run this once per environment, not per
deploy: running it again mints a *different* KEK, and anything already
encrypted under the old one becomes undecryptable until it is re-encrypted.

The plaintext KEK is never printed or written anywhere. Only its KMS-
encrypted ciphertext blob (safe to store in config, since only the KMS key
named by --kms-key-id can ever decrypt it back) and a short fingerprint for
verification are shown.

Requires the `kms` optional dependency group (`uv sync --extra kms`) and AWS
credentials with kms:GenerateDataKey and kms:Decrypt on the target key.

Example:

    uv run python scripts/generate_kms_kek.py \
        --kms-key-id arn:aws:kms:eu-central-1:123456789012:key/abcd-1234

Then set, in the target environment's config (never in version control):

    ENCRYPTION_KEY_PROVIDER=aws-kms
    ENCRYPTION_KMS_KEY_ID=<the same --kms-key-id>
    ENCRYPTION_KEK_CIPHERTEXT=<the CiphertextBlob this script prints>
"""

from __future__ import annotations

import argparse
import base64
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from app.core.encryption import _KEK_MIN_BYTES, hashes_fingerprint  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Mint a KMS-wrapped key-encryption key for field-level encryption.",
    )
    p.add_argument(
        "--kms-key-id",
        required=True,
        help="AWS KMS key id or ARN to wrap the KEK with (an alias also works, e.g. alias/evexia-kek)",
    )
    p.add_argument(
        "--region",
        default=None,
        help="AWS region for the KMS client, if not already set via AWS_DEFAULT_REGION",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    try:
        import boto3
    except ImportError:
        print(
            "boto3 is not installed. Run `uv sync --extra kms` first.",
            file=sys.stderr,
        )
        sys.exit(1)

    client = boto3.client("kms", region_name=args.region) if args.region else boto3.client("kms")

    response = client.generate_data_key(KeyId=args.kms_key_id, KeySpec="AES_256")
    plaintext_kek: bytes = response["Plaintext"]
    ciphertext_blob: bytes = response["CiphertextBlob"]

    if len(plaintext_kek) < _KEK_MIN_BYTES:
        print(
            f"KMS returned a {len(plaintext_kek)}-byte key, need >= {_KEK_MIN_BYTES}. Aborting.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Verify the round trip now, while we still hold the plaintext to compare
    # against, so a misconfigured key policy is caught here rather than at
    # the first real request in production.
    decrypted = client.decrypt(CiphertextBlob=ciphertext_blob, KeyId=args.kms_key_id)["Plaintext"]
    if decrypted != plaintext_kek:
        print(
            "KMS decrypt did not return the same key it just generated. Aborting.", file=sys.stderr
        )
        sys.exit(1)

    fingerprint = hashes_fingerprint(plaintext_kek).hex()
    ciphertext_b64 = base64.b64encode(ciphertext_blob).decode("ascii")

    # The plaintext key is discarded here; nothing below this line touches it.
    print("KMS round trip verified. Set these in the target environment's config:")
    print()
    print("ENCRYPTION_KEY_PROVIDER=aws-kms")
    print(f"ENCRYPTION_KMS_KEY_ID={args.kms_key_id}")
    print(f"ENCRYPTION_KEK_CIPHERTEXT={ciphertext_b64}")
    print()
    print(f"KEK fingerprint (for cross-checking against logs, never the key itself): {fingerprint}")
    print()
    print(
        "This ciphertext is safe to store in config: only the KMS key above can "
        "ever decrypt it. It is not safe to lose without a backup of the KMS key "
        "policy, since losing this value with no other copy makes every row "
        "encrypted under it permanently unrecoverable."
    )


if __name__ == "__main__":
    main()
