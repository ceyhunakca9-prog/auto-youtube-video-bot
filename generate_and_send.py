import os
import time
import requests

# Ortam değişkenleri (GitHub Secrets'tan gelecek)
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

OPENAI_API_BASE = "https://api.openai.com/v1"


def generate_sora_video(prompt: str, seconds: int = 4, size: str = "720x1280") -> str:
    """
    Sora ile text-to-video generation başlatır ve video_id döner.
    """
    url = f"{OPENAI_API_BASE}/videos/generations"

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }

    data = {
        "model": "sora-2",           # istersen "sora-2-pro" da deneyebiliriz
        "prompt": prompt,
        "seconds": str(seconds),     # "4", "8", "12" gibi değerler
        "size": size,                # "720x1280" (dikey) veya "1280x720" (yatay)
    }

    resp = requests.post(url, headers=headers, json=data)
    print("OpenAI response status:", resp.status_code)
    print("OpenAI response text:", resp.text)
    resp.raise_for_status()
    result = resp.json()
    video_id = result["id"]
    return video_id


def download_video(video_id: str, filename: str = "output.mp4") -> str:
    """
    /videos/{video_id}/content endpoint'inden MP4 indirir.
    """
    url = f"{OPENAI_API_BASE}/videos/{video_id}/content"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }

    with requests.get(url, headers=headers, stream=True) as r:
        print("Download status:", r.status_code)
        r.raise_for_status()
        with open(filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    return filename


def send_telegram_video(file_path: str, caption: str):
    """
    Telegram Bot API ile videoyu gönderir.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"

    with open(file_path, "rb") as video_file:
        files = {
            "video": video_file,
        }
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "caption": caption,
        }
        resp = requests.post(url, data=data, files=files)
        print("Telegram status:", resp.status_code)
        print("Telegram response:", resp.text)
        resp.raise_for_status()
        return resp.json()


def main():
    # Şimdilik sabit bir prompt; sonra otomatik senaryoya çevireceğiz.
    prompt = (
        "cinematic vertical shot of a parkour runner jumping between rooftops at sunset, "
        "smooth camera movement, realistic lighting, very satisfying slow motion, 4 seconds"
    )

    print("Sora ile video oluşturma isteği gönderiliyor...")
    video_id = generate_sora_video(prompt, seconds=4, size="720x1280")
    print("Video ID alındı:", video_id)

    print("Video işlenmesi için biraz bekleniyor...")
    time.sleep(25)  # render süresi için kısa bekleme

    print("MP4 dosyası indiriliyor...")
    video_path = download_video(video_id, filename="sora_output.mp4")
    print("İndirildi:", video_path)

    print("Telegram'a gönderiliyor...")
    tg_resp = send_telegram_video(
        video_path,
        caption=f"Sora ile otomatik üretilmiş video 🎥\nPrompt: {prompt}",
    )
    print("Telegram cevabı:", tg_resp)


if __name__ == "__main__":
    main()
