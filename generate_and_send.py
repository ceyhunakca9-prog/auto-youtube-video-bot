import os
import sys
import time
import requests
from openai import OpenAI

# ==== Ortam değişkenleri (GitHub Secrets) ====
#   OPENAI_API_KEY
#   TELEGRAM_BOT_TOKEN
#   TELEGRAM_CHAT_ID

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)


def generate_sora_video(
    prompt: str,
    seconds: int = 4,
    size: str = "720x1280",
    model: str = "sora-2",
) -> str:
    """
    Sora ile video üretir ve 'sora_video.mp4' dosya yolunu döner.
    """

    # 1) Video üretim işini başlat
    video = client.videos.create(
        model=model,
        prompt=prompt,
        seconds=str(seconds),
        size=size,
    )

    print("Video generation started:", video.id)

    # 2) Durumu takip et (queued / in_progress)
    bar_length = 30
    progress = getattr(video, "progress", 0)

    while video.status in ("in_progress", "queued"):
        # Durumu yenile
        video = client.videos.retrieve(video.id)
        progress = getattr(video, "progress", 0)

        filled_length = int((progress / 100) * bar_length)
        bar = "=" * filled_length + "-" * (bar_length - filled_length)
        status_text = "Queued" if video.status == "queued" else "Processing"

        sys.stdout.write(f"\r{status_text}: [{bar}] {progress:.1f}%")
        sys.stdout.flush()
        time.sleep(10)

    sys.stdout.write("\n")

    # 3) Hata var mı kontrol et
    if video.status == "failed":
        message = getattr(
            getattr(video, "error", None),
            "message",
            "Video generation failed",
        )
        raise RuntimeError(f"Sora video hatası: {message}")

    print("Video generation completed:", video.id)
    print("Downloading video content...")

    # 4) Videoyu indir
    content = client.videos.download_content(video.id, variant="video")
    output_path = "sora_video.mp4"
    content.write_to_file(output_path)

    print("Video dosyası kaydedildi:", output_path)
    return output_path


def send_video_to_telegram(video_path: str, caption: str = "") -> None:
    """
    Telegram'a video gönderir.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"

    with open(video_path, "rb") as f:
        files = {"video": f}
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "caption": caption,
        }
        resp = requests.post(url, data=data, files=files, timeout=180)

    if not resp.ok:
        raise RuntimeError(
            f"Telegram gönderim hatası: {resp.status_code} {resp.text}"
        )

    print("Video Telegram'a gönderildi.")


if __name__ == "__main__":
    # Buradaki promptu istediğin gibi değiştirebilirsin
    PROMPT = (
        "Short vertical 4 second video, parkour / survival / satisfying style, "
        "dynamic camera movement, high detail, realistic lighting, smooth motion."
    )

    print("Sora ile video üretiliyor...")
    video_file = generate_sora_video(
        prompt=PROMPT,
        seconds=4,
        size="720x1280",
        model="sora-2",
    )

    print("Telegram'a gönderiliyor...")
    send_video_to_telegram(video_file, caption="Otomatik Sora deneme videosu ✅")
