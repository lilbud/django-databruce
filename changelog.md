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
- [Event Detail] Added "set times" card. This will show start/end time and duration of event if known. Times are shown in local time. "Scheduled" time will show for future events.
- [Band Detail] Added "note" card
- Added "News" page, which is basically a site blog
- Fixed many issues with signup and user adding shows