from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ENUMS
class MediaStatus(Enum):
    FINISHED = "FINISHED"
    RELEASING = "RELEASING"
    NOT_YET_RELEASED = "NOT_YET_RELEASED"
    CANCELLED = "CANCELLED"
    HIATUS = "HIATUS"


class MediaType(Enum):
    ANIME = "ANIME"
    MANGA = "MANGA"


class UserMediaListStatus(Enum):
    PLANNING = "planning"
    WATCHING = "watching"
    COMPLETED = "completed"
    DROPPED = "dropped"
    PAUSED = "paused"
    REPEATING = "repeating"


class MediaGenre(Enum):
    ACTION = "Action"
    ADVENTURE = "Adventure"
    COMEDY = "Comedy"
    DRAMA = "Drama"
    ECCHI = "Ecchi"
    FANTASY = "Fantasy"
    HORROR = "Horror"
    MAHOU_SHOUJO = "Mahou Shoujo"
    MECHA = "Mecha"
    MUSIC = "Music"
    MYSTERY = "Mystery"
    PSYCHOLOGICAL = "Psychological"
    ROMANCE = "Romance"
    SCI_FI = "Sci-Fi"
    SLICE_OF_LIFE = "Slice of Life"
    SPORTS = "Sports"
    SUPERNATURAL = "Supernatural"
    THRILLER = "Thriller"
    HENTAI = "Hentai"


class MediaFormat(Enum):
    TV = "TV"
    TV_SHORT = "TV_SHORT"
    MOVIE = "MOVIE"
    MANGA = "MANGA"
    SPECIAL = "SPECIAL"
    OVA = "OVA"
    ONA = "ONA"
    MUSIC = "MUSIC"
    NOVEL = "NOVEL"
    ONE_SHOT = "ONE_SHOT"


class NotificationType(Enum):
    AIRING = "AIRING"
    RELATED_MEDIA_ADDITION = "RELATED_MEDIA_ADDITION"
    MEDIA_DATA_CHANGE = "MEDIA_DATA_CHANGE"
    # ... add other types as needed


# MODELS
class BaseMediaApiModel(BaseModel):
    model_config = ConfigDict(frozen=True)


class MediaImage(BaseMediaApiModel):
    """A generic representation of media imagery URLs."""

    large: str
    medium: Optional[str] = None
    extra_large: Optional[str] = None


class MediaTitle(BaseMediaApiModel):
    """A generic representation of media titles."""

    english: str
    romaji: Optional[str] = None
    native: Optional[str] = None


class MediaTrailer(BaseMediaApiModel):
    """A generic representation of a media trailer."""

    id: str
    site: str  # e.g., "youtube"
    thumbnail_url: Optional[str] = None


class AiringSchedule(BaseMediaApiModel):
    """A generic representation of the next airing episode."""

    episode: int
    airing_at: Optional[datetime] = None


class CharacterName(BaseMediaApiModel):
    """A generic representation of a character's name."""

    first: Optional[str] = None
    middle: Optional[str] = None
    last: Optional[str] = None
    full: Optional[str] = None
    native: Optional[str] = None


class CharacterImage(BaseMediaApiModel):
    """A generic representation of a character's image."""

    medium: Optional[str] = None
    large: Optional[str] = None


class Character(BaseMediaApiModel):
    """A generic representation of an anime character."""

    id: Optional[int] = None
    name: CharacterName
    image: Optional[CharacterImage] = None
    description: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[str] = None
    blood_type: Optional[str] = None
    favourites: Optional[int] = None
    date_of_birth: Optional[datetime] = None


class AiringScheduleItem(BaseMediaApiModel):
    """A generic representation of an airing schedule item."""

    episode: int
    airing_at: Optional[datetime] = None
    time_until_airing: Optional[int] = None  # In seconds


class CharacterSearchResult(BaseMediaApiModel):
    """A generic representation of character search results."""

    characters: List[Character] = Field(default_factory=list)
    page_info: Optional[PageInfo] = None


class AiringScheduleResult(BaseMediaApiModel):
    """A generic representation of airing schedule results."""

    schedule_items: List[AiringScheduleItem] = Field(default_factory=list)
    page_info: Optional[PageInfo] = None


class Studio(BaseMediaApiModel):
    """A generic representation of an animation studio."""

    id: Optional[int] = None
    name: Optional[str] = None
    favourites: Optional[int] = None
    is_animation_studio: Optional[bool] = None


class MediaTagItem(BaseMediaApiModel):
    """A generic representation of a descriptive tag."""

    name: MediaTag
    rank: Optional[int] = None  # Percentage relevance from 0-100


class StreamingEpisode(BaseMediaApiModel):
    """A generic representation of a streaming episode."""

    title: str
    thumbnail: Optional[str] = None


class UserListItem(BaseMediaApiModel):
    """Generic representation of a user's list status for a media item."""

    id: Optional[int] = None
    status: Optional[UserMediaListStatus] = None
    progress: Optional[int] = None
    score: Optional[float] = None
    repeat: Optional[int] = None
    notes: Optional[str] = None
    start_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[str] = None


class MediaItem(BaseMediaApiModel):
    id: int
    title: MediaTitle
    id_mal: Optional[int] = None
    type: MediaType = MediaType.ANIME
    status: MediaStatus = MediaStatus.FINISHED
    format: Optional[MediaFormat] = MediaFormat.TV

    cover_image: Optional[MediaImage] = None
    banner_image: Optional[str] = None
    trailer: Optional[MediaTrailer] = None

    description: Optional[str] = None
    episodes: Optional[int] = None
    duration: Optional[int] = None  # In minutes
    genres: List[MediaGenre] = Field(default_factory=list)
    tags: List[MediaTagItem] = Field(default_factory=list)
    studios: List[Studio] = Field(default_factory=list)
    synonymns: List[str] = Field(default_factory=list)

    average_score: Optional[float] = None
    popularity: Optional[int] = None
    favourites: Optional[int] = None

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    next_airing: Optional[AiringSchedule] = None

    # streaming episodes
    streaming_episodes: Dict[str, StreamingEpisode] = Field(default_factory=dict)

    # user related
    user_status: Optional[UserListItem] = None


class Notification(BaseMediaApiModel):
    """A generic representation of a user notification."""

    id: int
    type: NotificationType
    episode: Optional[int] = None
    contexts: List[str] = Field(default_factory=list)
    created_at: datetime
    media: MediaItem


class PageInfo(BaseMediaApiModel):
    """Generic pagination information."""

    total: int = 1
    current_page: int = 1
    has_next_page: bool = False
    per_page: int = 15


class MediaSearchResult(BaseMediaApiModel):
    """A generic representation of a page of media search results."""

    page_info: PageInfo
    media: List[MediaItem] = Field(default_factory=list)


class UserProfile(BaseMediaApiModel):
    """A generic representation of a user's profile."""

    id: int
    name: str
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None


class Reviewer(BaseMediaApiModel):
    """A generic representation of a user who wrote a review."""

    name: str
    avatar_url: Optional[str] = None


class MediaReview(BaseMediaApiModel):
    """A generic representation of a media review."""

    summary: Optional[str] = None
    body: str
    user: Reviewer


# ENUMS


class MediaTag(Enum):
    # Cast
    POLYAMOROUS = "Polyamorous"

    # Cast Main Cast
    ANTI_HERO = "Anti-Hero"
    ELDERLY_PROTAGONIST = "Elderly Protagonist"
    ENSEMBLE_CAST = "Ensemble Cast"
    ESTRANGED_FAMILY = "Estranged Family"
    FEMALE_PROTAGONIST = "Female Protagonist"
    MALE_PROTAGONIST = "Male Protagonist"
    PRIMARILY_ADULT_CAST = "Primarily Adult Cast"
    PRIMARILY_ANIMAL_CAST = "Primarily Animal Cast"
    PRIMARILY_CHILD_CAST = "Primarily Child Cast"
    PRIMARILY_FEMALE_CAST = "Primarily Female Cast"
    PRIMARILY_MALE_CAST = "Primarily Male Cast"
    PRIMARILY_TEEN_CAST = "Primarily Teen Cast"

    # Cast Traits
    AGE_REGRESSION = "Age Regression"
    AGENDER = "Agender"
    ALIENS = "Aliens"
    AMNESIA = "Amnesia"
    ANGELS = "Angels"
    ANTHROPOMORPHISM = "Anthropomorphism"
    AROMANTIC = "Aromantic"
    ARRANGED_MARRIAGE = "Arranged Marriage"
    ARTIFICIAL_INTELLIGENCE = "Artificial Intelligence"
    ASEXUAL = "Asexual"
    BISEXUAL = "Bisexual"
    BUTLER = "Butler"
    CENTAUR = "Centaur"
    CHIMERA = "Chimera"
    CHUUNIBYOU = "Chuunibyou"
    CLONE = "Clone"
    COSPLAY = "Cosplay"
    COWBOYS = "Cowboys"
    CROSSDRESSING = "Crossdressing"
    CYBORG = "Cyborg"
    DELINQUENTS = "Delinquents"
    DEMONS = "Demons"
    DETECTIVE = "Detective"
    DINOSAURS = "Dinosaurs"
    DISABILITY = "Disability"
    DISSOCIATIVE_IDENTITIES = "Dissociative Identities"
    DRAGONS = "Dragons"
    DULLAHAN = "Dullahan"
    ELF = "Elf"
    FAIRY = "Fairy"
    FEMBOY = "Femboy"
    GHOST = "Ghost"
    GOBLIN = "Goblin"
    GODS = "Gods"
    GYARU = "Gyaru"
    HIKIKOMORI = "Hikikomori"
    HOMELESS = "Homeless"
    IDOL = "Idol"
    KEMONOMIMI = "Kemonomimi"
    KUUDERE = "Kuudere"
    MAIDS = "Maids"
    MERMAID = "Mermaid"
    MONSTER_BOY = "Monster Boy"
    MONSTER_GIRL = "Monster Girl"
    NEKOMIMI = "Nekomimi"
    NINJA = "Ninja"
    NUDITY = "Nudity"
    NUN = "Nun"
    OFFICE_LADY = "Office Lady"
    OIRAN = "Oiran"
    OJOU_SAMA = "Ojou-sama"
    ORPHAN = "Orphan"
    PIRATES = "Pirates"
    ROBOTS = "Robots"
    SAMURAI = "Samurai"
    SHRINE_MAIDEN = "Shrine Maiden"
    SKELETON = "Skeleton"
    SUCCUBUS = "Succubus"
    TANNED_SKIN = "Tanned Skin"
    TEACHER = "Teacher"
    TOMBOY = "Tomboy"
    TRANSGENDER = "Transgender"
    TSUNDERE = "Tsundere"
    TWINS = "Twins"
    VAMPIRE = "Vampire"
    VETERINARIAN = "Veterinarian"
    VIKINGS = "Vikings"
    VILLAINESS = "Villainess"
    VTUBER = "VTuber"
    WEREWOLF = "Werewolf"
    WITCH = "Witch"
    YANDERE = "Yandere"
    YOUKAI = "Youkai"
    ZOMBIE = "Zombie"

    # Demographic
    JOSEI = "Josei"
    KIDS = "Kids"
    SEINEN = "Seinen"
    SHOUJO = "Shoujo"
    SHOUNEN = "Shounen"

    # Setting
    MATRIARCHY = "Matriarchy"

    # Setting Scene
    BAR = "Bar"
    BOARDING_SCHOOL = "Boarding School"
    CAMPING = "Camping"
    CIRCUS = "Circus"
    COASTAL = "Coastal"
    COLLEGE = "College"
    DESERT = "Desert"
    DUNGEON = "Dungeon"
    FOREIGN = "Foreign"
    INN = "Inn"
    KONBINI = "Konbini"
    NATURAL_DISASTER = "Natural Disaster"
    OFFICE = "Office"
    OUTDOOR_ACTIVITIES = "Outdoor Activities"
    PRISON = "Prison"
    RESTAURANT = "Restaurant"
    RURAL = "Rural"
    SCHOOL = "School"
    SCHOOL_CLUB = "School Club"
    SNOWSCAPE = "Snowscape"
    URBAN = "Urban"
    WILDERNESS = "Wilderness"
    WORK = "Work"

    # Setting Time
    ACHRONOLOGICAL_ORDER = "Achronological Order"
    ANACHRONISM = "Anachronism"
    ANCIENT_CHINA = "Ancient China"
    DYSTOPIAN = "Dystopian"
    HISTORICAL = "Historical"
    MEDIEVAL = "Medieval"
    TIME_SKIP = "Time Skip"

    # Setting Universe
    AFTERLIFE = "Afterlife"
    ALTERNATE_UNIVERSE = "Alternate Universe"
    AUGMENTED_REALITY = "Augmented Reality"
    OMEGAVERSE = "Omegaverse"
    POST_APOCALYPTIC = "Post-Apocalyptic"
    SPACE = "Space"
    URBAN_FANTASY = "Urban Fantasy"
    VIRTUAL_WORLD = "Virtual World"

    # Sexual Content
    AHEGAO = "Ahegao"
    AMPUTATION = "Amputation"
    ANAL_SEX = "Anal Sex"
    ARMPITS = "Armpits"
    ASHIKOKI = "Ashikoki"
    ASPHYXIATION = "Asphyxiation"
    BONDAGE = "Bondage"
    BOOBJOB = "Boobjob"
    CERVIX_PENETRATION = "Cervix Penetration"
    CHEATING = "Cheating"
    CUMFLATION = "Cumflation"
    CUNNILINGUS = "Cunnilingus"
    DEEPTHROAT = "Deepthroat"
    DEFLORATION = "Defloration"
    DILF = "DILF"
    DOUBLE_PENETRATION = "Double Penetration"
    EROTIC_PIERCINGS = "Erotic Piercings"
    EXHIBITIONISM = "Exhibitionism"
    FACIAL = "Facial"
    FEET = "Feet"
    FELLATIO = "Fellatio"
    FEMDOM = "Femdom"
    FISTING = "Fisting"
    FLAT_CHEST = "Flat Chest"
    FUTANARI = "Futanari"
    GROUP_SEX = "Group Sex"
    HAIR_PULLING = "Hair Pulling"
    HANDJOB = "Handjob"
    HUMAN_PET = "Human Pet"
    HYPERSEXUALITY = "Hypersexuality"
    INCEST = "Incest"
    INSEKI = "Inseki"
    IRRUMATIO = "Irrumatio"
    LACTATION = "Lactation"
    LARGE_BREASTS = "Large Breasts"
    MALE_PREGNANCY = "Male Pregnancy"
    MASOCHISM = "Masochism"
    MASTURBATION = "Masturbation"
    MATING_PRESS = "Mating Press"
    MILF = "MILF"
    NAKADASHI = "Nakadashi"
    NETORARE = "Netorare"
    NETORASE = "Netorase"
    NETORI = "Netori"
    PET_PLAY = "Pet Play"
    PROSTITUTION = "Prostitution"
    PUBLIC_SEX = "Public Sex"
    RAPE = "Rape"
    RIMJOB = "Rimjob"
    SADISM = "Sadism"
    SCAT = "Scat"
    SCISSORING = "Scissoring"
    SEX_TOYS = "Sex Toys"
    SHIMAIDON = "Shimaidon"
    SQUIRTING = "Squirting"
    SUMATA = "Sumata"
    SWEAT = "Sweat"
    TENTACLES = "Tentacles"
    THREESOME = "Threesome"
    VIRGINITY = "Virginity"
    VORE = "Vore"
    VOYEUR = "Voyeur"
    WATERSPORTS = "Watersports"
    ZOOPHILIA = "Zoophilia"

    # Technical
    _4_KOMA = "4-koma"
    ACHROMATIC = "Achromatic"
    ADVERTISEMENT = "Advertisement"
    ANTHOLOGY = "Anthology"
    CGI = "CGI"
    EPISODIC = "Episodic"
    FLASH = "Flash"
    FULL_CGI = "Full CGI"
    FULL_COLOR = "Full Color"
    LONG_STRIP = "Long Strip"
    MIXED_MEDIA = "Mixed Media"
    NO_DIALOGUE = "No Dialogue"
    NON_FICTION = "Non-fiction"
    POV = "POV"
    PUPPETRY = "Puppetry"
    ROTOSCOPING = "Rotoscoping"
    STOP_MOTION = "Stop Motion"
    VERTICAL_VIDEO = "Vertical Video"

    # Theme Action
    ARCHERY = "Archery"
    BATTLE_ROYALE = "Battle Royale"
    ESPIONAGE = "Espionage"
    FUGITIVE = "Fugitive"
    GUNS = "Guns"
    MARTIAL_ARTS = "Martial Arts"
    SPEARPLAY = "Spearplay"
    SWORDPLAY = "Swordplay"

    # Theme Arts
    ACTING = "Acting"
    CALLIGRAPHY = "Calligraphy"
    CLASSIC_LITERATURE = "Classic Literature"
    DRAWING = "Drawing"
    FASHION = "Fashion"
    FOOD = "Food"
    KABUKI = "Kabuki"
    MAKEUP = "Makeup"
    PHOTOGRAPHY = "Photography"
    RAKUGO = "Rakugo"
    WRITING = "Writing"

    # Theme Arts-Music
    BAND = "Band"
    CLASSICAL_MUSIC = "Classical Music"
    DANCING = "Dancing"
    HIP_HOP_MUSIC = "Hip-hop Music"
    JAZZ_MUSIC = "Jazz Music"
    METAL_MUSIC = "Metal Music"
    MUSICAL_THEATER = "Musical Theater"
    ROCK_MUSIC = "Rock Music"

    # Theme Comedy
    PARODY = "Parody"
    SATIRE = "Satire"
    SLAPSTICK = "Slapstick"
    SURREAL_COMEDY = "Surreal Comedy"

    # Theme Drama
    BULLYING = "Bullying"
    CLASS_STRUGGLE = "Class Struggle"
    COMING_OF_AGE = "Coming of Age"
    CONSPIRACY = "Conspiracy"
    ECO_HORROR = "Eco-Horror"
    FAKE_RELATIONSHIP = "Fake Relationship"
    KINGDOM_MANAGEMENT = "Kingdom Management"
    REHABILITATION = "Rehabilitation"
    REVENGE = "Revenge"
    SUICIDE = "Suicide"
    TRAGEDY = "Tragedy"

    # Theme Fantasy
    ALCHEMY = "Alchemy"
    BODY_SWAPPING = "Body Swapping"
    CULTIVATION = "Cultivation"
    CURSES = "Curses"
    EXORCISM = "Exorcism"
    FAIRY_TALE = "Fairy Tale"
    HENSHIN = "Henshin"
    ISEKAI = "Isekai"
    REVERSE_ISEKAI = "Reverse Isekai"
    KAIJU = "Kaiju"
    MAGIC = "Magic"
    MYTHOLOGY = "Mythology"
    NECROMANCY = "Necromancy"
    SHAPESHIFTING = "Shapeshifting"
    STEAMPUNK = "Steampunk"
    SUPER_POWER = "Super Power"
    SUPERHERO = "Superhero"
    WUXIA = "Wuxia"

    # Theme Game
    BOARD_GAME = "Board Game"
    E_SPORTS = "E-Sports"
    VIDEO_GAMES = "Video Games"

    # Theme Game-Card & Board Game
    CARD_BATTLE = "Card Battle"
    GO = "Go"
    KARUTA = "Karuta"
    MAHJONG = "Mahjong"
    POKER = "Poker"
    SHOGI = "Shogi"

    # Theme Game-Sport
    ACROBATICS = "Acrobatics"
    AIRSOFT = "Airsoft"
    AMERICAN_FOOTBALL = "American Football"
    ATHLETICS = "Athletics"
    BADMINTON = "Badminton"
    BASEBALL = "Baseball"
    BASKETBALL = "Basketball"
    BOWLING = "Bowling"
    BOXING = "Boxing"
    CHEERLEADING = "Cheerleading"
    CYCLING = "Cycling"
    FENCING = "Fencing"
    FISHING = "Fishing"
    FITNESS = "Fitness"
    FOOTBALL = "Football"
    GOLF = "Golf"
    HANDBALL = "Handball"
    ICE_SKATING = "Ice Skating"
    JUDO = "Judo"
    LACROSSE = "Lacrosse"
    PARKOUR = "Parkour"
    RUGBY = "Rugby"
    SCUBA_DIVING = "Scuba Diving"
    SKATEBOARDING = "Skateboarding"
    SUMO = "Sumo"
    SURFING = "Surfing"
    SWIMMING = "Swimming"
    TABLE_TENNIS = "Table Tennis"
    TENNIS = "Tennis"
    VOLLEYBALL = "Volleyball"
    WRESTLING = "Wrestling"

    # Theme Other
    ADOPTION = "Adoption"
    ANIMALS = "Animals"
    ASTRONOMY = "Astronomy"
    AUTOBIOGRAPHICAL = "Autobiographical"
    BIOGRAPHICAL = "Biographical"
    BLACKMAIL = "Blackmail"
    BODY_HORROR = "Body Horror"
    BODY_IMAGE = "Body Image"
    CANNIBALISM = "Cannibalism"
    CHIBI = "Chibi"
    COSMIC_HORROR = "Cosmic Horror"
    CREATURE_TAMING = "Creature Taming"
    CRIME = "Crime"
    CROSSOVER = "Crossover"
    DEATH_GAME = "Death Game"
    DENPA = "Denpa"
    DRUGS = "Drugs"
    ECONOMICS = "Economics"
    EDUCATIONAL = "Educational"
    ENVIRONMENTAL = "Environmental"
    ERO_GURO = "Ero Guro"
    FILMMAKING = "Filmmaking"
    FOUND_FAMILY = "Found Family"
    GAMBLING = "Gambling"
    GENDER_BENDING = "Gender Bending"
    GORE = "Gore"
    INDIGENOUS_CULTURES = "Indigenous Cultures"
    LANGUAGE_BARRIER = "Language Barrier"
    LGBTQ_PLUS_THEMES = "LGBTQ+ Themes"
    LOST_CIVILIZATION = "Lost Civilization"
    MARRIAGE = "Marriage"
    MEDICINE = "Medicine"
    MEMORY_MANIPULATION = "Memory Manipulation"
    META = "Meta"
    MOUNTAINEERING = "Mountaineering"
    NOIR = "Noir"
    OTAKU_CULTURE = "Otaku Culture"
    PANDEMIC = "Pandemic"
    PHILOSOPHY = "Philosophy"
    POLITICS = "Politics"
    PREGNANCY = "Pregnancy"
    PROXY_BATTLE = "Proxy Battle"
    PSYCHOSEXUAL = "Psychosexual"
    REINCARNATION = "Reincarnation"
    RELIGION = "Religion"
    RESCUE = "Rescue"
    ROYAL_AFFAIRS = "Royal Affairs"
    SLAVERY = "Slavery"
    SOFTWARE_DEVELOPMENT = "Software Development"
    SURVIVAL = "Survival"
    TERRORISM = "Terrorism"
    TORTURE = "Torture"
    TRAVEL = "Travel"
    VOCAL_SYNTH = "Vocal Synth"
    WAR = "War"

    # Theme Other-Organisations
    ASSASSINS = "Assassins"
    CRIMINAL_ORGANIZATION = "Criminal Organization"
    CULT = "Cult"
    FIREFIGHTERS = "Firefighters"
    GANGS = "Gangs"
    MAFIA = "Mafia"
    MILITARY = "Military"
    POLICE = "Police"
    TRIADS = "Triads"
    YAKUZA = "Yakuza"

    # Theme Other-Vehicle
    AVIATION = "Aviation"
    CARS = "Cars"
    MOPEDS = "Mopeds"
    MOTORCYCLES = "Motorcycles"
    SHIPS = "Ships"
    TANKS = "Tanks"
    TRAINS = "Trains"

    # Theme Romance
    AGE_GAP = "Age Gap"
    BOYS_LOVE = "Boys' Love"
    COHABITATION = "Cohabitation"
    FEMALE_HAREM = "Female Harem"
    HETEROSEXUAL = "Heterosexual"
    LOVE_TRIANGLE = "Love Triangle"
    MALE_HAREM = "Male Harem"
    MATCHMAKING = "Matchmaking"
    MIXED_GENDER_HAREM = "Mixed Gender Harem"
    TEENS_LOVE = "Teens' Love"
    UNREQUITED_LOVE = "Unrequited Love"
    YURI = "Yuri"

    # Theme Sci-Fi
    CYBERPUNK = "Cyberpunk"
    SPACE_OPERA = "Space Opera"
    TIME_LOOP = "Time Loop"
    TIME_MANIPULATION = "Time Manipulation"
    TOKUSATSU = "Tokusatsu"

    # Theme Sci-Fi-Mecha
    REAL_ROBOT = "Real Robot"
    SUPER_ROBOT = "Super Robot"

    # Theme Slice of Life
    AGRICULTURE = "Agriculture"
    CUTE_BOYS_DOING_CUTE_THINGS = "Cute Boys Doing Cute Things"
    CUTE_GIRLS_DOING_CUTE_THINGS = "Cute Girls Doing Cute Things"
    FAMILY_LIFE = "Family Life"
    HORTICULTURE = "Horticulture"
    IYASHIKEI = "Iyashikei"
    PARENTHOOD = "Parenthood"


class MediaSort(Enum):
    ID = "ID"
    ID_DESC = "ID_DESC"
    TITLE_ROMAJI = "TITLE_ROMAJI"
    TITLE_ROMAJI_DESC = "TITLE_ROMAJI_DESC"
    TITLE_ENGLISH = "TITLE_ENGLISH"
    TITLE_ENGLISH_DESC = "TITLE_ENGLISH_DESC"
    TITLE_NATIVE = "TITLE_NATIVE"
    TITLE_NATIVE_DESC = "TITLE_NATIVE_DESC"
    TYPE = "TYPE"
    TYPE_DESC = "TYPE_DESC"
    FORMAT = "FORMAT"
    FORMAT_DESC = "FORMAT_DESC"
    START_DATE = "START_DATE"
    START_DATE_DESC = "START_DATE_DESC"
    END_DATE = "END_DATE"
    END_DATE_DESC = "END_DATE_DESC"
    SCORE = "SCORE"
    SCORE_DESC = "SCORE_DESC"
    POPULARITY = "POPULARITY"
    POPULARITY_DESC = "POPULARITY_DESC"
    TRENDING = "TRENDING"
    TRENDING_DESC = "TRENDING_DESC"
    EPISODES = "EPISODES"
    EPISODES_DESC = "EPISODES_DESC"
    DURATION = "DURATION"
    DURATION_DESC = "DURATION_DESC"
    STATUS = "STATUS"
    STATUS_DESC = "STATUS_DESC"
    CHAPTERS = "CHAPTERS"
    CHAPTERS_DESC = "CHAPTERS_DESC"
    VOLUMES = "VOLUMES"
    VOLUMES_DESC = "VOLUMES_DESC"
    UPDATED_AT = "UPDATED_AT"
    UPDATED_AT_DESC = "UPDATED_AT_DESC"
    SEARCH_MATCH = "SEARCH_MATCH"
    FAVOURITES = "FAVOURITES"
    FAVOURITES_DESC = "FAVOURITES_DESC"


class UserMediaListSort(Enum):
    MEDIA_ID = "MEDIA_ID"
    MEDIA_ID_DESC = "MEDIA_ID_DESC"
    SCORE = "SCORE"
    SCORE_DESC = "SCORE_DESC"
    STATUS = "STATUS"
    STATUS_DESC = "STATUS_DESC"
    PROGRESS = "PROGRESS"
    PROGRESS_DESC = "PROGRESS_DESC"
    PROGRESS_VOLUMES = "PROGRESS_VOLUMES"
    PROGRESS_VOLUMES_DESC = "PROGRESS_VOLUMES_DESC"
    REPEAT = "REPEAT"
    REPEAT_DESC = "REPEAT_DESC"
    PRIORITY = "PRIORITY"
    PRIORITY_DESC = "PRIORITY_DESC"
    STARTED_ON = "STARTED_ON"
    STARTED_ON_DESC = "STARTED_ON_DESC"
    FINISHED_ON = "FINISHED_ON"
    FINISHED_ON_DESC = "FINISHED_ON_DESC"
    ADDED_TIME = "ADDED_TIME"
    ADDED_TIME_DESC = "ADDED_TIME_DESC"
    UPDATED_TIME = "UPDATED_TIME"
    UPDATED_TIME_DESC = "UPDATED_TIME_DESC"
    MEDIA_TITLE_ROMAJI = "MEDIA_TITLE_ROMAJI"
    MEDIA_TITLE_ROMAJI_DESC = "MEDIA_TITLE_ROMAJI_DESC"
    MEDIA_TITLE_ENGLISH = "MEDIA_TITLE_ENGLISH"
    MEDIA_TITLE_ENGLISH_DESC = "MEDIA_TITLE_ENGLISH_DESC"
    MEDIA_TITLE_NATIVE = "MEDIA_TITLE_NATIVE"
    MEDIA_TITLE_NATIVE_DESC = "MEDIA_TITLE_NATIVE_DESC"
    MEDIA_POPULARITY = "MEDIA_POPULARITY"
    MEDIA_POPULARITY_DESC = "MEDIA_POPULARITY_DESC"
    MEDIA_SCORE = "MEDIA_SCORE"
    MEDIA_SCORE_DESC = "MEDIA_SCORE_DESC"
    MEDIA_START_DATE = "MEDIA_START_DATE"
    MEDIA_START_DATE_DESC = "MEDIA_START_DATE_DESC"
    MEDIA_RATING = "MEDIA_RATING"
    MEDIA_RATING_DESC = "MEDIA_RATING_DESC"


class MediaSeason(Enum):
    WINTER = "WINTER"
    SPRING = "SPRING"
    SUMMER = "SUMMER"
    FALL = "FALL"


class MediaYear(Enum):
    _1900 = "1900"
    _1910 = "1910"
    _1920 = "1920"
    _1930 = "1930"
    _1940 = "1940"
    _1950 = "1950"
    _1960 = "1960"
    _1970 = "1970"
    _1980 = "1980"
    _1990 = "1990"
    _2000 = "2000"
    _2004 = "2004"
    _2005 = "2005"
    _2006 = "2006"
    _2007 = "2007"
    _2008 = "2008"
    _2009 = "2009"
    _2010 = "2010"
    _2011 = "2011"
    _2012 = "2012"
    _2013 = "2013"
    _2014 = "2014"
    _2015 = "2015"
    _2016 = "2016"
    _2017 = "2017"
    _2018 = "2018"
    _2019 = "2019"
    _2020 = "2020"
    _2021 = "2021"
    _2022 = "2022"
    _2023 = "2023"
    _2024 = "2024"
    _2025 = "2025"
