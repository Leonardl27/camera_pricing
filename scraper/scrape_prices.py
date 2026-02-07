#!/usr/bin/env python3
"""
Security Camera Price Scraper

This script fetches prices from configured camera product pages and updates
the prices.json file used by the dashboard.

Usage:
    python scrape_prices.py

Configuration:
    Edit cameras.json to add/modify cameras to track.
    Each camera entry needs:
    - id: Unique identifier
    - name: Display name
    - model: Model number
    - category: wired, wireless, ptz, bullet, dome, nvr
    - url: Product page URL
    - retailer: Source name
    - price_selector: CSS selector for price element
    - enabled: true/false to enable/disable scraping
"""

import json
import re
import os
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup


# Configuration
SCRIPT_DIR = Path(__file__).parent
CAMERAS_CONFIG = SCRIPT_DIR / "cameras.json"
OUTPUT_FILE = SCRIPT_DIR.parent / "data" / "prices.json"

# Request settings
REQUEST_TIMEOUT = 30
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def load_camera_config():
    """Load camera configuration from JSON file."""
    with open(CAMERAS_CONFIG, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_price(price_text):
    """
    Extract numeric price from text.

    Examples:
        "$149.99" -> 149.99
        "USD 149.99" -> 149.99
        "149.99 USD" -> 149.99
        "$1,299.99" -> 1299.99
    """
    if not price_text:
        return None

    # Remove currency symbols, commas, and whitespace
    cleaned = re.sub(r'[^\d.]', '', price_text)

    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def fetch_price(url, price_selector):
    """
    Fetch price from a product page.

    Args:
        url: Product page URL
        price_selector: CSS selector for price element

    Returns:
        Price as float, or None if not found/failed
    """
    try:
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "lxml")
        price_element = soup.select_one(price_selector)

        if price_element:
            price_text = price_element.get_text(strip=True)
            return parse_price(price_text)

        # Try common fallback selectors
        fallback_selectors = [
            '[class*="price"]',
            '[id*="price"]',
            '.product-price',
            '.current-price',
            'span[itemprop="price"]',
            'meta[itemprop="price"]',
        ]

        for selector in fallback_selectors:
            element = soup.select_one(selector)
            if element:
                # Check for content attribute (meta tags)
                if element.get("content"):
                    return parse_price(element["content"])
                price = parse_price(element.get_text(strip=True))
                if price:
                    return price

        return None

    except requests.RequestException as e:
        print(f"  Error fetching {url}: {e}")
        return None
    except Exception as e:
        print(f"  Unexpected error for {url}: {e}")
        return None


def scrape_all_cameras(cameras_config):
    """
    Scrape prices for all enabled cameras.

    Args:
        cameras_config: Camera configuration dict

    Returns:
        List of camera dicts with updated prices
    """
    results = []

    for camera in cameras_config.get("cameras", []):
        if not camera.get("enabled", True):
            print(f"Skipping disabled camera: {camera['name']}")
            continue

        print(f"Fetching price for: {camera['name']}")

        price = fetch_price(camera["url"], camera.get("price_selector", ".price"))

        result = {
            "id": camera["id"],
            "name": camera["name"],
            "model": camera["model"],
            "category": camera["category"],
            "price": price,
            "retailer": camera.get("retailer", "Unknown"),
            "url": camera["url"],
            "description": camera.get("description", ""),
        }

        if price:
            print(f"  Found price: ${price:.2f}")
        else:
            print(f"  Price not found (will use existing if available)")

        results.append(result)

    return results


def load_existing_prices():
    """Load existing prices from output file."""
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"cameras": [], "last_updated": None}


def merge_prices(new_cameras, existing_data):
    """
    Merge new prices with existing data.
    Keeps existing price if new price couldn't be fetched.
    """
    existing_prices = {c["id"]: c.get("price") for c in existing_data.get("cameras", [])}

    for camera in new_cameras:
        if camera["price"] is None and camera["id"] in existing_prices:
            camera["price"] = existing_prices[camera["id"]]
            print(f"  Using existing price for {camera['name']}: ${camera['price']:.2f}" if camera['price'] else "")

    return new_cameras


def save_prices(cameras):
    """Save prices to output JSON file."""
    output = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "cameras": cameras
    }

    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved {len(cameras)} cameras to {OUTPUT_FILE}")


def main():
    """Main entry point."""
    print("=" * 50)
    print("Security Camera Price Scraper")
    print("=" * 50)
    print()

    # Load configuration
    print("Loading camera configuration...")
    config = load_camera_config()
    print(f"Found {len(config.get('cameras', []))} cameras configured\n")

    # Scrape prices
    print("Fetching prices...")
    print("-" * 50)
    cameras = scrape_all_cameras(config)

    # Merge with existing data (preserve prices that couldn't be fetched)
    print("\nMerging with existing data...")
    existing = load_existing_prices()
    cameras = merge_prices(cameras, existing)

    # Save results
    save_prices(cameras)

    # Summary
    prices_found = sum(1 for c in cameras if c["price"] is not None)
    print(f"\nSummary: {prices_found}/{len(cameras)} prices available")
    print("Done!")


if __name__ == "__main__":
    main()
