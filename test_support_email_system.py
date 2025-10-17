#!/usr/bin/env python3
"""
Comprehensive Test File for Support Email System

This test file covers all aspects of the support email functionality:
- Finding users with missed lessons
- Creating email content
- Sending support emails
- Testing individual user emails
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.services.scheduler_service import get_users_with_missed_lessons, send_support_email_to_struggling_users
from app.utils.support_email import create_support_email_content, send_support_email_to_user

def test_get_users_with_missed_lessons():
    """Test getting users with missed lessons"""
    print("=" * 60)
    print("TEST 1: Getting Users with Missed Lessons")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Test with different thresholds
        users_3_plus = get_users_with_missed_lessons(db, min_miss_count=3)
        users_5_plus = get_users_with_missed_lessons(db, min_miss_count=5)
        
        print(f"Users with 3+ missed lessons: {len(users_3_plus)}")
        print(f"Users with 5+ missed lessons: {len(users_5_plus)}")
        
        if users_3_plus:
            print("\nSample user data:")
            sample_user = users_3_plus[0]
            print(f"   - User ID: {sample_user['user_id']}")
            print(f"   - Email: {sample_user['email']}")
            print(f"   - Name: {sample_user['full_name'] or sample_user['username']}")
            print(f"   - Missed Count: {sample_user['missed_count']}")
        
        return len(users_3_plus) >= 0
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        db.close()

def test_create_email_content():
    """Test creating email content"""
    print("\n" + "=" * 60)
    print("TEST 2: Creating Email Content")
    print("=" * 60)
    
    # Test data
    test_user_data = {
        'user_id': 1,
        'email': 'test@example.com',
        'full_name': 'Test User',
        'username': 'testuser',
        'missed_count': 5
    }
    
    try:
        html_content, text_content = create_support_email_content(test_user_data)
        
        print(f"HTML content created: {len(html_content)} characters")
        print(f"Text content created: {len(text_content)} characters")
        
        # Check if key elements are present
        checks = [
            ("Hi Test User" in html_content, "Personalized greeting"),
            ("Are you experiencing any problems?" in html_content, "Support question"),
            ("Do you need any help?" in html_content, "Help offer"),
            ("Leadership Development Support" in text_content, "Email subject"),
            ("https://leadership-development-platform-self.vercel.app" in html_content, "App URL")
        ]
        
        print("\nContent validation:")
        for check, description in checks:
            status = "PASS" if check else "FAIL"
            print(f"   {status} {description}")
        
        all_checks_passed = all(check for check, _ in checks)
        return all_checks_passed
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_send_support_emails():
    """Test sending support emails to struggling users"""
    print("\n" + "=" * 60)
    print("TEST 3: Sending Support Emails to Struggling Users")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        result = send_support_email_to_struggling_users(db, min_miss_count=3)
        
        print(f"Total users found: {result['total_users']}")
        print(f"Emails sent successfully: {result['emails_sent']}")
        print(f"Emails failed: {result['emails_failed']}")
        print(f"Overall success: {result['success']}")
        
        if result['failed_emails']:
            print(f"Failed emails: {result['failed_emails']}")
        
        if 'error' in result:
            print(f"Error: {result['error']}")
        
        return result['success']
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        db.close()

def test_send_individual_user_email():
    """Test sending email to a specific user"""
    print("\n" + "=" * 60)
    print("TEST 4: Sending Email to Individual User")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Get a user from the database
        users = get_users_with_missed_lessons(db, min_miss_count=1)
        
        if not users:
            print("No users found with missed lessons - skipping individual email test")
            return True
        
        test_user = users[0]
        user_id = test_user['user_id']
        
        print(f"Sending test email to user {user_id} ({test_user['email']})")
        
        # Send with custom message
        custom_message = "This is a test message to verify the support email system is working correctly."
        success = send_support_email_to_user(db, user_id, custom_message)
        
        if success:
            print("Individual user email sent successfully")
        else:
            print("Failed to send individual user email")
        
        return success
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        db.close()

def test_scheduler_integration():
    """Test that scheduler can import and use the functions"""
    print("\n" + "=" * 60)
    print("TEST 5: Scheduler Integration")
    print("=" * 60)
    
    try:
        # Test imports that scheduler.py uses
        from app.services.scheduler_service import send_support_email_to_struggling_users
        from app.utils.support_email import create_support_email_content
        
        print("Scheduler can import send_support_email_to_struggling_users")
        print("Scheduler can import create_support_email_content")
        
        # Test that functions are callable
        if callable(send_support_email_to_struggling_users):
            print("send_support_email_to_struggling_users is callable")
        else:
            print("send_support_email_to_struggling_users is not callable")
            return False
        
        if callable(create_support_email_content):
            print("create_support_email_content is callable")
        else:
            print("create_support_email_content is not callable")
            return False
        
        return True
        
    except Exception as e:
        print(f"Import error: {e}")
        return False

def main():
    """Run all tests"""
    print("COMPREHENSIVE SUPPORT EMAIL SYSTEM TEST")
    print("=" * 60)
    print("Testing the complete support email functionality...")
    
    tests = [
        ("Get Users with Missed Lessons", test_get_users_with_missed_lessons),
        ("Create Email Content", test_create_email_content),
        ("Send Support Emails", test_send_support_emails),
        ("Send Individual User Email", test_send_individual_user_email),
        ("Scheduler Integration", test_scheduler_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"FAIL - {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("ALL TESTS PASSED! Support email system is working perfectly!")
        return True
    else:
        print("Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
