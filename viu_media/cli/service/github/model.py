from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AuthMethod(str, Enum):
    """Authentication method for GitHub API."""

    BROWSER = "browser"
    GH_CLI = "gh"


class GitHubAuth(BaseModel):
    """Stored GitHub authentication credentials."""

    access_token: str
    token_type: str = "bearer"
    scope: str = ""


class GitHubContribution(BaseModel):
    """Represents a normalizer mapping contribution."""

    provider_name: str = Field(..., description="The provider name (e.g., 'allanime')")
    provider_title: str = Field(
        ..., description="The title as it appears on the provider"
    )
    media_api_title: str = Field(..., description="The normalized media API title")
    anilist_id: Optional[int] = Field(
        default=None, description="Optional AniList ID for reference"
    )


class GitHubPRResponse(BaseModel):
    """Response from GitHub API when creating a pull request."""

    id: int
    number: int
    html_url: str
    title: str
    state: str


class GitHubUser(BaseModel):
    """GitHub user information."""

    login: str
    id: int


class GitHubRepo(BaseModel):
    """GitHub repository information."""

    full_name: str
    default_branch: str
    fork: bool = False


class GitHubFileContent(BaseModel):
    """GitHub file content response."""

    sha: str
    content: str
    encoding: str = "base64"

