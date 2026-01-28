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

# v1.14 (February XX, 2026)
- (1/28) Song Detail: fix frequency causing "divide by zero" error when there are no events
- (1/28) Events: "setlist" is now an annotated calculated value instead of a stored value