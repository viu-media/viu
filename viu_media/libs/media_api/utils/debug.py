from ..base import BaseApiClient
import logging

logger = logging.getLogger(__name__)


def test_media_api(api_client: BaseApiClient):
    """
    Test all abstract methods of the media API with user feedback.

    This function provides an interactive test suite that validates all the core
    functionality of the media API, similar to test_anime_provider for anime providers.

    Tests performed:
    1. Authentication status and user profile retrieval
    2. Media search functionality
    3. Anime recommendations fetching
    4. Related anime retrieval
    5. Character information fetching
    6. Airing schedule information
    7. User media list operations (if authenticated)
    8. List entry management (add/remove from user list)

    Args:
        api_client: An instance of AniListApi to test

    Usage:
        Run this module directly: python -m viu_media.libs.media_api.anilist.api
        Or import and call: test_media_api(AniListApi(config, client))
    """
    from ....core.constants import APP_ASCII_ART
    from ..params import (
        MediaRecommendationParams,
        MediaRelationsParams,
        MediaSearchParams,
        UpdateUserMediaListEntryParams,
        UserMediaListSearchParams,
    )
    from ..types import UserMediaListStatus

    print(APP_ASCII_ART)
    print("=== Media API Test Suite ===\n")

    # Test 1: Authentication
    print("1. Testing Authentication...")
    print(f"Authenticated: {api_client.is_authenticated()}")
    if api_client.is_authenticated():
        profile = api_client.get_viewer_profile()
        if profile:
            print(f"   User: {profile.name} (ID: {profile.id})")
        else:
            print("   Failed to get user profile")
    else:
        print("   Not authenticated - some features will be limited")
    print()

    # Test 2: Media Search
    print("2. Testing Media Search...")
    query = input("What anime would you like to search for: ")
    search_results = api_client.search_media(MediaSearchParams(query=query, per_page=5))

    if not search_results or not search_results.media:
        print("   No search results found")
        return

    print(f"   Found {len(search_results.media)} results:")
    for i, result in enumerate(search_results.media):
        title = result.title.english or result.title.romaji
        print(f"   {i + 1}: {title} ({result.episodes or '?'} episodes)")

    # Select an anime for further testing
    try:
        choice = (
            int(
                input(
                    f"\nSelect anime for detailed testing (1-{len(search_results.media)}): "
                )
            )
            - 1
        )
        selected_anime = search_results.media[choice]
    except (ValueError, IndexError):
        print("Invalid selection")
        return

    print(f"\nSelected: {selected_anime.title.english or selected_anime.title.romaji}")
    print()

    # Test 3: Get Recommendations
    print("3. Testing Recommendations...")
    try:
        recommendations = api_client.get_recommendation_for(
            MediaRecommendationParams(id=selected_anime.id, page=1, per_page=3)
        )
        if recommendations:
            print(f"   Found {len(recommendations)} recommendations:")
            for rec in recommendations[:3]:  # Show first 3
                title = rec.title.english or rec.title.romaji
                print(f"     - {title}")
        else:
            print("   No recommendations found")
    except Exception as e:
        print(f"   Error getting recommendations: {e}")
        logger.error(f"Recommendations error for anime {selected_anime.id}: {e}")
    print()

    # Test 4: Get Related Anime
    print("4. Testing Related Anime...")
    try:
        relations = api_client.get_related_anime_for(
            MediaRelationsParams(id=selected_anime.id)
        )
        if relations:
            print(f"   Found {len(relations)} related anime:")
            for rel in relations[:3]:  # Show first 3
                title = rel.title.english or rel.title.romaji
                print(f"     - {title}")
        else:
            print("   No related anime found")
    except Exception as e:
        print(f"   Error getting related anime: {e}")
        logger.error(f"Relations error for anime {selected_anime.id}: {e}")
    print()

    # Test 5: Get Characters
    # TODO: Recreate this test

    # Test 6: Get Airing Schedule
    # TODO: Recreate this test

    # Test 7: User Media List (if authenticated)
    if api_client.is_authenticated():
        print("7. Testing User Media List...")
        try:
            user_list = api_client.search_media_list(
                UserMediaListSearchParams(
                    status=UserMediaListStatus.WATCHING, page=1, per_page=3
                )
            )
            if user_list and user_list.media:
                print(f"   Found {len(user_list.media)} watching anime:")
                for anime in user_list.media:
                    title = anime.title.english or anime.title.romaji
                    progress = anime.user_status.progress if anime.user_status else 0
                    print(
                        f"     - {title} (Progress: {progress}/{anime.episodes or '?'})"
                    )
            else:
                print("   No anime in watching list")
        except Exception as e:
            print(f"   Error: {e}")
        print()

        # Test 8: Update List Entry
        print("8. Testing List Entry Management...")
        update_test = input(
            "Would you like to test adding the selected anime to your list? (y/n): "
        )
        if update_test.lower() == "y":
            try:
                success = api_client.update_list_entry(
                    UpdateUserMediaListEntryParams(
                        media_id=selected_anime.id, status=UserMediaListStatus.PLANNING
                    )
                )
                if success:
                    print("   ✓ Successfully added to planning list")

                    # Test delete
                    delete_test = input(
                        "   Would you like to remove it from your list? (y/n): "
                    )
                    if delete_test.lower() == "y":
                        delete_success = api_client.delete_list_entry(selected_anime.id)
                        if delete_success:
                            print("   ✓ Successfully removed from list")
                        else:
                            print("   ✗ Failed to remove from list")
                else:
                    print("   ✗ Failed to add to list")
            except Exception as e:
                print(f"   Error: {e}")
        print()
    else:
        print("7-8. Skipping user list tests (not authenticated)\n")

    print("=== Test Suite Complete ===")
    print("All basic API methods have been tested!")
