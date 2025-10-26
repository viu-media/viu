from httpx import get

ANISKIP_ENDPOINT = "https://api.aniskip.com/v1/skip-times"


# TODO: Finish own implementation of aniskip script
class AniSkip:
    @classmethod
    def get_skip_times(
        cls, mal_id: int, episode_number: float | int, types=["op", "ed"]
    ):
        url = f"{ANISKIP_ENDPOINT}/{mal_id}/{episode_number}?types=op&types=ed"
        response = get(url)
        print(response.text)
        return response.json()


if __name__ == "__main__":
    mal_id = input("Mal id: ")
    episode_number = input("episode_number: ")
    skip_times = AniSkip.get_skip_times(int(mal_id), float(episode_number))
    print(skip_times)
