"""
User agent utilities for web scraping.

Provides functionality to generate random user agent strings
to avoid detection and blocking by websites.
"""

import random
from typing import List, Optional


class UserAgentGenerator:
    """
    Generator for realistic user agent strings.

    Provides a variety of common user agents from different browsers
    and operating systems to help avoid detection.
    """

    # Common user agents for different browsers and OS combinations
    USER_AGENTS = [
        # Chrome on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        # Chrome on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        # Chrome on Linux
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        # Firefox on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
        # Firefox on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0",
        # Firefox on Linux
        "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
        # Safari on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        # Edge on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
        # Mobile Chrome (Android)
        "Mozilla/5.0 (Linux; Android 14; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
        # Mobile Safari (iOS)
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPad; CPU OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1",
    ]

    # Browser-specific user agents for when you need a specific browser
    CHROME_USER_AGENTS = [
        ua for ua in USER_AGENTS if "Chrome" in ua and "Edg" not in ua
    ]
    FIREFOX_USER_AGENTS = [ua for ua in USER_AGENTS if "Firefox" in ua]
    SAFARI_USER_AGENTS = [
        ua for ua in USER_AGENTS if "Safari" in ua and "Chrome" not in ua
    ]
    EDGE_USER_AGENTS = [ua for ua in USER_AGENTS if "Edg" in ua]

    # Platform-specific user agents
    WINDOWS_USER_AGENTS = [ua for ua in USER_AGENTS if "Windows NT" in ua]
    MACOS_USER_AGENTS = [ua for ua in USER_AGENTS if "Macintosh" in ua]
    LINUX_USER_AGENTS = [
        ua for ua in USER_AGENTS if "Linux" in ua and "Android" not in ua
    ]
    MOBILE_USER_AGENTS = [ua for ua in USER_AGENTS if "Mobile" in ua or "Android" in ua]

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the user agent generator.

        Args:
            seed: Random seed for reproducible results (optional)
        """
        if seed is not None:
            random.seed(seed)

    def random(self) -> str:
        """
        Get a random user agent string.

        Returns:
            Random user agent string
        """
        return random.choice(self.USER_AGENTS)

    def random_browser(self, browser: str) -> str:
        """
        Get a random user agent for a specific browser.

        Args:
            browser: Browser name ('chrome', 'firefox', 'safari', 'edge')

        Returns:
            Random user agent string for the specified browser

        Raises:
            ValueError: If browser is not supported
        """
        browser = browser.lower()
        if browser == "chrome":
            return random.choice(self.CHROME_USER_AGENTS)
        elif browser == "firefox":
            return random.choice(self.FIREFOX_USER_AGENTS)
        elif browser == "safari":
            return random.choice(self.SAFARI_USER_AGENTS)
        elif browser == "edge":
            return random.choice(self.EDGE_USER_AGENTS)
        else:
            raise ValueError(f"Unsupported browser: {browser}")

    def random_platform(self, platform: str) -> str:
        """
        Get a random user agent for a specific platform.

        Args:
            platform: Platform name ('windows', 'macos', 'linux', 'mobile')

        Returns:
            Random user agent string for the specified platform

        Raises:
            ValueError: If platform is not supported
        """
        platform = platform.lower()
        if platform == "windows":
            return random.choice(self.WINDOWS_USER_AGENTS)
        elif platform in ("macos", "mac"):
            return random.choice(self.MACOS_USER_AGENTS)
        elif platform == "linux":
            return random.choice(self.LINUX_USER_AGENTS)
        elif platform == "mobile":
            return random.choice(self.MOBILE_USER_AGENTS)
        else:
            raise ValueError(f"Unsupported platform: {platform}")

    def add_user_agent(self, user_agent: str) -> None:
        """
        Add a custom user agent to the list.

        Args:
            user_agent: Custom user agent string to add
        """
        if user_agent not in self.USER_AGENTS:
            self.USER_AGENTS.append(user_agent)

    def get_all(self) -> List[str]:
        """
        Get all available user agent strings.

        Returns:
            List of all user agent strings
        """
        return self.USER_AGENTS.copy()


# Global instance for convenience
_default_generator = UserAgentGenerator()


def random_user_agent() -> str:
    """
    Get a random user agent string using the default generator.

    Returns:
        Random user agent string

    Examples:
        >>> ua = random_user_agent()
        >>> "Mozilla" in ua
        True
    """
    return _default_generator.random()


def random_user_agent_browser(browser: str) -> str:
    """
    Get a random user agent for a specific browser.

    Args:
        browser: Browser name ('chrome', 'firefox', 'safari', 'edge')

    Returns:
        Random user agent string for the specified browser
    """
    return _default_generator.random_browser(browser)


def random_user_agent_platform(platform: str) -> str:
    """
    Get a random user agent for a specific platform.

    Args:
        platform: Platform name ('windows', 'macos', 'linux', 'mobile')

    Returns:
        Random user agent string for the specified platform
    """
    return _default_generator.random_platform(platform)


def set_user_agent_seed(seed: int) -> None:
    """
    Set the random seed for user agent generation.

    Args:
        seed: Random seed value
    """
    global _default_generator
    _default_generator = UserAgentGenerator(seed)


def add_custom_user_agent(user_agent: str) -> None:
    """
    Add a custom user agent to the default generator.

    Args:
        user_agent: Custom user agent string to add
    """
    _default_generator.add_user_agent(user_agent)


def get_all_user_agents() -> List[str]:
    """
    Get all available user agent strings from the default generator.

    Returns:
        List of all user agent strings
    """
    return _default_generator.get_all()
