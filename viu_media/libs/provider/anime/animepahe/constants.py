import re

ANIMEPAHE = "animepahe.si"
ANIMEPAHE_BASE = f"https://{ANIMEPAHE}"
ANIMEPAHE_ENDPOINT = f"{ANIMEPAHE_BASE}/api"
CDN_PROVIDER = "kwik.cx"
CDN_PROVIDER_BASE = f"https://{CDN_PROVIDER}"

SERVERS_AVAILABLE = ["kwik"]
REQUEST_HEADERS = {
    "Cookie": "__ddgid_=VvX0ebHrH2DsFZo4; __ddgmark_=3savRpSVFhvZcn5x; __ddg2_=buBJ3c4pNBYKFZNp; __ddg1_=rbVADKr9URtt55zoIGFa; SERVERID=janna; XSRF-TOKEN=eyJpdiI6IjV5bFNtd0phUHgvWGJxc25wL0VJSUE9PSIsInZhbHVlIjoicEJTZktlR2hxR2JZTWhnL0JzazlvZU5TQTR2bjBWZ2dDb0RwUXVUUWNSclhQWUhLRStYSmJmWmUxWkpiYkFRYU12RjFWejlSWHorME1wZG5qQ1U0TnFlNnBFR2laQjN1MjdyNjc5TjVPdXdJb2o5VkU1bEduRW9pRHNDTHh6Sy8iLCJtYWMiOiI0OTc0ZmNjY2UwMGJkOWY2MWNkM2NlMjk2ZGMyZGJmMWE0NTdjZTdkNGI2Y2IwNTIzZmFiZWU5ZTE2OTk0YmU4IiwidGFnIjoiIn0%3D; laravel_session=eyJpdiI6ImxvdlpqREFnTjdaeFJubUlXQWlJVWc9PSIsInZhbHVlIjoiQnE4R3VHdjZ4M1NDdEVWM1ZqMUxtNnVERnJCcmtCUHZKNzRPR2RFbzNFcStTL29xdnVTbWhsNVRBUXEybVZWNU1UYVlTazFqYlN5UjJva1k4czNGaXBTbkJJK01oTUd3VHRYVHBoc3dGUWxHYnFlS2NJVVNFbTFqMVBWdFpuVUgiLCJtYWMiOiI1NDdjZTVkYmNhNjUwZTMxZmRlZmVmMmRlMGNiYjAwYjlmYjFjY2U0MDc1YTQzZThiMTIxMjJlYTg1NTA4YjBmIiwidGFnIjoiIn0%3D; latest=5592",
    "Host": ANIMEPAHE,
    "Accept": "application, text/javascript, */*; q=0.01",
    "Accept-Encoding": "Utf-8",
    "Referer": ANIMEPAHE_BASE,
    "DNT": "1",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "TE": "trailers",
}
SERVER_HEADERS = {
    "Host": "kwik.cx",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "Utf-8",
    "DNT": "1",
    "Connection": "keep-alive",
    "Referer": ANIMEPAHE_BASE + "/",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "iframe",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "Priority": "u=4",
    "TE": "trailers",
}

STREAM_HEADERS = {
    # "Host": "vault-16.owocdn.top", # This will have to be the actual host of the stream (behind Kwik)
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Origin": CDN_PROVIDER_BASE,
    "Sec-GPC": "1",
    "Connection": "keep-alive",
    "Referer": CDN_PROVIDER_BASE + "/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
    "TE": "trailers",
}


JUICY_STREAM_REGEX = re.compile(r"source='(.*)';")
KWIK_RE = re.compile(r"Player\|(.+?)'")
