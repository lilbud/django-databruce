Note: While I have posted updates in various places, I've never compiled them together like this. This is a somewhat broad overview of changes to the site. The version numbers are largely arbitrary, and definitely don't follow "best practices". This is being written well after the fact, and the numbers are just to mark progress.

I had intended to create "releases" on Github, but you can't easily backdate them. And this really isn't a project with "releases", so it wouldn't make sense.

# v0.1 (June 10, 2025)

First beta release of Databruce. Site was opened to a small group to test and give feedback.

# v0.11 (June 11, 2025)

- Added "users" page
- Added ability for users to change username/email
- Added "latest show" card to front page

# v0.12 (June 14, 2025)

- User Profile Updates
  - "Rare Songs" (<100 total plays) added
  - "Personal Premieres" added
  - "Most Played Not Seen" added
- Tour Detail page now shows songs in a given position (Opener/Closer)

# v1.0 (July 15, 2025)

First public release of the site. Site was locked behind a login and accounts only I could make while beta testing was underway. Had to get an email provider set up to send confirmation emails

- Event page style changes to look better on mobile
- Added autocomplete to navbar event search

# v1.01 (July 18, 2025)

- Login now redirects to previous page rather than home page

# v1.02 (July 21, 2025)

- Date filtering added to tables
- Advanced Search form improved on mobile
- Added short url creation to advanced search (thanks to Jerrybase for the idea)
- General layout changes
- Added About page

# v1.03 (August 26, 2025)

- Fixed "On This Day" home page card not updating with current date

# v1.04 (September 3, 2025)

- Updated Song page layout
- Updated Event page layout
- Updated Events page
- Rewrote About page

# v1.05 (September 8, 2025)

- Added "tour" column to event page
- Added colored markers to event setlist page to indicate "position" (show opener, show closer, etc.)

# v1.06 (October 25, 2025)

- Song Detail page loads faster
- Style changes, largely to "standardize" everything
- Added "Synthwave" theme from DaisyUI
- Added "Setlist Options" to Event Detail page, contained toggle to show/hide all setlist notes, as well as button to copy setlist as plain text.

# v1.10 (December 3, 2025)

- Added "Event Calendar" page, shows events and runs in a more visual manner
- Synthwave theme removed, wasn't a fan of it
- Added regex support to Table Search
- Tables are now responsive on mobile, putting everything in a child row instead of requiring horizontal scroll
- Release Detail page now groups tracks by disc

# v1.11 (December 8, 2025)

- Updated Event Detail, songs in setlist are now highlighted when hovering over an album in the "breakdown" card. (Credit to Dripfield.pro)
- Fixed Event Detail showing "null" for some gaps due to some shows not being counted
- Updated Event Detail layout, setlist card is wider

# v1.12 (January 4, 2026)

- (12/14) Added `changelog.md`, lists changes and versions. Versions prior to 1.1 were retroactively added, and shouldn't be considered accurate.
- (12/15) Added "Remember Me" check to the login form. This *should* keep you logged in for 2 weeks.
- (12/17) Fixed table SearchBuilder. Moved to a bootstrap modal so it would stay on screen and not get cut off by table.
- (12/17) Added tabs to event detail page. Main page is "overview", and the only other option is "notes". This will be the home of any extended notes/reviews/etc. about each show. Feature will be modelled after Speedrun.com "News" tab with a card for each item.
- (12/19) Fixed advanced search fields not properly searching. Some filters were missing so no matter what was typed the result set wouldn't filter correctly.
- (12/19) Added "First Friday" filter to the Nugs Releases page
- (12/19) Nugs Releases now show time of release if it is known. Thanks to Kieran Lane who tracked times for many of these releases.
- (12/19) SearchBuilder modal width fixed
- (12/22) Responsive Child Rows removed as they make screen size changes incredibly slow. Now tables on mobile will only show the most important columns.
- (12/22) "Setlist Slots" tables now fix date/location columns and have the positions scrollable.
- (12/22) Mistakenly removed "Original Artist" column from songs table. This has been fixed.
- (12/22) Fixed event table links not being clickable

# v1.13 (January 27, 2026)

- (1/6) Fix songs page search not finding originals not marked as such. It would initially match against the "category" being originals/covers, but if category was a studio album then it wouldn't find it (so filtering originals then searching for Racing gave no results.)
- (1/6) Update footer year
- (1/6) Update Event Detail, move "placeholder date" text under date row. Remove background color.
- (1/17) Fix "last" in setlist showing null for tour debuts
- (1/18) Added "show gap" to song detail page. Listing how many shows since it's last performance.
- (1/23) Fix song detail page snippet table not loading properly
- (1/27) Event Setlist now tallies tour count/total live, instead of having to pull values from a view.
- (1/27) Combined "Year by Year" and "Stats" into single tab on SongDetail page
- (1/27) SongDetail snippet table now has band, venue, and location
- (1/27) Songs Page fixed columns being too wide on mobile
- (1/27) Songs Page searchbuilder on Lyrics now works properly
- (1/27) Song Detail page year-by-year chart now resizes correctly
- (1/27) Reenable autocomplete on navbar event search

# v1.13.1 (January 28, 2026)

- (1/28) Song Detail: fix frequency causing "divide by zero" error when there are no events
- (1/28) Events: "setlist" is now an annotated calculated value instead of a stored value
- (1/28) Events: Year dropdown is now next to page title instead of other side
- (1/28) Events: Year dropdown height now limited to stay on page
- (1/28) Event Calendar: Year dropdown spacing fixed
- (1/28) Events: Year dropdown now starts at current year and descends, instead of ascending from 1965.

# v1.14 (Feburary 2026)

- Replaced `django_rest_framework_datatables` with a custom renderer/pagination.
- Redid how much of the backend works, many pages now load a bit faster
- All page links now match primary site color
- Layout has been redone on many pages, particularly in regards to card/column spacing.
- Added `columnControl` to datatables, allows for more flexible ordering/sorting. This allows for easier multi-column ordering, as well as it now being possible on mobile.
- "Setlist Slots" tables now hide empty columns. Things like "Set 1/2" on tours with a "Show/Encore" structure
- Theme Toggle is now a simple "light/dark" button instead of a dropdown menu.
- Every link now uses UUID instead of ID, if you have any bookmarks they will not work anymore.
- Redid how DataTables filter/order/search
- Event Search: Fixed location not being shown on Event Search
- User Profile: songs seen/rare now show first/last event you saw a song at
- "Songs" table on many detail pages now shows first/last event
- Event Calendar:
  - Fixed Event Runs not showing up
  - Improved loading time
  - Links now open in new tab by default
  - Added releases
- Added "success" indicator on Contact Form submit.
- Home Page featured/latest setlist now shows position indicators and notes
- Lyric Detail note now renders markdown if present
- Event Detail
  - Loading time improved.
  - Column ratio modified, setlist card is *slightly* narrower, and side column expanded.
  - Onstage has been moved to it's own tab, rather than being squished on the sidebar.
  - Album Breakdown: percentage is now of total number of songs instead of per album
  - Album Breakdown: clicking on row now expands list of songs. This also means the popup is gone.
  - Fixed tour counts showing 1 for all songs and shows.
- Style:
  - Table columns with dates now show day of week
  - Updates to many layouts, including style tweaks and fixing some odd colors.
  - Dark Theme colors updated slightly, better contrast on cards
  - Much tighter layout in regards to spacing. Less padding in tables, and font has been shrunken slightly. Allows for more rows visible at once on desktop.
  - Fixed table horizonal scrolling, was originally removed due to odd quirks with Datatables breaking mobile layouts.
- Release Detail:
  - Notes now show if present
  - Fixed `event_date` showing date and time instead of just date
  - Discs now show for all releases. If there is a "disc name" (Tracks 2), it is shown, otherwise just "Disc #". Defaults to "Disc 1" in most cases
- Advanced Search:
  - Performance improvements
  - Significantly reworked this, as it was an absolute mess
  - "band" is now when a band appeared at an event rather than solely if they're the "main" band for an event
- Setlist Note Search
  - Redid notes on the database, so this has been updated to match. Now searches all setlist notes.

# v1.15 (March 2026)

- [Event Detail] Updated page so that "note" and "album breakdown" only show on the "overview" tab, and are hidden on the other tabs (onstage, notes, links).
- [Event Detail] Added "Nugs" button back to event detail header
- [Advanced Search] Updated event type to allow multiple values to be searched.
- [Advanced Search] Event type field now styled to closer match default dropdown
- [Release Detail] Fixed event link using wrong ID
- [Release Detail] Changed track num to text to allow for Vinyl releases, which follow a different format than simply counting tracks.
- [Song Detail] Added snippet, opener, and closer count to info
- [Detail Pages] Added count badge to the tab buttons on most detail pages. This includes event count and song count for: Event Run, Tour, Tour Leg, Venue, City, State, Country. Tours also counts Tour Legs. This is loaded with the table, and will briefly show 0.
- All event and song tables have been made consistent in terms of column widths and ordering/searching.
- [Song Tables] These now pull songs listed as recording at private events in addition to songs during a "valid" set at a public show. This way, venues like the Record Plant will show all songs instead of 0.
- [Songs] Added opener/closer count to table
- [Setlist] Fixed double single quotes in song names. `"I''ve Been Everywhere" -> "I've Been Everywhere".`
- [Event Detail] Fixed onstage "note" column not showing notes
- [Songs] Fixed songs page search not searching song name and not showing certain songs.
- [Event Detail] Fixed gap calculation counting cancelled/postponed events.
- [Event Detail] Added "rumored" event type for events that were only rumored to have happened. This may be extended to events with little evidence that they happened.
- [Home Page] Readded the "upcoming events" table
- [Event Detail] Tweaked the font size/spacing on the album breakdown card
- [Home Page] Upcoming events card now includes current date when listing events
- [Home Page] Fixed updates "new band" broken link
- [Home Page] Fixed image having bottom rounded corners
- [City Search] Fixed bug where cities without states wouldn't show in results
- [Search] Updated search to ignore accented characters in query
- Added "Events by Type" page
- [Song Detail] Last Played now shows "latest event" instead of "0 show gap"
- [Event Calendar] Past releases now show on calendar, they appear as a no fill orange box compared to the filled orange box for new releases.
- [Band Detail] Added event count badge
- [Relation Detail] Added event count badge
- [Home Page] New home page image
- [Relation Detail] Born/Died now shows for many relations, least those with known birthdays.
- [Venue Detail] Added leaflet.js map to venue detail page. Most venues have addresses/coords, with those up through E having been manually checked.
- [Event Calendar] Added many birthdays to event calendar. Only those who've been a member of one of Bruce's bands are shown.
- [User Profile] Redesigned page slightly
- [User Profile] Added "albums" tab, which shows every studio album and the songs seen by the user
- [Band Detail] Fixed members event link not linking to event
- [General] Updated page titles and descriptions so that many show on opengraph embeds

# v1.16 (April 2026)

- [Fix] Fixed issues with signup and user adding shows
- [New Page] Added "News" page, which is basically a site blog
- [Style] Colors changed slightly. Badge/Button colors slightly different
- [Style] Light/Dark Theme Colors Updated Slightly
- [Style] Numerous style tweaks, using some elements from Hummingbird as I think it looks nicer.
- [Update] Cleaned up several API views, faster response on many
- [Home Page] Changed rendering of Upcoming/Recent/OTD Tables, no longer using Datatables.
- [Event Tables] Changed setlist icon to checkmark, removed true/false text
- [Band Detail] Added "note" card
- [Release Detail] Moved most items to cards
- [Song Detail] Updated year stats to pull from API
- [Releases] Fixed length not showing on table
- [Profile] Added count badge to nav tab buttons
- [Event Detail] Added "set times" card. This will show start/end time and duration of event if known. Times are shown in local time.
- [Event Detail] Link buttons now centered and evenly spaced
- [Event Detail] Album Breakdown no longer uses Datatables
- [Advanced Search] City search now shows country if no state
- [Advanced Search] Fixed issue where quotes in IDs would cause error
- [Blog Posts] Added `magnific-popup` to blog posts, images now have the same popup as my Github Pages site

# v1.17 (June 2026)

- 1 Year of Databruce!, Site first went public on June 10, 2025 in beta, and July fully public.
- [Song Detail] Fixed year stats bar chart not scaling properly with window
- [Song Detail] Updated layout of position cards, text now wraps
- [Event Detail] Adjusted event table column widths
- [User Profile] Added info row cards to user profile, removed from navigation buttons. Counts are done in views instead of tied to datatables
- [Event Detail] Added user list on hover to attended button
- [Adv. Search] Fixed advanced search control spacing on mobile being busted
- [General] General code cleanup, removed some unnecessary code to reduce queries
- [User Profile] Added "change password" section
- [User Profile] Added "discord name" to user profiles. Can be used in conjunction with Brucebot to display your own stats or another users stats.
- [Event Detail] Updated setlist positions. Originally had them set semi-automatically, but found it was too much of a mess. With many positions being wrong (marking show opener/closer when Bruce only appeared for 2 songs mid-set). These are now set manually.
- [Event Detail] Added "Event Info" card. Extended info about event that doesn't fit in header. Currently it is a current event num/total for tour, leg, and venue. More will likely be added eventually.
- [General] Fixed spacing on navbar login button
- Add custom 404 page.
- Add custom 500 page, also has link to contact and email if needed.
- [Events] Fix issue where the "year" filter accepted any value rather than complete years.
- [Venues] Fixed venue name/detail being wrong way around on many venues
- [Venue Detail] Moved address to map tab
- [Venue Detail] Added "Same Address As" to note card, lists venues at the same physical location.
- [Venues] Added "child venues". Venues that are all at the same "location" (like studios at Rockerfeller Plaze, or different places on a college campus like Monmouth).
- [Venue Detail] Events are now listed for that venue AND any child venues.
- [Event Detail] Badge added to mark top 10 longest shows.

# v1.17.1 (June 16, 2026)

- Fixed issue where profiles with no events would cause an error when attempting to view profile page.
- Fixed Advanced Search Song dropdown not including original artist. So "Fire (Jimi Hendrix)" and "Fire (Bruce Springsteen)" would show up as the same "Fire".

# v1.18 (July 6, 2026)

- [User] Signup now requires answering a verification question.
- [Event Detail] Minor page redesign, header updated date/artist to be bigger size while shrinking venue/city. Very much inspired by WTED Archives.
- [Event Detail] New "Stats" tab. Show stats like venue/tour/tour leg/etc have been moved from overview sidebar to here. Stats tab layout inspired by speedrun.org.
- Box Office Data is now part of Databruce! This data was manually compiled from Billboard Magazine and Pollstar Magazine. Events now have how many tickets sold, min/max price, price range and promoter company. If an event is part of a "run", then the data is a aggregrate of all shows on the run. The data pulled gives info on shows from 1976 up through 2026. 2023-26 had to be pulled from "touringdata.org", and doesn't list ticket prices. Pre-1976 data doesn't seem to have been published anywhere.
- [Event Detail] Album cover images now show in-place of their names on the album breakdown. The list of songs will also show on hover as well. Clicking will still expand a list like before. Idea borrowed from Dripfield.pro.
- [Event Detail] Album breakdown now changes the progress bar color if the album is "complete" at a show. I couldn't have both the album image AND the complete badge without the layout breaking.
- [Event Detail] Updated "show times" card. This contains the scheduled time (from ticket stub), actual start/end time if known, and show length (dependent on the previous being present). Times were pulled from ticket stubs sourced from Brucebase, and are shown in venue local time. To speed up the process, AI was used to first OCR the stub images to extract the times. This data was then reviewed and corrected manually before being inserted into the database.

# v1.18.1 (July 15, 2026)

- Cleaned up API code. Reduced response size and as a result many pages have seen improvements in API
- Songs Snippet Tab now shows setlist notes
- Card Header tabs have been redesigned to no longer use buttons but tabs
- Album Breakdown will no longer mark an album as "complete" if all songs present but NOT in sequential order.
- Event Table now shows city/state under venue name
- Event Table now shows Tour Leg under Tour name
- Added setlist image generation to Event Details page under the "Setlist Options". This will generate an image of the setlist and show info and prompt you to download. Image generation is done entirely in browser, and *should* work on most browsers. Consider this to be a beta addition for the time being.
- Fixed event search not returning correct results for date only.

# v1.18.2 (July 17, 2026)

- All Datatables have had their controls replaced with custom controls for filtering/search.
  - DTs built-in controls are inflexible and hard to work with. They can't be easily styled or moved, and often don't respond well to different screen sizes. Additionally adding new filters/controls is a PITA with how DT handles them.
  - Replacing them with custom fields gives me more flexibility. I can style them how I want, place them wherever, and have much more control over their functionality.
- The "page length" dropdown has been removed. All tables default to 50 rows now, which is great for nearly every table minus the larger song/location tables.
- In addition to the event tables having a "publicity" filter, other tables have gotten similar dropdowns as well. More will likely be added over time.
  - Song tables have an Original/Cover songs filter dropdown
  - Tours can now show/hide all the "Misc" tours
  - Bootlegs can filter recording type (AUD/SBD)
- Nearly all of the event/song tables have been simplified, consolidating all of them into functions with common settings. Makes it much easier to work with.
- Fixed the "included songs" table on the song detail page. It was working but not finding all songs and only showing a count of 1 regardless of the actual number.
- Event Table publicity filter now orders by event date before searching
- Update table filters to sort table before applying filter.
