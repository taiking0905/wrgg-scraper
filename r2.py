import os
import boto3
from dotenv import load_dotenv
from config import DATA_DIR

load_dotenv()

BUCKET = os.getenv("R2_BUCKET")

s3 = boto3.client(
    "s3",
    endpoint_url=f"https://{os.getenv('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
    aws_access_key_id=os.getenv("R2_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("R2_SECRET_KEY"),
    region_name="auto"
)


def sync_from_r2():
    """
    R2(data/) → DATA_DIR
    """
    print("[R2] Download Start")

    os.makedirs(DATA_DIR, exist_ok=True)

    response = s3.list_objects_v2(
        Bucket=BUCKET,
        Prefix="data/"
    )

    if "Contents" not in response:
        print("[R2] data/ が空です")
        return

    for obj in response["Contents"]:
        key = obj["Key"]

        # data/ 自体はスキップ
        if key.endswith("/"):
            continue

        # data/champions.json
        # ↓
        # champions.json
        relative_key = key.removeprefix("data/")

        local_path = os.path.join(
            DATA_DIR,
            relative_key
        )

        os.makedirs(
            os.path.dirname(local_path),
            exist_ok=True
        )

        print(f"[DOWNLOAD] {key}")

        s3.download_file(
            BUCKET,
            key,
            local_path
        )

    print("[R2] Download Complete")


def sync_to_r2():
    """
    DATA_DIR → R2(data/)
    """
    print("[R2] Upload Start")

    for root, dirs, files in os.walk(DATA_DIR):
        for file in files:
            local_path = os.path.join(root, file)

            relative_path = os.path.relpath(
                local_path,
                DATA_DIR
            ).replace("\\", "/")

            # R2では data/ 配下に保存
            key = f"data/{relative_path}"

            print(f"[UPLOAD] {key}")

            s3.upload_file(
                local_path,
                BUCKET,
                key
            )

    print("[R2] Upload Complete")