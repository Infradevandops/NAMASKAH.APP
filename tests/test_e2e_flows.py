#!/usr/bin/env python3
"""
End-to-End Tests for namaskah Workflows
Tests complete user journeys using Playwright for browser automation
Requires: pytest-playwright installed (pip install pytest-playwright)
Run with: pytest tests/test_e2e_flows.py --headed (for visual debugging)
"""
import os
import time

import pytest
from playwright.sync_api import sync_playwright


@pytest.fixture(scope="session")
def playwright_instance():
    """Create Playwright instance"""
    with sync_playwright() as p:
        yield p


@pytest.mark.asyncio
async def test_user_registration_to_verification(playwright_instance):
    """Test complete workflow: Register → Purchase Number → Create Verification"""
    browser = playwright_instance.chromium.launch(
        headless=False
    )  # Headed for debugging
    page = browser.new_page()

    # Step 1: Navigate to registration
    page.goto("http://localhost:8000/register")

    # Fill registration form
    page.fill('input[name="email"]', "testuser@example.com")
    page.fill('input[name="username"]', "e2e_test_user")
    page.fill('input[name="password"]', "TestPassword123!")
    page.fill('input[name="full_name"]', "E2E Test User")

    # Submit registration
    page.click('button[type="submit"]')

    # Wait for success and redirect to dashboard
    page.wait_for_selector(".alert-success", timeout=10000)
    assert page.is_visible(".alert-success")
    assert "registration successful" in page.inner_text(".alert-success")

    # Step 2: Purchase phone number
    page.goto("http://localhost:8000/phone-marketplace")
    page.wait_for_selector("#country-select", timeout=5000)

    # Select US and search
    page.select_option("#country-select", "US")
    page.fill("#area-code", "555")
    page.click("#search-numbers-btn")

    # Wait for results and select first
    page.wait_for_selector("#search-results .number-card", timeout=10000)
    first_number = page.query_selector("#search-results .number-card")
    first_number.click()

    # Complete purchase
    page.wait_for_selector("#purchase-details", timeout=5000)
    page.click("#confirm-purchase-btn")
    page.wait_for_selector(".alert-success", timeout=10000)
    assert "purchased" in page.inner_text(".alert-success")

    # Step 3: Create verification
    page.goto("http://localhost:8000/verifications")
    page.wait_for_selector('select[name="service_name"]', timeout=5000)

    # Select WhatsApp and create
    page.select_option('select[name="service_name"]', "whatsapp")
    page.click('button[type="submit"]')

    # Wait for verification creation
    page.wait_for_selector(".verification-card", timeout=10000)
    assert page.is_visible(".verification-card")

    browser.close()


@pytest.mark.asyncio
async def test_chat_conversation_flow(playwright_instance):
    """Test chat conversation flow with multiple users"""
    browser = playwright_instance.chromium.launch(headless=False)

    # User 1: Create conversation
    page1 = browser.new_page()
    page1.goto("http://localhost:8000/chat")

    # Wait for user list and create conversation
    page1.wait_for_selector(".user-list", timeout=5000)
    page1.click(".user-list .user-item")  # Select another user

    # Verify conversation opens
    page1.wait_for_selector(".conversation-panel", timeout=10000)

    # Send message
    page1.fill(".message-input", "Hello from E2E test!")
    page1.press(".message-input", "Enter")

    # Wait for message to appear
    page1.wait_for_selector(".message-content", timeout=5000)
    assert "Hello from E2E test!" in page1.inner_text(".message-content")

    # Verify typing indicator (simulate from another user - manual for now)
    # In full test, would need second browser instance

    browser.close()


@pytest.mark.asyncio
async def test_international_routing_optimization(playwright_instance):
    """Test international routing optimization workflow"""
    browser = playwright_instance.chromium.launch(headless=False)
    page = browser.new_page()

    # Navigate to international routing page
    page.goto("http://localhost:8000/international-routing")
    page.wait_for_selector(".routing-dashboard", timeout=10000)

    # Verify analytics display
    assert page.is_visible(".usage-chart")
    assert page.is_visible(".cost-optimization-panel")

    # Test routing optimization
    page.click("#optimize-routing-btn")
    page.wait_for_selector(".optimization-results", timeout=10000)

    # Verify recommendations
    recommendations = page.query_selector_all(".recommendation-card")
    assert len(recommendations) > 0, "No optimization recommendations found"

    # Check for country suggestions
    us_suggestion = page.query_selector('.recommendation-card:has-text("US")')
    assert us_suggestion is not None

    browser.close()


@pytest.mark.asyncio
async def test_error_handling_in_ui(playwright_instance):
    """Test UI error handling and recovery"""
    browser = playwright_instance.chromium.launch(headless=False)
    page = browser.new_page()

    # Navigate to a page that might fail
    page.goto("http://localhost:8000/phone-marketplace")

    # Simulate network error by blocking a resource
    # In real test, use page.route to mock failures
    page.route("**/api/**", lambda route: route.abort())

    # Trigger an action that calls API
    page.select_option("#country-select", "US")
    page.click("#search-numbers-btn")

    # Wait for error message
    page.wait_for_selector(".alert-danger", timeout=5000)
    error_msg = page.inner_text(".alert-danger")
    assert "failed" in error_msg.lower() or "error" in error_msg.lower()

    # Verify retry mechanism
    retry_btn = page.query_selector(".retry-button")
    assert retry_btn is not None
    assert retry_btn.is_enabled()

    browser.close()


@pytest.mark.asyncio
async def test_accessibility_in_chat(playwright_instance):
    """Test accessibility features in chat interface"""
    browser = playwright_instance.chromium.launch(headless=False)
    page = browser.new_page()

    page.goto("http://localhost:8000/chat")

    # Check ARIA labels and roles
    message_input = page.wait_for_selector(".message-input", timeout=5000)
    assert message_input.get_attribute("aria-label") == "Type your message"

    send_button = page.query_selector('button[aria-label="Send message"]')
    assert send_button is not None

    # Test keyboard navigation
    page.keyboard.press("Enter")  # Should focus on input if accessible

    # Verify screen reader compatibility (basic check)
    assert page.query_selector('main[role="main"]') is not None
    assert page.query_selector('nav[role="navigation"]') is not None

    browser.close()


# Run with: pytest tests/test_e2e_flows.py --headed -v
