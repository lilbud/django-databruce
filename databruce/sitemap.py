from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = "daily"

    def items(self):
        return [
            "events",
            "tours",
            "songs",
            "venues",
            "cities",
            "states",
            "countries",
            "relations",
            "bands",
            "releases",
            "bootlegs",
            "nugs",
            "adv_search",
            "note_search",
            "about",
            "links",
        ]

    def location(self, item):
        return reverse(item)
