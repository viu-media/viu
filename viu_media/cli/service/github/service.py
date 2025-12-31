"""
GitHub Contribution Service

Provides functionality to submit normalizer mappings to the viu repository
via Pull Request, using either browser-based OAuth or the GitHub CLI (gh).
"""

import base64
import json
import logging
import shutil
import subprocess
import time
import webbrowser
from typing import TYPE_CHECKING, Optional

import httpx

from ....core.constants import APP_DATA_DIR, AUTHOR, CLI_NAME
from ....core.utils.file import AtomicWriter, FileLock
from ....core.utils.normalizer import USER_NORMALIZER_JSON
from .model import (
    AuthMethod,
    GitHubAuth,
    GitHubContribution,
    GitHubFileContent,
    GitHubPRResponse,
    GitHubRepo,
    GitHubUser,
)

if TYPE_CHECKING:
    from ....libs.selectors.base import BaseSelector
    from ...service.feedback import FeedbackService

logger = logging.getLogger(__name__)

# GitHub OAuth configuration
GITHUB_CLIENT_ID = "Iv23liXUYWot4d4Zvjxa"  # Register your OAuth app on GitHub
GITHUB_OAUTH_SCOPES = "public_repo"
GITHUB_API_BASE = "https://api.github.com"

# Repository information
REPO_OWNER = AUTHOR
REPO_NAME = "viu"  # Must match GitHub repo name exactly (case-sensitive)
NORMALIZER_FILE_PATH = "viu_media/assets/normalizer.json"

AUTH_FILE = APP_DATA_DIR / "github_auth.json"


class GitHubContributionService:
    """Service for submitting normalizer mappings to GitHub."""

    def __init__(
        self,
        selector: "BaseSelector",
        feedback: Optional["FeedbackService"] = None,
    ):
        self.selector = selector
        self.feedback = feedback
        self._lock = FileLock(APP_DATA_DIR / "github_auth.lock")
        self._http_client = httpx.Client(
            headers={
                "Accept": "application/json",
                "User-Agent": f"{CLI_NAME}/1.0",
            },
            timeout=30.0,
            follow_redirects=True,  # Follow redirects for all request types
        )

    def __del__(self):
        """Cleanup HTTP client."""
        if hasattr(self, "_http_client"):
            self._http_client.close()

    def is_gh_cli_available(self) -> bool:
        """Check if GitHub CLI (gh) is installed and available."""
        return shutil.which("gh") is not None

    def is_gh_cli_authenticated(self) -> bool:
        """Check if GitHub CLI is authenticated."""
        if not self.is_gh_cli_available():
            return False
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, OSError):
            return False

    def get_available_auth_methods(self) -> list[AuthMethod]:
        """Get list of available authentication methods."""
        methods = [AuthMethod.BROWSER]
        if self.is_gh_cli_available():
            methods.insert(0, AuthMethod.GH_CLI)  # Prefer gh CLI if available
        return methods

    def prompt_auth_method(self) -> Optional[AuthMethod]:
        """
        Prompt user to select their preferred authentication method.

        Returns:
            Selected AuthMethod or None if cancelled.
        """
        methods = self.get_available_auth_methods()

        choices = []
        for method in methods:
            if method == AuthMethod.GH_CLI:
                status = "✓ authenticated" if self.is_gh_cli_authenticated() else ""
                choices.append(f"gh CLI {status}".strip())
            else:
                choices.append("Browser (OAuth)")

        choices.append("Cancel")

        choice = self.selector.choose(
            prompt="Select GitHub authentication method",
            choices=choices,
        )

        if not choice or choice == "Cancel":
            return None

        if choice.startswith("gh CLI"):
            return AuthMethod.GH_CLI
        return AuthMethod.BROWSER

    def submit_contribution(
        self,
        contribution: GitHubContribution,
        auth_method: Optional[AuthMethod] = None,
    ) -> Optional[str]:
        """
        Submit a normalizer mapping contribution to GitHub as a Pull Request.

        This will:
        1. Fork the repository (if not already forked)
        2. Create a new branch with the updated normalizer.json
        3. Open a Pull Request to the upstream repository

        Args:
            contribution: The mapping contribution to submit.
            auth_method: The authentication method to use. If None, will prompt.

        Returns:
            URL of the created PR, or None if failed.
        """
        if auth_method is None:
            auth_method = self.prompt_auth_method()
            if auth_method is None:
                return None

        if auth_method == AuthMethod.GH_CLI:
            return self._submit_pr_via_gh_cli(contribution)
        else:
            return self._submit_pr_via_api(contribution)

    def _get_user_normalizer_content(self) -> Optional[dict]:
        """Read the user's local normalizer.json file."""
        if not USER_NORMALIZER_JSON.exists():
            self._log_error(
                f"Local normalizer.json not found at {USER_NORMALIZER_JSON}"
            )
            return None

        try:
            with USER_NORMALIZER_JSON.open("r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            self._log_error(f"Failed to read normalizer.json: {e}")
            return None

    def _submit_pr_via_gh_cli(
        self, contribution: GitHubContribution
    ) -> Optional[str]:
        """Submit PR using GitHub CLI."""
        if not self.is_gh_cli_available():
            self._log_error("GitHub CLI (gh) is not installed")
            return None

        if not self.is_gh_cli_authenticated():
            self._log_info("GitHub CLI not authenticated. Running 'gh auth login'...")
            try:
                subprocess.run(["gh", "auth", "login"], check=True)
            except subprocess.SubprocessError:
                self._log_error("Failed to authenticate with GitHub CLI")
                return None

        # Read local normalizer content
        normalizer_content = self._get_user_normalizer_content()
        if not normalizer_content:
            return None

        # Get current username
        try:
            result = subprocess.run(
                ["gh", "api", "user", "--jq", ".login"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                self._log_error("Failed to get GitHub username")
                return None
            username = result.stdout.strip()
        except subprocess.SubprocessError as e:
            self._log_error(f"Failed to get username: {e}")
            return None

        # Fork the repository if not already forked
        self._log_info("Ensuring fork exists...")
        try:
            subprocess.run(
                ["gh", "repo", "fork", f"{REPO_OWNER}/{REPO_NAME}", "--clone=false"],
                capture_output=True,
                text=True,
                timeout=60,
            )
        except subprocess.SubprocessError:
            pass  # Fork may already exist, continue

        # Create branch name
        branch_name = f"normalizer/{contribution.provider_name}-{int(time.time())}"

        # Create the PR using gh pr create with the file content
        title = self._format_pr_title(contribution)
        body = self._format_pr_body(contribution)

        # We need to create the branch and commit via API since gh doesn't support this directly
        # Fall back to API method for the actual PR creation
        self._log_info("Creating pull request...")

        # Get token from gh CLI
        try:
            result = subprocess.run(
                ["gh", "auth", "token"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                self._log_error("Failed to get auth token from gh CLI")
                return None
            token = result.stdout.strip()
        except subprocess.SubprocessError as e:
            self._log_error(f"Failed to get token: {e}")
            return None

        return self._create_pr_via_api(contribution, token, normalizer_content)

    def _submit_pr_via_api(self, contribution: GitHubContribution) -> Optional[str]:
        """Submit PR using browser-based OAuth and GitHub API."""
        # Authenticate
        auth = self._load_cached_auth()

        if not auth or not self._validate_token(auth.access_token):
            auth = self._perform_device_flow_auth()
            if not auth:
                self._log_error("Failed to authenticate with GitHub")
                return None
            self._save_auth(auth)

        # Read local normalizer content
        normalizer_content = self._get_user_normalizer_content()
        if not normalizer_content:
            return None

        return self._create_pr_via_api(contribution, auth.access_token, normalizer_content)

    def _create_pr_via_api(
        self,
        contribution: GitHubContribution,
        token: str,
        normalizer_content: dict,
    ) -> Optional[str]:
        """Create a Pull Request via GitHub API."""
        headers = {"Authorization": f"Bearer {token}"}

        # Step 1: Get current user
        self._log_info("Getting user info...")
        try:
            response = self._http_client.get(
                f"{GITHUB_API_BASE}/user", headers=headers
            )
            response.raise_for_status()
            user = GitHubUser.model_validate(response.json())
        except httpx.HTTPError as e:
            self._log_error(f"Failed to get user info: {e}")
            return None

        # Step 2: Fork the repository (if not already forked)
        self._log_info("Ensuring fork exists...")
        fork_exists = False
        fork_full_name = ""

        try:
            # Check if fork exists by listing user's forks of the repo
            response = self._http_client.get(
                f"{GITHUB_API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/forks",
                headers=headers,
            )
            response.raise_for_status()
            forks = response.json()
            
            # Find user's fork
            user_fork = next(
                (f for f in forks if f["owner"]["login"].lower() == user.login.lower()),
                None
            )
            
            if user_fork:
                fork_full_name = user_fork["full_name"]
                fork_exists = True
            else:
                # Create fork
                self._log_info("Creating fork...")
                response = self._http_client.post(
                    f"{GITHUB_API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/forks",
                    headers=headers,
                )
                response.raise_for_status()
                fork_data = response.json()
                fork_full_name = fork_data["full_name"]
                # Wait for fork to be ready
                time.sleep(5)
        except httpx.HTTPError as e:
            self._log_error(f"Failed to create/check fork: {e}")
            return None

        self._log_info(f"Using fork: {fork_full_name}")

        # Step 3: Get the default branch SHA from upstream
        self._log_info("Getting upstream branch info...")
        try:
            response = self._http_client.get(
                f"{GITHUB_API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/git/ref/heads/master",
                headers=headers,
            )
            response.raise_for_status()
            base_sha = response.json()["object"]["sha"]
        except httpx.HTTPError as e:
            self._log_error(f"Failed to get base branch: {e}")
            return None

        # Step 3.5: Sync fork with upstream if it already existed
        if fork_exists:
            self._log_info("Syncing fork with upstream...")
            try:
                response = self._http_client.post(
                    f"{GITHUB_API_BASE}/repos/{fork_full_name}/merge-upstream",
                    headers=headers,
                    json={"branch": "master"},
                )
                # 409 means already up to date, which is fine
                if response.status_code not in (200, 409):
                    response.raise_for_status()
            except httpx.HTTPError as e:
                self._log_info(f"Could not sync fork (continuing anyway): {e}")

        # Step 4: Create a new branch in the fork
        branch_name = f"normalizer/{contribution.provider_name}-{int(time.time())}"
        self._log_info(f"Creating branch: {branch_name}")

        try:
            response = self._http_client.post(
                f"{GITHUB_API_BASE}/repos/{fork_full_name}/git/refs",
                headers=headers,
                json={"ref": f"refs/heads/{branch_name}", "sha": base_sha},
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_detail = str(e.response.json())
            except Exception:
                pass
            self._log_error(f"Failed to create branch: {e} {error_detail}")
            return None
        except httpx.HTTPError as e:
            self._log_error(f"Failed to create branch: {e}")
            return None

        # Step 5: Get current normalizer.json from the fork's new branch to get SHA
        self._log_info("Fetching current normalizer.json...")
        try:
            response = self._http_client.get(
                f"{GITHUB_API_BASE}/repos/{fork_full_name}/contents/{NORMALIZER_FILE_PATH}",
                headers=headers,
                params={"ref": branch_name},
            )
            response.raise_for_status()
            file_info = GitHubFileContent.model_validate(response.json())
            file_sha = file_info.sha

            # Decode existing content and merge with user's mappings
            existing_content = json.loads(
                base64.b64decode(file_info.content).decode("utf-8")
            )

            # Merge: user's normalizer takes precedence
            merged_content = existing_content.copy()
            for provider, mappings in normalizer_content.items():
                if provider not in merged_content:
                    merged_content[provider] = {}
                merged_content[provider].update(mappings)

        except httpx.HTTPError as e:
            self._log_error(f"Failed to get normalizer.json: {e}")
            return None

        # Step 6: Update the file in the fork
        self._log_info("Committing changes...")
        new_content = json.dumps(merged_content, indent=2, ensure_ascii=False)
        encoded_content = base64.b64encode(new_content.encode("utf-8")).decode("utf-8")

        commit_message = (
            f"feat(normalizer): add mapping for '{contribution.provider_title}'\n\n"
            f"Provider: {contribution.provider_name}\n"
            f"Maps: {contribution.provider_title} -> {contribution.media_api_title}"
        )

        try:
            response = self._http_client.put(
                f"{GITHUB_API_BASE}/repos/{fork_full_name}/contents/{NORMALIZER_FILE_PATH}",
                headers=headers,
                json={
                    "message": commit_message,
                    "content": encoded_content,
                    "sha": file_sha,
                    "branch": branch_name,
                },
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_detail = str(e.response.json())
            except Exception:
                pass
            self._log_error(f"Failed to commit changes: {e} {error_detail}")
            return None
        except httpx.HTTPError as e:
            self._log_error(f"Failed to commit changes: {e}")
            return None

        # Step 7: Create the Pull Request
        self._log_info("Creating pull request...")
        title = self._format_pr_title(contribution)
        body = self._format_pr_body(contribution)

        try:
            response = self._http_client.post(
                f"{GITHUB_API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/pulls",
                headers=headers,
                json={
                    "title": title,
                    "body": body,
                    "head": f"{user.login}:{branch_name}",
                    "base": "master",
                },
            )
            response.raise_for_status()
            pr = GitHubPRResponse.model_validate(response.json())
            self._log_success(f"Created PR #{pr.number}: {pr.html_url}")
            return pr.html_url

        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_json = e.response.json()
                error_detail = error_json.get("message", "")
                # GitHub includes detailed errors in 'errors' array
                if "errors" in error_json:
                    errors = error_json["errors"]
                    error_detail += " | " + str(errors)
            except Exception:
                pass
            self._log_error(f"Failed to create PR: {e} {error_detail}")
            return None
        except httpx.HTTPError as e:
            self._log_error(f"Failed to create PR: {e}")
            return None

    def _format_pr_title(self, contribution: GitHubContribution) -> str:
        """Format the PR title."""
        return (
            f"feat(normalizer): add mapping for '{contribution.provider_title}' "
            f"({contribution.provider_name})"
        )

    def _format_pr_body(self, contribution: GitHubContribution) -> str:
        """Format the PR body."""
        return f"""## Normalizer Mapping Contribution

This PR adds a new title mapping to the normalizer.

### Mapping Details

| Field | Value |
|-------|-------|
| **Provider** | `{contribution.provider_name}` |
| **Provider Title** | `{contribution.provider_title}` |
| **Media API Title** | `{contribution.media_api_title}` |
| **AniList ID** | {contribution.anilist_id or 'N/A'} |

### Changes

This PR updates `{NORMALIZER_FILE_PATH}` with the following mapping:

```json
"{contribution.provider_title}": "{contribution.media_api_title.lower()}"
```

---
*Submitted automatically via {CLI_NAME} CLI*
"""

    def _perform_device_flow_auth(self) -> Optional[GitHubAuth]:
        """
        Perform GitHub Device Flow authentication.

        This is more reliable for CLI apps than the web redirect flow.
        """
        self._log_info("Starting GitHub authentication...")

        # Request device code
        try:
            response = self._http_client.post(
                "https://github.com/login/device/code",
                data={
                    "client_id": GITHUB_CLIENT_ID,
                    "scope": GITHUB_OAUTH_SCOPES,
                },
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            self._log_error(f"Failed to start authentication: {e}")
            return None

        device_code = data.get("device_code")
        user_code = data.get("user_code")
        verification_uri = data.get("verification_uri")
        expires_in = data.get("expires_in", 900)
        interval = data.get("interval", 5)

        if not all([device_code, user_code, verification_uri]):
            self._log_error("Invalid response from GitHub")
            return None

        # Show user the code and open browser
        self._log_info(f"\n🔑 Your code: {user_code}")
        self._log_info(f"Opening {verification_uri} in your browser...")
        self._log_info("Enter the code above to authenticate.\n")

        webbrowser.open(verification_uri)

        # Poll for token
        import time

        start_time = time.time()
        while time.time() - start_time < expires_in:
            time.sleep(interval)

            try:
                token_response = self._http_client.post(
                    "https://github.com/login/oauth/access_token",
                    data={
                        "client_id": GITHUB_CLIENT_ID,
                        "device_code": device_code,
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    },
                    headers={"Accept": "application/json"},
                )
                token_data = token_response.json()

                if "access_token" in token_data:
                    self._log_success("Authentication successful!")
                    return GitHubAuth(
                        access_token=token_data["access_token"],
                        token_type=token_data.get("token_type", "bearer"),
                        scope=token_data.get("scope", ""),
                    )

                error = token_data.get("error")
                if error == "authorization_pending":
                    continue
                elif error == "slow_down":
                    interval += 5
                elif error == "expired_token":
                    self._log_error("Authentication expired. Please try again.")
                    return None
                elif error == "access_denied":
                    self._log_error("Authentication denied by user.")
                    return None
                else:
                    self._log_error(f"Authentication error: {error}")
                    return None

            except httpx.HTTPError:
                continue

        self._log_error("Authentication timed out. Please try again.")
        return None

    def _validate_token(self, token: str) -> bool:
        """Check if a GitHub token is still valid."""
        try:
            response = self._http_client.get(
                f"{GITHUB_API_BASE}/user",
                headers={"Authorization": f"Bearer {token}"},
            )
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    def _load_cached_auth(self) -> Optional[GitHubAuth]:
        """Load cached GitHub authentication."""
        if not AUTH_FILE.exists():
            return None

        try:
            with AUTH_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
                return GitHubAuth.model_validate(data)
        except (json.JSONDecodeError, ValueError):
            return None

    def _save_auth(self, auth: GitHubAuth) -> None:
        """Save GitHub authentication to cache."""
        APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with AtomicWriter(AUTH_FILE) as f:
                json.dump(auth.model_dump(), f, indent=2)

    def clear_cached_auth(self) -> None:
        """Clear cached GitHub authentication."""
        if AUTH_FILE.exists():
            AUTH_FILE.unlink()
            logger.info("Cleared GitHub authentication cache")

    def _log_info(self, message: str) -> None:
        """Log info message."""
        if self.feedback:
            self.feedback.info(message)
        else:
            logger.info(message)

    def _log_success(self, message: str) -> None:
        """Log success message."""
        if self.feedback:
            self.feedback.success(message)
        else:
            logger.info(message)

    def _log_error(self, message: str) -> None:
        """Log error message."""
        if self.feedback:
            self.feedback.error(message)
        else:
            logger.error(message)
