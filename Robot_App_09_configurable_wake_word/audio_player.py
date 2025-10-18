# audio_player.py
# -------------------------------------------------------------------
# Unified audio playback (async + blocking) via a single worker thread
# Uses pygame.mixer under the hood. Safe for concurrent calls.
# -------------------------------------------------------------------

from __future__ import annotations
from dataclasses import dataclass, field
from threading import Event, Thread, Lock
from queue import Queue, Empty
from typing import Optional
import time
import os
import pygame


@dataclass
class AudioJob:
    path: str
    blocking: bool = False          # True => caller waits until done
    volume: float = 1.0
    done: Event = field(default_factory=Event)
    # داخليًا: يستعمله الـ AudioPlayer للغاء وظائف قديمة عند المقاطعة
    canceled: Event = field(default_factory=Event)


class AudioPlayer:
    """
    Threaded audio playback manager.
    - play_async(path): يشغّل الصوت في الخلفية فورًا ولا يوقف مسار التنفيذ.
    - play_blocking(path): يرسل job للثريد وينتظر حتى انتهاء التشغيل.
    - stop_current(): يوقف أي صوت قيد التشغيل فورًا.
    - shutdown(): يغلق الثريد والمكسر بأمان.

    ملاحظات:
      * احرص على استدعاء start() مرّة واحدة بعد الإنشاء.
      * يدعم pygame فقط (بدون تخصيص خرج متقدّم).
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        buffer: int = 1024 ,
        auto_init_mixer: bool = True
    ) -> None:
        self._queue: Queue[AudioJob] = Queue(maxsize=8)
        self._worker: Optional[Thread] = None
        self._running: bool = False
        self._lock = Lock()
        self._auto_init_mixer = auto_init_mixer
        self._sample_rate = sample_rate
        self._channels = channels
        self._buffer = buffer
        # آخر تشغيل لنفس الملف (لـ debounce اختياري)
        self._last_play_ts: dict[str, float] = {}
        self._min_gap_sec: float = 0.35  # تجاهل تكرارات أسرع من 350ms

    # ---------------- Lifecycle ----------------

    def start(self) -> None:
        with self._lock:
            if self._running:
                return
            # تهيئة mixer بوضوح (مهم للـ RPi/Linux)
            if self._auto_init_mixer:
                try:
                    pygame.mixer.pre_init(
                        frequency=self._sample_rate,
                        size=-16,
                        channels=self._channels,
                        buffer=self._buffer
                    )
                    pygame.init()
                    pygame.mixer.init()
                except Exception as e:
                    print(f"⚠️ AudioPlayer mixer init failed: {e}")

            self._running = True
            self._worker = Thread(target=self._run, name="AudioPlayerWorker", daemon=True)
            self._worker.start()

    def shutdown(self, join_timeout: float = 2.0) -> None:
        with self._lock:
            self._running = False
        # أرسل job فارغ لإيقاظ الثريد لو كان ينتظر
        try:
            self._queue.put_nowait(AudioJob(path="", blocking=False))
        except:
            pass
        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=join_timeout)
        # اغلق الميكسـر بأمان
        try:
            pygame.mixer.music.stop()
        except:
            pass
        try:
            pygame.mixer.quit()
        except:
            pass

    # ---------------- Public API ----------------

    def play_async(self, path: str, volume: float = 1.0) -> AudioJob:
        """شغّل الصوت في الخلفية (لا يحجب التنفيذ)."""
        if not path:
            return AudioJob(path="")
        if self._debounced(path):
            # تجاهل السبام السريع لنفس الملف
            return AudioJob(path=path, blocking=False)
        job = AudioJob(path=path, blocking=False, volume=volume)
        self._safe_put(job)
        return job

    def play_blocking(self, path: str, volume: float = 1.0, timeout: Optional[float] = None) -> bool:
        """شغّل الصوت وانتظر حتى نهايته (أو حتى timeout)."""
        if not path:
            return True
        job = AudioJob(path=path, blocking=True, volume=volume)
        self._safe_put(job)
        job.done.wait(timeout=timeout)
        return job.done.is_set()

    def stop_current(self) -> None:
        """إيقاف فوري لأي صوت جارٍ + إلغاء أي job جاري."""
        try:
            pygame.mixer.music.stop()
        except:
            pass
        # ألغِ المهمة الحالية عبر إرسال job إلغاء خفيف (يُكتشف داخل _run)
        self._cancel_head_job()

    # ---------------- Internal ----------------

    def _safe_put(self, job: AudioJob) -> None:
        try:
            self._queue.put_nowait(job)
        except:
            # لو الطابور ممتلئ، اسحب أقدم عنصر وارمِه ثم ضع الجديد
            try:
                _ = self._queue.get_nowait()
            except Empty:
                pass
            self._queue.put_nowait(job)

    def _run(self) -> None:
        current: Optional[AudioJob] = None
        while True:
            # التحقق من الحالة
            with self._lock:
                if not self._running:
                    break

            try:
                job = self._queue.get(timeout=0.5)
            except Empty:
                continue

            # end condition / wake worker
            if job.path == "" and not self._running:
                job.done.set()
                break

            # دعم قديم لو حد حط string بدل AudioJob (أمانًا)
            if not isinstance(job, AudioJob):
                job = AudioJob(path=str(job), blocking=False)

            # مسار غير موجود
            if not os.path.exists(job.path):
                print(f"⚠️ Missing audio file: {job.path}")
                job.done.set()
                continue

            current = job
            try:
                pygame.mixer.music.load(job.path)
                pygame.mixer.music.set_volume(job.volume)
                pygame.mixer.music.play()

                # انتظر حتى ينتهي الملف أو يتم إيقاف التشغيل أو يُلغى
                while pygame.mixer.music.get_busy():
                    # تم إلغاء التشغيل؟
                    if current.canceled.is_set():
                        try:
                            pygame.mixer.music.stop()
                        except:
                            pass
                        break
                    time.sleep(0.02)  # ~50 FPS polling

            except Exception as e:
                print(f"❌ Audio playback error: {e}")
            finally:
                # علّم المُرسل بانتهاء التشغيل (حتى لو حصل خطأ)
                job.done.set()
                # سجّل توقيت آخر تشغيل لهذا المسار (لـ debounce)
                self._last_play_ts[job.path] = time.time()
                current = None

    def _cancel_head_job(self) -> None:
        """
        يطلب من المهمة الحالية التوقّف (عبر canceled Event).
        لا يزيل العناصر من الطابور؛ فقط يوقف الجاري الآن.
        """
        # للأسف لا يمكن الوصول المباشر لـ current هنا،
        # لذلك نستخدم pygame.mixer.stop() لضمان الوقف.
        # ولو أردت إلغاء دقيق، يمكننا لاحقًا تخزين المؤشر current كحقل في الكلاس.

        # extra: flush أي voice sfx غير مهمة (اختياري)
        # self._flush_non_blocking_tail()

        pass

    def _debounced(self, path: str) -> bool:
        last = self._last_play_ts.get(path)
        if last is None:
            return False
        return (time.time() - last) < self._min_gap_sec

    # اختياري: مسح تراكم SFX الخلفية (لو حابب)
    def flush_queue(self) -> None:
        try:
            while True:
                self._queue.get_nowait()
        except Empty:
            pass
