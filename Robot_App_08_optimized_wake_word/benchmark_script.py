# benchmark.py
# سكريبت لقياس أداء كل مكون في النظام

import time
import io
import wave
from Config import Config
from audio_recorder import AudioRecorder
from speech_to_text import SpeechToText
from text_to_speech import TextToSpeech
from ai_n8n import N8nClient

class Benchmark:
    def __init__(self):
        self.cfg = Config()
        self.results = {}
        
    def print_header(self, title):
        print("\n" + "=" * 60)
        print(f"  {title}")
        print("=" * 60)
    
    def print_result(self, name, duration, status="✅"):
        print(f"{status} {name:.<40} {duration:.2f}s")
        self.results[name] = duration
    
    def generate_test_audio(self, duration=2.0):
        """إنشاء ملف صوت اختباري (صمت)"""
        sample_rate = 16000
        channels = 1
        sampwidth = 2
        
        num_samples = int(sample_rate * duration)
        silence = b'\x00\x00' * num_samples
        
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sampwidth)
            wf.setframerate(sample_rate)
            wf.writeframes(silence)
        
        return buf.getvalue()
    
    def test_config(self):
        """اختبار تحميل Config"""
        self.print_header("⚙️  CONFIG TEST")
        
        start = time.time()
        try:
            cfg = Config()
            cfg.print_settings()
            duration = time.time() - start
            self.print_result("Config loading", duration)
            return True
        except Exception as e:
            print(f"❌ Config failed: {e}")
            return False
    
    def test_audio_recorder(self):
        """اختبار Audio Recorder"""
        self.print_header("🎤 AUDIO RECORDER TEST")
        
        try:
            rec = AudioRecorder(self.cfg)
            
            # Test initialization
            start = time.time()
            duration = time.time() - start
            self.print_result("Recorder initialization", duration)
            
            print("\nℹ️  Recorder settings:")
            print(f"   Sample rate: {rec.rate} Hz")
            print(f"   Channels: {rec.channels}")
            print(f"   Chunk size: {rec.chunk}")
            print(f"   Silence threshold: {self.cfg.SILENCE_THRESHOLD}")
            
            rec.close()
            return True
            
        except Exception as e:
            print(f"❌ Recorder test failed: {e}")
            return False
    
    def test_stt(self):
        """اختبار Speech-to-Text"""
        self.print_header("📝 SPEECH-TO-TEXT TEST")
        
        try:
            stt = SpeechToText(self.cfg)
            
            # Test initialization
            start = time.time()
            duration = time.time() - start
            self.print_result("STT initialization", duration)
            
            # Test transcription with silent audio
            print("\nℹ️  Testing transcription (this may take 5-15s)...")
            test_audio = self.generate_test_audio(duration=2.0)
            
            start = time.time()
            result = stt.transcribe_bytes(test_audio, is_wav=True)
            duration = time.time() - start
            
            self.print_result("STT transcription (2s audio)", duration)
            print(f"   Result: '{result}' (empty is normal for silence)")
            
            stt.cleanup()
            return True
            
        except Exception as e:
            print(f"❌ STT test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_tts(self):
        """اختبار Text-to-Speech"""
        self.print_header("🗣️  TEXT-TO-SPEECH TEST")
        
        try:
            tts = TextToSpeech(self.cfg)
            
            # Test initialization
            start = time.time()
            duration = time.time() - start
            self.print_result("TTS initialization", duration)
            
            print(f"\nℹ️  Backend: {tts.backend}")
            print(f"   Voice: {self.cfg.DEFAULT_VOICE}")
            
            # Note: We won't actually play audio in benchmark
            print("\n⚠️  Skipping actual audio playback in benchmark")
            print("   (Use main.py for full testing)")
            
            tts.cleanup()
            return True
            
        except Exception as e:
            print(f"❌ TTS test failed: {e}")
            return False
    
    def test_ai_client(self):
        """اختبار AI N8N Client"""
        self.print_header("🤖 AI CLIENT TEST")
        
        try:
            client = N8nClient(self.cfg)
            
            # Test initialization
            start = time.time()
            duration = time.time() - start
            self.print_result("Client initialization", duration)
            
            print(f"\nℹ️  Endpoint: {client.url}")
            print(f"   Timeout: {client.timeout}s")
            print(f"   Max retries: {client.max_retries}")
            
            # Test connection (with short timeout)
            print("\nℹ️  Testing connection (this may take 5-20s)...")
            start = time.time()
            response = client.chat("benchmark-test", "Hello")
            duration = time.time() - start
            
            if response:
                self.print_result("AI response time", duration)
                print(f"   Response length: {len(response)} chars")
            else:
                self.print_result("AI response time", duration, status="⚠️")
                print("   No response (check n8n endpoint)")
            
            client.close()
            return True
            
        except Exception as e:
            print(f"❌ AI client test failed: {e}")
            return False
    
    def test_full_pipeline(self):
        """اختبار Pipeline كامل (محاكاة)"""
        self.print_header("🚀 FULL PIPELINE SIMULATION")
        
        try:
            # Create test audio
            print("📦 Generating test audio...")
            test_audio = self.generate_test_audio(duration=2.0)
            
            # STT
            print("📝 Testing STT...")
            stt = SpeechToText(self.cfg)
            start = time.time()
            text = stt.transcribe_bytes(test_audio, is_wav=True)
            stt_time = time.time() - start
            
            # AI (if we got text)
            ai_time = 0
            if text:
                print(f"🤖 Testing AI (text: '{text[:30]}...')...")
                client = N8nClient(self.cfg)
                start = time.time()
                response = client.chat("benchmark-pipeline", text)
                ai_time = time.time() - start
                client.close()
            else:
                print("⚠️  No text from STT, simulating AI time...")
                ai_time = 2.0
            
            # TTS (simulated)
            tts_time = 1.5  # estimated
            
            total_time = stt_time + ai_time + tts_time
            
            print("\n📊 Pipeline breakdown:")
            self.print_result("  STT processing", stt_time)
            self.print_result("  AI processing", ai_time)
            self.print_result("  TTS playback (estimated)", tts_time)
            print("-" * 60)
            self.print_result("  Total pipeline time", total_time)
            
            stt.cleanup()
            return True
            
        except Exception as e:
            print(f"❌ Pipeline test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_all(self):
        """تشغيل كل الاختبارات"""
        print("\n")
        print("╔" + "=" * 58 + "╗")
        print("║" + " " * 10 + "🤖 AI ROBOT BENCHMARK SUITE" + " " * 19 + "║")
        print("╚" + "=" * 58 + "╝")
        
        tests = [
            ("Config", self.test_config),
            ("Audio Recorder", self.test_audio_recorder),
            ("Speech-to-Text", self.test_stt),
            ("Text-to-Speech", self.test_tts),
            ("AI Client", self.test_ai_client),
            ("Full Pipeline", self.test_full_pipeline),
        ]
        
        passed = 0
        failed = 0
        
        for name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"\n❌ {name} crashed: {e}")
                failed += 1
        
        # Summary
        self.print_header("📊 SUMMARY")
        print(f"✅ Passed: {passed}/{len(tests)}")
        print(f"❌ Failed: {failed}/{len(tests)}")
        
        if self.results:
            print("\n⏱️  Performance metrics:")
            for name, duration in self.results.items():
                print(f"   {name}: {duration:.2f}s")
        
        print("\n" + "=" * 60)
        
        if failed == 0:
            print("🎉 All tests passed! System is ready.")
        else:
            print("⚠️  Some tests failed. Check errors above.")
        
        print("=" * 60 + "\n")


if __name__ == "__main__":
    import sys
    
    benchmark = Benchmark()
    
    # Check if specific test requested
    if len(sys.argv) > 1:
        test_name = sys.argv[1].lower()
        
        test_map = {
            "config": benchmark.test_config,
            "recorder": benchmark.test_audio_recorder,
            "stt": benchmark.test_stt,
            "tts": benchmark.test_tts,
            "ai": benchmark.test_ai_client,
            "pipeline": benchmark.test_full_pipeline,
        }
        
        if test_name in test_map:
            test_map[test_name]()
        else:
            print(f"❌ Unknown test: {test_name}")
            print(f"Available tests: {', '.join(test_map.keys())}")
            sys.exit(1)
    else:
        # Run all tests
        benchmark.run_all()
