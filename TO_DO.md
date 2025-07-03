# Digital Ocean Stuff to Fix:
<!-- - search looks like hell on mobile -->
<!-- - actually, check every page on mobile -->
<!-- - logout not working? -->
<!-- - sort out static files hosting? -->
- get registration and email working
  <!-- - have to purchase porkbun email, as DO blocks all SMTP email ports for security reasons -->
  - got working with mailgun as a temporary. They have pretty low limits (100/day, 3000/mo) so I'm not sure how well it will work exactly. I doubt password resets will be major but activations could be limited not sure. Site won't require login so its not a major deal.
<!-- - flesh out user profile, add personal info and ability for user to edit that. -->
<!-- - add users page with table so people can find other pages -->
- look into "friends" with profiles?


# Pages to add:
<!-- - Event Run Details
  - events, songs -->
<!-- - Tour Legs -->
<!-- - Tour Leg Details?
  - events, songs -->
<!-- - Setlist Notes Search -->

# Features?
<!-- - Event page layout improvements
  - clean up setlist notes. Some events (like 2016-01-16) have a ridiculous number of notes, all of which are debut/premiere/bustout. Find another way to display this info. Could maybe do a table like Dripfield, but that doesn't quite work on mobile. They use tooltips with links to indicate last show, which jump to that event when tapped on mobile.
  - nugs/releases/archive links
  - notes
  - album breakdown -->
- Advanced Search: change to GET instead of POST
  - while POST works, it doesn't allow sharing of results. JB has a "get short link" which returns a bit.ly link for the long search url. This allows results to be shared with others rather than everyone having to put in all the search results manually.
  - would require making an "advanced search results" view again, and going that way.
  - alternatively, keep the current view and have a parameter passed to the view like "url ... with submit=true"?.
- update structure of pages
  - especially the tour/song pages, or any with the header buttons. Maybe have the following as shortcuts?
    - tours/###/stats
    - tours/###/songs
    - tours/###/shows

- Songs page additions? likely dropdowns or maybe incorporate the sidebar filter that dripfield does?
  - Songs only played as snippets (if snip_only is true)
  - Songs never played live (all num columns == 0)

<!-- - Releases
  - add musicbrainz links -->

# Other
<!-- - move tours to a dropdown on navbar? tours/legs -->
<!-- - Clean up release tracks page, add musicbrainz links and art -->
<!-- - style pages to use cards like setlist page -->
<!-- - finish setlist page, add venue/city links and show info like title/type/run/tour.  -->
<!-- figure out a logo -->
<!-- Better styling -->

# eventual features after initial launch
- article vault
- Radio Nowhere Archive page