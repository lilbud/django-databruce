Note: While I have posted updates in various places, I've never compiled them together like this. This is a somewhat broad overview of changes to the site. The version numbers are largely arbitrary, and definitely don't follow "best practices". This is being written well after the fact, and the numbers are just to mark progress.

I had intended to create "releases" on Github, but you can't easily backdate them. And this really isn't a project with "releases", so it wouldn't make sense.

# v0.1 (June 10, 2025)
First beta release of Databruce. Site was opened to a small group to test and give feedback.

# v0.1.1 (June 11, 2025)
- Added "users" page
- Added ability for users to change username/email
- Added "latest show" card to front page

# v0.1.2 (June 14, 2025)
- User Profile Updates
	- "Rare Songs" (<100 total plays) added
	- "Personal Premieres" added
	- "Most Played Not Seen" added
- Tour Detail page now shows songs in a given position (Opener/Closer)

# v1.0 (July 15, 2025)
First public release of the site. Site was locked behind a login and accounts only I could make while beta testing was underway. Had to get an email provider set up to send confirmation emails
- Event page style changes to look better on mobile
- Added autocomplete to navbar event search

# v1.0.1 (July 18, 2025)
- Login now redirects to previous page rather than home page

# v1.0.2 (July 21, 2025)
- Date filtering added to tables
- Advanced Search form improved on mobile
- Added short url creation to advanced search (thanks to Jerrybase for the idea)
- General layout changes
- Added About page

# v1.0.3 (August 26, 2025)
- Fixed "On This Day" home page card not updating with current date

# v1.0.4 (September 3, 2025)
- Updated Song page layout
- Updated Event page layout
- Updated Events page
- Rewrote About page

# v1.0.5 (September 8, 2025)
- Added "tour" column to event page
- Added colored markers to event setlist page to indicate "position" (show opener, show closer, etc.)

# v1.0.6 (October 25, 2025)
- Song Detail page loads faster
- Style changes, largely to "standardize" everything
- Added "Synthwave" theme from DaisyUI
- Added "Setlist Options" to Event Detail page, contained toggle to show/hide all setlist notes, as well as button to copy setlist as plain text.

# v1.1.0 (December 3, 2025)
- Added "Event Calendar" page, shows events and runs in a more visual manner
- Synthwave theme removed, wasn't a fan of it
- Added regex support to Table Search
- Tables are now responsive on mobile, putting everything in a child row instead of requiring horizontal scroll
- Release Detail page now groups tracks by disc

# v1.1.1 (December 8, 2025)
- Updated Event Detail, songs in setlist are now highlighted when hovering over an album in the "breakdown" card. (Credit to Dripfield.pro)
- Fixed Event Detail showing "null" for some gaps due to some shows not being counted
- Updated Event Detail layout, setlist card is wider
