#!/usr/bin/env python3
"""
Test script for AI Dependency Update Agent API

This script demonstrates how to use the API.
"""

import requests
import time
import sys


BASE_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")

    if response.status_code == 200:
        print("✓ Health check passed")
        print(f"  Response: {response.json()}")
        return True
    else:
        print("✗ Health check failed")
        return False


def test_supported_package_managers():
    """Test supported package managers endpoint"""
    print("\nTesting supported package managers endpoint...")
    response = requests.get(f"{BASE_URL}/api/supported-package-managers")

    if response.status_code == 200:
        data = response.json()
        print("✓ Supported package managers retrieved")
        print(f"  Package managers: {', '.join(data['supported_package_managers'])}")
        return True
    else:
        print("✗ Failed to get supported package managers")
        return False


def test_update_job(repo_url):
    """Test creating and monitoring an update job"""
    print(f"\nTesting update job for repository: {repo_url}")

    # Create job
    print("Creating update job...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/update",
            json={
                "repository_url": repo_url,
                "create_pr": False  # Set to False for testing
            }
        )

        if response.status_code != 200:
            print(f"✗ Failed to create job: {response.text}")
            return False

        job = response.json()
        job_id = job["job_id"]
        print(f"✓ Job created: {job_id}")

    except Exception as e:
        print(f"✗ Error creating job: {e}")
        return False

    # Monitor job
    print("\nMonitoring job status...")
    max_attempts = 60  # 5 minutes max
    attempt = 0

    while attempt < max_attempts:
        try:
            response = requests.get(f"{BASE_URL}/api/jobs/{job_id}")

            if response.status_code != 200:
                print(f"✗ Failed to get job status: {response.text}")
                return False

            status = response.json()

            # Print latest log
            if status.get("logs"):
                print(f"  {status['logs'][-1]}")

            # Check if completed
            if status["status"] in ["completed", "failed"]:
                if status["status"] == "completed":
                    print("\n✓ Job completed successfully!")

                    if status.get("package_manager"):
                        print(f"  Package Manager: {status['package_manager']}")

                    if status.get("outdated_packages"):
                        print(f"  Outdated Packages: {len(status['outdated_packages'])}")
                        for pkg in status["outdated_packages"][:5]:
                            print(f"    - {pkg['name']}: {pkg['current_version']} → {pkg['latest_version']}")
                        if len(status["outdated_packages"]) > 5:
                            print(f"    ... and {len(status['outdated_packages']) - 5} more")

                    if status.get("pr_url"):
                        print(f"  PR URL: {status['pr_url']}")

                    return True
                else:
                    print(f"\n✗ Job failed: {status.get('error', 'Unknown error')}")
                    return False

            time.sleep(5)
            attempt += 1

        except Exception as e:
            print(f"✗ Error monitoring job: {e}")
            return False

    print("\n✗ Job timed out")
    return False


def main():
    """Main test function"""
    print("=" * 60)
    print("AI Dependency Update Agent - API Test")
    print("=" * 60)

    # Test health
    if not test_health():
        print("\n❌ Server is not running or not healthy")
        print("   Start the server with: python run.py")
        sys.exit(1)

    # Test supported package managers
    if not test_supported_package_managers():
        print("\n❌ Failed to get supported package managers")
        sys.exit(1)

    # Test update job (optional - requires repository URL)
    if len(sys.argv) > 1:
        repo_url = sys.argv[1]
        if test_update_job(repo_url):
            print("\n✅ All tests passed!")
        else:
            print("\n❌ Update job test failed")
            sys.exit(1)
    else:
        print("\n" + "=" * 60)
        print("Basic tests passed!")
        print("=" * 60)
        print("\nTo test the full workflow, run:")
        print("  python test_api.py https://github.com/owner/repo")
        print("\nNote: Make sure you have the required API keys configured")


if __name__ == "__main__":
    main()
