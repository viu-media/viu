# pyright: reportAttributeAccessIssue=false, reportPossiblyUnboundVariable=false
"""
HTML parsing utilities with optional lxml support.

This module provides comprehensive HTML parsing capabilities using either
Python's built-in html.parser or lxml for better performance when available.
"""

# TODO: Review and optimize the HTML parsing logic for better performance and flexibility.
#       Consider adding more utility functions for common HTML manipulation tasks.
import logging
import re
from html.parser import HTMLParser as BaseHTMLParser
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

if TYPE_CHECKING:
    from lxml import etree

logger = logging.getLogger(__name__)

# Try to import lxml
HAS_LXML = False
try:
    from lxml import etree, html as lxml_html

    HAS_LXML = True
    logger.debug("lxml is available and will be used for HTML parsing")
except ImportError:
    logger.debug("lxml not available, falling back to html.parser")


class HTMLParserConfig:
    """Configuration for HTML parser selection."""

    def __init__(self, use_lxml: Optional[bool] = None):
        """
        Initialize parser configuration.

        Args:
            use_lxml: Force use of lxml (True), html.parser (False), or auto-detect (None)
        """
        if use_lxml is None:
            self.use_lxml = HAS_LXML
        else:
            self.use_lxml = use_lxml and HAS_LXML

        if use_lxml and not HAS_LXML:
            logger.warning(
                "lxml requested but not available, falling back to html.parser"
            )


class HTMLParser:
    """
    Comprehensive HTML parser with optional lxml support.

    Provides a unified interface for HTML parsing operations regardless
    of the underlying parser implementation.
    """

    def __init__(self, config: Optional[HTMLParserConfig] = None):
        """Initialize the HTML parser with configuration."""
        self.config = config or HTMLParserConfig()

    def parse(self, html_content: str) -> Union[Any, "ParsedHTML"]:
        """
        Parse HTML content and return a parsed tree.

        Args:
            html_content: Raw HTML string to parse

        Returns:
            Parsed HTML tree (lxml Element or custom ParsedHTML object)
        """
        if self.config.use_lxml:
            return self._parse_with_lxml(html_content)
        else:
            return self._parse_with_builtin(html_content)

    def _parse_with_lxml(self, html_content: str) -> Any:
        """Parse HTML using lxml."""
        try:
            # Use lxml's HTML parser which is more lenient
            return lxml_html.fromstring(html_content)
        except Exception as e:
            logger.warning(f"lxml parsing failed: {e}, falling back to html.parser")
            return self._parse_with_builtin(html_content)

    def _parse_with_builtin(self, html_content: str) -> "ParsedHTML":
        """Parse HTML using Python's built-in parser."""
        parser = BuiltinHTMLParser()
        parser.feed(html_content)
        return ParsedHTML(parser.elements, html_content)


class BuiltinHTMLParser(BaseHTMLParser):
    """Enhanced HTML parser using Python's built-in capabilities."""

    def __init__(self):
        super().__init__()
        self.elements = []
        self.current_element = None
        self.element_stack = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]):
        """Handle opening tags."""
        element = {
            "tag": tag,
            "attrs": dict(attrs),
            "text": "",
            "children": [],
            "start_pos": self.getpos(),
        }

        if self.element_stack:
            self.element_stack[-1]["children"].append(element)
        else:
            self.elements.append(element)

        self.element_stack.append(element)

    def handle_endtag(self, tag: str):
        """Handle closing tags."""
        if self.element_stack and self.element_stack[-1]["tag"] == tag:
            element = self.element_stack.pop()
            element["end_pos"] = self.getpos()

    def handle_data(self, data: str):
        """Handle text content."""
        if self.element_stack:
            self.element_stack[-1]["text"] += data


class ParsedHTML:
    """Wrapper for parsed HTML using built-in parser."""

    def __init__(self, elements: List[Dict], raw_html: str):
        self.elements = elements
        self.raw_html = raw_html

    def find_by_id(self, element_id: str) -> Optional[Dict]:
        """Find element by ID."""
        return self._find_recursive(
            self.elements, lambda el: el["attrs"].get("id") == element_id
        )

    def find_by_class(self, class_name: str) -> List[Dict]:
        """Find elements by class name."""
        results = []
        self._find_all_recursive(
            self.elements,
            lambda el: class_name in el["attrs"].get("class", "").split(),
            results,
        )
        return results

    def find_by_tag(self, tag_name: str) -> List[Dict]:
        """Find elements by tag name."""
        results = []
        self._find_all_recursive(
            self.elements, lambda el: el["tag"].lower() == tag_name.lower(), results
        )
        return results

    def _find_recursive(self, elements: List[Dict], condition) -> Optional[Dict]:
        """Recursively find first element matching condition."""
        for element in elements:
            if condition(element):
                return element
            result = self._find_recursive(element["children"], condition)
            if result:
                return result
        return None

    def _find_all_recursive(self, elements: List[Dict], condition, results: List[Dict]):
        """Recursively find all elements matching condition."""
        for element in elements:
            if condition(element):
                results.append(element)
            self._find_all_recursive(element["children"], condition, results)


# Global parser instance
_default_parser = HTMLParser()


def extract_attributes(html_element: str) -> Dict[str, str]:
    """
    Extract attributes from an HTML element string.

    Args:
        html_element: HTML element as string (e.g., '<div class="test" id="main">')

    Returns:
        Dictionary of attribute name-value pairs

    Examples:
        >>> extract_attributes('<div class="test" id="main">')
        {'class': 'test', 'id': 'main'}
    """
    if not html_element:
        return {}

    # Use regex to extract attributes from HTML string
    attr_pattern = r'(\w+)=(["\'])([^"\']*?)\2'
    matches = re.findall(attr_pattern, html_element)

    attributes = {}
    for match in matches:
        attr_name, _, attr_value = match
        attributes[attr_name] = attr_value

    # Handle attributes without quotes
    unquoted_pattern = r"(\w+)=([^\s>]+)"
    unquoted_matches = re.findall(unquoted_pattern, html_element)
    for attr_name, attr_value in unquoted_matches:
        if attr_name not in attributes:
            attributes[attr_name] = attr_value

    return attributes


def get_element_by_id(element_id: str, html_content: str) -> Optional[str]:
    """
    Get HTML element by ID.

    Args:
        element_id: The ID attribute value to search for
        html_content: HTML content to search in

    Returns:
        HTML string of the element or None if not found

    Examples:
        >>> html = '<div id="test">Content</div>'
        >>> get_element_by_id("test", html)
        '<div id="test">Content</div>'
    """
    parsed = _default_parser.parse(html_content)

    if _default_parser.config.use_lxml and HAS_LXML:
        try:
            element = parsed.xpath(f'//*[@id="{element_id}"]')
            if element:
                return etree.tostring(element[0], encoding="unicode", method="html")
        except Exception as e:
            logger.warning(f"lxml XPath search failed: {e}")
            return None
    else:
        element = parsed.find_by_id(element_id)
        if element:
            return _element_to_html(element, html_content)

    return None


def get_element_by_tag(tag_name: str, html_content: str) -> Optional[str]:
    """
    Get first HTML element by tag name.

    Args:
        tag_name: The tag name to search for
        html_content: HTML content to search in

    Returns:
        HTML string of the element or None if not found
    """
    parsed = _default_parser.parse(html_content)

    if _default_parser.config.use_lxml and HAS_LXML:
        try:
            elements = parsed.xpath(f"//{tag_name}")
            if elements:
                return etree.tostring(elements[0], encoding="unicode", method="html")
        except Exception as e:
            logger.warning(f"lxml XPath search failed: {e}")
            return None
    else:
        elements = parsed.find_by_tag(tag_name)
        if elements:
            return _element_to_html(elements[0], html_content)

    return None


def get_element_by_class(class_name: str, html_content: str) -> Optional[str]:
    """
    Get first HTML element by class name.

    Args:
        class_name: The class name to search for
        html_content: HTML content to search in

    Returns:
        HTML string of the element or None if not found
    """
    parsed = _default_parser.parse(html_content)

    if _default_parser.config.use_lxml and HAS_LXML:
        try:
            elements = parsed.xpath(f'//*[contains(@class, "{class_name}")]')
            if elements:
                return etree.tostring(elements[0], encoding="unicode", method="html")
        except Exception as e:
            logger.warning(f"lxml XPath search failed: {e}")
            return None
    else:
        elements = parsed.find_by_class(class_name)
        if elements:
            return _element_to_html(elements[0], html_content)

    return None


def get_elements_by_tag(tag_name: str, html_content: str) -> List[str]:
    """
    Get all HTML elements by tag name.

    Args:
        tag_name: The tag name to search for
        html_content: HTML content to search in

    Returns:
        List of HTML strings for matching elements
    """
    parsed = _default_parser.parse(html_content)
    results = []

    if _default_parser.config.use_lxml and HAS_LXML:
        try:
            elements = parsed.xpath(f"//{tag_name}")
            for element in elements:
                results.append(
                    etree.tostring(element, encoding="unicode", method="html")
                )
        except Exception as e:
            logger.warning(f"lxml XPath search failed: {e}")
    else:
        elements = parsed.find_by_tag(tag_name)
        for element in elements:
            results.append(_element_to_html(element, html_content))

    return results


def get_elements_by_class(class_name: str, html_content: str) -> List[str]:
    """
    Get all HTML elements by class name.

    Args:
        class_name: The class name to search for
        html_content: HTML content to search in

    Returns:
        List of HTML strings for matching elements
    """
    parsed = _default_parser.parse(html_content)
    results = []

    if _default_parser.config.use_lxml and HAS_LXML:
        try:
            elements = parsed.xpath(f'//*[contains(@class, "{class_name}")]')
            for element in elements:
                results.append(
                    etree.tostring(element, encoding="unicode", method="html")
                )
        except Exception as e:
            logger.warning(f"lxml XPath search failed: {e}")
    else:
        elements = parsed.find_by_class(class_name)
        for element in elements:
            results.append(_element_to_html(element, html_content))

    return results


def get_elements_html_by_class(class_name: str, html_content: str) -> List[str]:
    """
    Get HTML strings of elements by class name.

    This is an alias for get_elements_by_class for yt-dlp compatibility.

    Args:
        class_name: The class name to search for
        html_content: HTML content to search in

    Returns:
        List of HTML strings for matching elements
    """
    return get_elements_by_class(class_name, html_content)


def get_element_text_and_html_by_tag(
    tag_name: str, html_content: str
) -> Tuple[Optional[str], Optional[str]]:
    """
    Get both text content and HTML of first element by tag name.

    Args:
        tag_name: The tag name to search for
        html_content: HTML content to search in

    Returns:
        Tuple of (text_content, html_string) or (None, None) if not found

    Examples:
        >>> html = '<script>alert("test");</script>'
        >>> get_element_text_and_html_by_tag("script", html)
        ('alert("test");', '<script>alert("test");</script>')
    """
    parsed = _default_parser.parse(html_content)

    if _default_parser.config.use_lxml and HAS_LXML:
        try:
            elements = parsed.xpath(f"//{tag_name}")
            if elements:
                element = elements[0]
                text = (
                    element.text_content()
                    if hasattr(element, "text_content")
                    else (element.text or "")
                )
                html_str = etree.tostring(element, encoding="unicode", method="html")
                return text, html_str
        except Exception as e:
            logger.warning(f"lxml XPath search failed: {e}")
            return None, None
    else:
        elements = parsed.find_by_tag(tag_name)
        if elements:
            element = elements[0]
            text = _extract_text_content(element)
            html_str = _element_to_html(element, html_content)
            return text, html_str

    return None, None


def _element_to_html(element: Dict, original_html: str) -> str:
    """
    Convert parsed element back to HTML string.

    This is a simplified implementation that reconstructs HTML from parsed data.
    For production use, consider using lxml for better accuracy.
    """
    if not element:
        return ""

    # Build opening tag
    tag = element["tag"]
    attrs = element.get("attrs", {})
    attr_str = " ".join(f'{k}="{v}"' for k, v in attrs.items() if v is not None)

    if attr_str:
        opening_tag = f"<{tag} {attr_str}>"
    else:
        opening_tag = f"<{tag}>"

    # Add text content
    text = element.get("text", "")

    # Add children
    children_html = ""
    for child in element.get("children", []):
        children_html += _element_to_html(child, original_html)

    # Build closing tag
    closing_tag = f"</{tag}>"

    return f"{opening_tag}{text}{children_html}{closing_tag}"


def _extract_text_content(element: Dict) -> str:
    """Extract all text content from element and its children."""
    text = element.get("text", "")

    for child in element.get("children", []):
        text += _extract_text_content(child)

    return text


def configure_parser(use_lxml: Optional[bool] = None) -> None:
    """
    Configure the global HTML parser.

    Args:
        use_lxml: Force use of lxml (True), html.parser (False), or auto-detect (None)
    """
    global _default_parser
    _default_parser = HTMLParser(HTMLParserConfig(use_lxml))
    logger.info(
        f"HTML parser configured: {'lxml' if _default_parser.config.use_lxml else 'html.parser'}"
    )
