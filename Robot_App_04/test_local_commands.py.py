"""
Test Script for Local Commands
Tests all local command patterns without running the full system
"""

from local_commands import handle_local_command

def test_command(command, expected_action=None):
    """Test a single command and display results"""
    print(f"\n{'='*60}")
    print(f"🔹 Testing: '{command}'")
    print(f"{'='*60}")
    
    should_continue, response, action = handle_local_command(command)
    
    print(f"📤 Response: {response}")
    print(f"⚙️  Action: {action}")
    print(f"🔄 Continue to API: {should_continue}")
    
    if expected_action and action != expected_action:
        print(f"⚠️  WARNING: Expected action '{expected_action}', got '{action}'")
    
    return should_continue, response, action

def run_all_tests():
    """Run comprehensive test suite"""
    print("\n" + "="*60)
    print("🧪 LOCAL COMMAND HANDLER - TEST SUITE")
    print("="*60)
    
    # Test Cases
    test_cases = [
        # Greetings
        ("hello", 'resume'),
        ("hi there", 'resume'),
        ("مرحبا", 'resume'),
        ("هلا والله", 'resume'),
        
        # Goodbyes
        ("bye", 'pause'),
        ("goodbye", 'pause'),
        ("مع السلامة", 'pause'),
        ("وداعا", 'pause'),
        
        # Pause/Resume
        ("sleep mode", 'pause'),
        ("wake up", 'resume'),
        ("توقف", 'pause'),
        ("استيقظ", 'resume'),
        
        # Time queries
        ("what time is it", None),
        ("كم الساعة", None),
        
        # Date queries
        ("what date is it", None),
        ("ما التاريخ", None),
        
        # Thank you
        ("thank you", None),
        ("thanks", None),
        ("شكرا", None),
        ("شكرا جزيلا", None),
        
        # How are you
        ("how are you", None),
        ("كيف حالك", None),
        
        # Help
        ("help", None),
        ("مساعدة", None),
        
        # Should go to API
        ("what is the capital of France", None),
        ("اخبرني عن الطقس", None),
    ]
    
    passed = 0
    failed = 0
    api_calls = 0
    
    for command, expected_action in test_cases:
        try:
            should_continue, response, action = test_command(command, expected_action)
            
            if should_continue:
                api_calls += 1
                print("✅ Correctly forwarded to API")
            elif response:
                passed += 1
                print("✅ Handled locally - SUCCESS")
            else:
                failed += 1
                print("❌ No response generated - FAILED")
                
        except Exception as e:
            failed += 1
            print(f"❌ ERROR: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"✅ Local Commands Handled: {passed}")
    print(f"🔄 Forwarded to API: {api_calls}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Total Tests: {len(test_cases)}")
    print(f"🎯 Success Rate: {(passed/(passed+failed)*100):.1f}%" if (passed+failed) > 0 else "N/A")
    print("="*60)

def interactive_test():
    """Interactive testing mode"""
    print("\n" + "="*60)
    print("🎮 INTERACTIVE TEST MODE")
    print("="*60)
    print("Type commands to test (or 'quit' to exit)")
    print("Examples: 'hello', 'what time is it', 'bye'")
    print("="*60 + "\n")
    
    while True:
        try:
            command = input("🎤 Enter command: ").strip()
            
            if command.lower() in ['quit', 'exit', 'q']:
                print("👋 Exiting test mode...")
                break
            
            if not command:
                continue
            
            test_command(command)
            
        except KeyboardInterrupt:
            print("\n\n👋 Exiting test mode...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def benchmark_performance():
    """Benchmark local command performance"""
    import time
    
    print("\n" + "="*60)
    print("⚡ PERFORMANCE BENCHMARK")
    print("="*60)
    
    test_commands = [
        "hello",
        "what time is it",
        "thank you",
        "bye",
        "مرحبا",
        "كم الساعة"
    ]
    
    total_time = 0
    iterations = 1000
    
    print(f"Running {iterations} iterations per command...\n")
    
    for command in test_commands:
        start = time.time()
        for _ in range(iterations):
            handle_local_command(command)
        end = time.time()
        
        elapsed = end - start
        avg_time = (elapsed / iterations) * 1000  # Convert to milliseconds
        total_time += elapsed
        
        print(f"'{command:20s}' - Avg: {avg_time:.3f}ms ({iterations} iterations)")
    
    print(f"\n📊 Overall Average: {(total_time / (len(test_commands) * iterations)) * 1000:.3f}ms")
    print("="*60)

if __name__ == "__main__":
    import sys
    
    print("\n🎯 Local Command Testing Utility")
    print("Choose test mode:\n")
    print("1. Run All Tests")
    print("2. Interactive Mode")
    print("3. Performance Benchmark")
    print("4. Exit")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        run_all_tests()
    elif choice == "2":
        interactive_test()
    elif choice == "3":
        benchmark_performance()
    else:
        print("👋 Goodbye!")
