from .forms import EventSearch


def base_data(request):  # noqa: ARG001
    data = {}
    data["searchForm"] = EventSearch()
    return data


# views.py or context_processors.py


def get_navbar_links():
    return [
        {
            "name": "Events",
            "match_keyword": "events",
            "icon": "bi-calendar-fill",
            "children": [
                {"name": "Events By Year", "url": "events"},
                {"name": "Events By Run", "url": "runs"},
                {
                    "name": "Events By Type",
                    "url": "events_by_type",
                    "kwargs": {"slug": "concert"},
                },
                {
                    "name": "Events By Tag",
                    "url": "events_by_tag",
                    "kwargs": {"slug": "full-greetings"},
                },
                {"name": "Event Calendar", "url": "calendar"},
            ],
        },
        {
            "name": "Tours",
            "match_keyword": "tours",
            "icon": "bi-bus-front-fill",
            "children": [
                {"name": "Tours", "url": "tours"},
                {"name": "Tour Legs", "url": "tour_legs"},
            ],
        },
        {
            "name": "Songs",
            "match_keyword": "songs",
            "icon": "bi-music-note-beamed",
            "children": [
                {"name": "Songs", "url": "songs"},
                {"name": "Lyrics", "url": "song_lyrics"},
            ],
        },
        {
            "name": "Locations",
            "icon": "bi-geo-alt-fill",
            "children": [
                {"name": "Venues", "url": "venues"},
                {"name": "Cities", "url": "cities"},
                {"name": "States", "url": "states"},
                {"name": "Countries", "url": "countries"},
            ],
        },
        {
            "name": "Relations and Bands",
            "match_keywords": ["relations", "bands"],
            "icon": "bi-person-fill",
            "children": [
                {"name": "Relations", "url": "relations"},
                {"name": "Bands", "url": "bands"},
            ],
        },
        {
            "name": "Releases",
            "match_keyword": "releases",
            "icon": "bi-vinyl-fill",
            "children": [
                {"name": "Official Releases", "url": "releases"},
                {"name": "Nugs Releases", "url": "nugs"},
                # {"name": "Bootlegs", "url": "bootlegs"},
            ],
        },
        {
            "name": "Search",
            "match_keyword": "search",
            "icon": "bi-binoculars-fill",
            "children": [
                {"name": "Advanced Search", "url": "adv_search"},
                {"name": "Setlist Note Search", "url": "note_search"},
            ],
        },
        {
            "name": "About Databruce",
            "icon": "bi-question-circle-fill",
            "children": [
                {
                    "name": "News",
                    "url": "blog:blog",
                    "match_keyword": "blog",
                },
                {
                    "name": "About Site",
                    "url": "blog:blog_post",
                    "kwargs": {"slug": "about-databruce"},
                },
                {"name": "Links", "url": "blog:blog_post", "kwargs": {"slug": "links"}},
                {"name": "Updates", "url": "updates"},
                {
                    "name": "Roadmap",
                    "url": "blog:blog_post",
                    "kwargs": {"slug": "roadmap"},
                },
                {"name": "Contact Us", "url": "contact"},
            ],
        },
    ]


def navbar_context(request):
    return {"nav_links": get_navbar_links()}
