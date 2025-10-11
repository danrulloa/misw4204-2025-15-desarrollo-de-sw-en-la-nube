from celery import shared_task
import time

@shared_task(name="tasks.process_video.run")
def run(video_path: str):
    print(f"[Worker] Procesando video: {video_path}")
    for i in range(5):
        print(f"[Worker] Progreso: {20 * (i + 1)}%")
        time.sleep(1)
    print(f"[Worker] Video procesado correctamente: {video_path}")
    return {"status": "ok", "video": video_path}
