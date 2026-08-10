# databruce - Data Dictionary

Commit `17f408623f48929941b2df0bbec7527dcec83a93`

---

## Table of Contents [#](#toc)

- [Table of Contents](#toc)
- [Modules](#modules)
  - [admin](#admin)
    - [LogEntry](#logentry)
  - [auth](#auth)
    - [Permission](#permission)
    - [Group](#group)
  - [contenttypes](#contenttypes)
    - [ContentType](#contenttype)
  - [sessions](#sessions)
    - [Session](#session)
  - [databruce](#databruce)
    - [CustomUser](#customuser)
    - [ArchiveLinks](#archivelinks)
    - [Bands](#bands)
    - [Bootlegs](#bootlegs)
    - [Cities](#cities)
    - [Continents](#continents)
    - [Countries](#countries)
    - [Covers](#covers)
    - [States](#states)
    - [Venues](#venues)
    - [VenuesText](#venuestext)
    - [VenueAliases](#venuealiases)
    - [Events](#events)
    - [NugsReleases](#nugsreleases)
    - [Relations](#relations)
    - [RelationAliases](#relationaliases)
    - [Onstage](#onstage)
    - [ReleaseTracks](#releasetracks)
    - [Releases](#releases)
    - [SetlistNotes](#setlistnotes)
    - [Songs](#songs)
    - [Setlists](#setlists)
    - [SetlistsBySetAndDate](#setlistsbysetanddate)
    - [Snippets](#snippets)
    - [Tours](#tours)
    - [TourLegs](#tourlegs)
    - [Runs](#runs)
    - [EventRankStat](#eventrankstat)
    - [StudioSessions](#studiosessions)
    - [UserAttendedShows](#userattendedshows)
    - [Guests](#guests)
    - [Lyrics](#lyrics)
    - [Updates](#updates)
    - [SiteUpdates](#siteupdates)
    - [OnstageBandMembers](#onstagebandmembers)
    - [ReleaseDiscs](#releasediscs)
    - [SetlistEntries](#setlistentries)
    - [Notes](#notes)
    - [Contact](#contact)
    - [TourCount](#tourcount)
    - [SetlistPositions](#setlistpositions)
    - [SongsPage](#songspage)
    - [SetlistStats](#setliststats)
    - [EventTypes](#eventtypes)
    - [BlogCategory](#blogcategory)
    - [BlogTags](#blogtags)
    - [BlogPosts](#blogposts)
    - [BlogPostTags](#blogposttags)
    - [BlogPostCategories](#blogpostcategories)
    - [BlogAuthors](#blogauthors)
    - [Tags](#tags)
    - [EventTags](#eventtags)
  - [sites](#sites)
    - [Site](#site)
  - [shortener](#shortener)
    - [UrlMap](#urlmap)
    - [UrlProfile](#urlprofile)

---

## Modules [#](#modules)

### admin

#### LogEntry[#](#logentry)

`LogEntry(id, action_time, user, content_type, object_id, object_repr, action_flag, change_message)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  |  |  |  |  |
|  | action_time | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | user_id | `bigint` | [CustomUser](#customuser) |  |  |  |  |  | ✓ |
|  | content_type_id | `integer` | [ContentType](#contenttype) |  | ✓ |  |  |  | ✓ |
|  | object_id | `text` |  |  | ✓ |  |  |  |  |
|  | object_repr | `varchar` |  |  |  |  |  | 200 |  |
|  | action_flag | `smallint` |  |  |  |  |  |  |  |
|  | change_message | `text` |  |  |  |  |  |  |  |

### auth

#### Permission[#](#permission)

`Permission(id, name, content_type, codename)`

The permissions system provides a way to assign permissions to specific
    users and groups of users.

    The permission system is used by the Django admin site, but may also be
    useful in your own code. The Django admin site uses permissions as follows:

        - The "add" permission limits the user's ability to view the "add" form
          and add an object.
        - The "change" permission limits a user's ability to view the change
          list, view the "change" form and change an object.
        - The "delete" permission limits the ability to delete an object.
        - The "view" permission limits the ability to view an object.

    Permissions are set globally per type of object, not per specific object
    instance. It is possible to say "Mary may change news stories," but it's
    not currently possible to say "Mary may change news stories, but only the
    ones she created herself" or "Mary may only change news stories that have a
    certain status or publication date."

    The permissions listed above are automatically created for each model.

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  |  |  |  |  |
|  | name | `varchar` |  |  |  |  |  | 255 |  |
|  | content_type_id | `integer` | [ContentType](#contenttype) |  |  |  |  |  | ✓ |
|  | codename | `varchar` |  |  |  |  |  | 100 |  |

#### Group[#](#group)

`Group(id, name)`

Groups are a generic way of categorizing users to apply permissions, or
    some other label, to those users. A user can belong to any number of
    groups.

    A user in a group automatically has all the permissions granted to that
    group. For example, if the group 'Site editors' has the permission
    can_edit_home_page, any user in that group will have that permission.

    Beyond permissions, groups are a convenient way to categorize users to
    apply some label, or extended functionality, to them. For example, you
    could create a group 'Special users', and you could write code that would
    do special things to those users -- such as giving them access to a
    members-only portion of your site, or sending them members-only email
    messages.

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  |  |  |  |  |
|  | name | `varchar` |  |  |  |  |  | 150 |  |

### contenttypes

#### ContentType[#](#contenttype)

`ContentType(id, app_label, model)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  | ✓ |  |  |  |
|  | app_label | `varchar` |  |  |  |  |  | 100 |  |
|  | model | `varchar` |  |  |  |  |  | 100 |  |

### sessions

#### Session[#](#session)

`Session(session_key, session_data, expire_date)`

Django provides full support for anonymous sessions. The session
    framework lets you store and retrieve arbitrary data on a
    per-site-visitor basis. It stores data on the server side and
    abstracts the sending and receiving of cookies. Cookies contain a
    session ID -- not the data itself.

    The Django sessions framework is entirely cookie-based. It does
    not fall back to putting session IDs in URLs. This is an intentional
    design decision. Not only does that behavior make URLs ugly, it makes
    your site vulnerable to session-ID theft via the "Referer" header.

    For complete documentation on using Sessions in your code, consult
    the sessions documentation that is shipped with Django (also available
    on the Django web site).

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | session_key | `varchar` |  |  |  |  |  | 40 |  |
|  | session_data | `text` |  |  |  |  |  |  |  |
|  | expire_date | `timestamp with time zone` |  |  |  |  |  |  | ✓ |

### databruce

#### CustomUser[#](#customuser)

`CustomUser(id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined, uuid, discord_name)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `bigint` |  |  |  | ✓ |  |  |  |
|  | password | `varchar` |  |  |  |  |  | 128 |  |
|  | last_login | `timestamp with time zone` |  |  | ✓ |  |  |  |  |
|  | is_superuser | `boolean` |  | Designates that this user has all permissions without explicitly assigning them. |  |  |  |  |  |
|  | username | `varchar` |  | Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only. |  | ✓ |  | 150 |  |
|  | first_name | `varchar` |  |  |  |  |  | 150 |  |
|  | last_name | `varchar` |  |  |  |  |  | 150 |  |
|  | email | `varchar` |  |  |  |  |  | 254 |  |
|  | is_staff | `boolean` |  | Designates whether the user can log into this admin site. |  |  |  |  |  |
|  | is_active | `boolean` |  | Designates whether this user should be treated as active. Unselect this instead of deleting accounts. |  |  |  |  |  |
|  | date_joined | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | uuid | `uuid` |  |  |  |  |  | 32 |  |
|  | discord_name | `text` |  |  | ✓ |  |  |  |  |

#### ArchiveLinks[#](#archivelinks)

`ArchiveLinks(created_at, updated_at, id, uuid, event, url)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  | ✓ |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | uuid | `uuid` |  |  |  |  |  | 32 |  |
|  | event_id | `integer` | [Events](#events) |  | ✓ |  |  |  | ✓ |
|  | url | `text` |  |  |  |  |  |  |  |

#### Bands[#](#bands)

`Bands(created_at, updated_at, id, uuid, brucebase_url, name, num_events, first_event, last_event, springsteen_band, mbid, note)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  | ✓ |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | uuid | `uuid` |  |  |  |  |  | 32 |  |
|  | brucebase_url | `text` |  |  | ✓ |  |  |  |  |
|  | name | `text` |  |  | ✓ |  |  |  |  |
|  | num_events | `integer` |  |  |  |  |  |  |  |
|  | first_event_id | `integer` | [Events](#events) |  | ✓ |  |  |  | ✓ |
|  | last_event_id | `integer` | [Events](#events) |  | ✓ |  |  |  | ✓ |
|  | springsteen_band | `boolean` |  |  |  |  |  |  |  |
|  | mbid | `uuid` |  |  | ✓ |  |  | 32 |  |
|  | note | `text` |  |  | ✓ |  |  |  |  |

#### Bootlegs[#](#bootlegs)

`Bootlegs(created_at, updated_at, id, uuid, slid, mbid, event, category, title, label, source, source_info, version_info, transfer, editor, type, catalog_number, media_type, has_info, has_artwork, archive)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  |  |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | uuid | `uuid` |  |  |  |  |  | 32 |  |
|  | slid | `integer` |  |  |  |  |  |  |  |
|  | mbid | `uuid` |  |  | ✓ |  |  | 32 |  |
|  | event_id | `integer` | [Events](#events) |  |  |  |  |  | ✓ |
|  | category | `text` |  |  | ✓ |  |  |  |  |
|  | title | `text` |  |  | ✓ |  |  |  |  |
|  | label | `text` |  |  | ✓ |  |  |  |  |
|  | source | `text` |  |  | ✓ |  |  |  |  |
|  | source_info | `text` |  |  | ✓ |  |  |  |  |
|  | version_info | `text` |  |  | ✓ |  |  |  |  |
|  | transfer | `text` |  |  | ✓ |  |  |  |  |
|  | editor | `text` |  |  | ✓ |  |  |  |  |
|  | type | `text` |  |  | ✓ |  |  |  |  |
|  | catalog_number | `text` |  |  | ✓ |  |  |  |  |
|  | media_type | `text` |  |  | ✓ |  |  |  |  |
|  | has_info | `boolean` |  |  |  |  |  |  |  |
|  | has_artwork | `boolean` |  |  |  |  |  |  |  |
|  | archive_id | `integer` | [ArchiveLinks](#archivelinks) |  |  |  |  |  | ✓ |

#### Cities[#](#cities)

`Cities(created_at, updated_at, id, uuid, mbid, name, state, country, num_events, aliases, first_event, last_event, timezone)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  | ✓ |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | uuid | `uuid` |  |  |  |  |  | 32 |  |
|  | mbid | `uuid` |  |  | ✓ |  |  | 32 |  |
|  | name | `text` |  |  |  |  |  |  |  |
|  | state_id | `integer` | [States](#states) |  | ✓ |  |  |  | ✓ |
|  | country_id | `integer` | [Countries](#countries) |  | ✓ |  |  |  | ✓ |
|  | num_events | `integer` |  |  |  |  |  |  |  |
|  | aliases | `text` |  |  | ✓ |  |  |  |  |
|  | first_event_id | `integer` | [Events](#events) |  | ✓ |  |  |  | ✓ |
|  | last_event_id | `integer` | [Events](#events) |  | ✓ |  |  |  | ✓ |
|  | timezone | `varchar` |  |  |  |  |  | 63 |  |

#### Continents[#](#continents)

`Continents(created_at, updated_at, id, uuid, name, num_events)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  | ✓ |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | uuid | `uuid` |  |  |  |  |  | 32 |  |
|  | name | `text` |  |  |  |  |  |  |  |
|  | num_events | `integer` |  |  |  |  |  |  |  |

#### Countries[#](#countries)

`Countries(created_at, updated_at, id, uuid, name, num_events, continent, alpha_2, aliases, mbid, first_event, last_event)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  | ✓ |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | uuid | `uuid` |  |  |  |  |  | 32 |  |
|  | name | `text` |  |  |  |  |  |  |  |
|  | num_events | `integer` |  |  |  |  |  |  |  |
|  | continent_id | `integer` | [Continents](#continents) |  | ✓ |  |  |  | ✓ |
|  | alpha_2 | `text` |  |  |  |  |  | 2 |  |
|  | aliases | `text` |  |  | ✓ |  |  |  |  |
|  | mbid | `uuid` |  |  | ✓ |  |  | 32 |  |
|  | first_event_id | `integer` | [Events](#events) |  | ✓ |  |  |  | ✓ |
|  | last_event_id | `integer` | [Events](#events) |  | ✓ |  |  |  | ✓ |

#### Covers[#](#covers)

`Covers(created_at, updated_at, id, uuid, event_date, url, event)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  |  |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | uuid | `uuid` |  |  |  |  |  | 32 |  |
|  | event_date | `text` |  |  | ✓ |  |  |  |  |
|  | url | `text` |  |  |  |  |  |  |  |
|  | event_id | `integer` | [Events](#events) |  |  |  |  |  | ✓ |

#### States[#](#states)

`States(created_at, updated_at, id, uuid, abbrev, name, country, num_events, mbid, first_event, last_event)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  | ✓ |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | uuid | `uuid` |  |  |  |  |  | 32 |  |
|  | abbrev | `text` |  |  |  |  |  |  |  |
|  | name | `text` |  |  | ✓ |  |  |  |  |
|  | country_id | `integer` | [Countries](#countries) |  |  |  |  |  | ✓ |
|  | num_events | `integer` |  |  |  |  |  |  |  |
|  | mbid | `uuid` |  |  | ✓ |  |  | 32 |  |
|  | first_event_id | `integer` | [Events](#events) |  | ✓ |  |  |  | ✓ |
|  | last_event_id | `integer` | [Events](#events) |  | ✓ |  |  |  | ✓ |

#### Venues[#](#venues)

`Venues(created_at, updated_at, id, uuid, brucebase_url, name, detail, city, num_events, note, mbid, first_event, last_event, address, latitude, longitude, parent)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  | ✓ |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | uuid | `uuid` |  |  |  |  |  | 32 |  |
|  | brucebase_url | `text` |  |  | ✓ |  |  |  |  |
|  | name | `text` |  |  |  |  |  |  |  |
|  | detail | `text` |  |  | ✓ |  |  |  |  |
|  | city_id | `integer` | [Cities](#cities) |  | ✓ |  |  |  | ✓ |
|  | num_events | `integer` |  |  |  |  |  |  |  |
|  | note | `text` |  |  | ✓ |  |  |  |  |
|  | mbid | `uuid` |  |  | ✓ |  |  | 32 |  |
|  | first_event_id | `integer` | [Events](#events) |  | ✓ |  |  |  | ✓ |
|  | last_event_id | `integer` | [Events](#events) |  | ✓ |  |  |  | ✓ |
|  | address | `text` |  |  |  |  |  |  |  |
|  | latitude | `numeric` |  |  | ✓ |  |  |  |  |
|  | longitude | `numeric` |  |  | ✓ |  |  |  |  |
|  | parent_id | `integer` | [Venues](#venues) |  | ✓ |  |  |  | ✓ |

#### VenuesText[#](#venuestext)

`VenuesText(id, location, formatted)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id_id | `integer` | [Venues](#venues) |  |  |  |  |  | ✓ |
|  | location | `text` |  |  |  |  |  |  |  |
|  | formatted | `text` |  |  |  |  |  |  |  |

#### VenueAliases[#](#venuealiases)

`VenueAliases(created_at, updated_at, id, uuid, venue, name, note)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  |  |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | uuid | `uuid` |  |  |  |  |  | 32 |  |
|  | venue_id | `integer` | [Venues](#venues) |  | ✓ |  |  |  | ✓ |
|  | name | `text` |  |  |  |  |  |  |  |
|  | note | `text` |  |  |  |  |  |  |  |

#### Events[#](#events)

`Events(created_at, updated_at, id, num, event_id, date, uuid, early_late, public, artist, brucebase_url, venue, tour, leg, run, type, title, event_certainty, setlist_certainty, note, summary, bootleg, is_stats_eligible, official, nugs, start_time, end_time, scheduled_time, length, sales, capacity, gross, ticket_min, ticket_max, box_office_source, box_office_note, sellout, ticket_range, promo_company)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  | ✓ |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | num | `integer` |  |  | ✓ |  |  |  |  |
|  | event_id | `varchar` |  |  |  | ✓ |  | 11 |  |
|  | date | `date` |  |  |  |  |  |  |  |
|  | uuid | `uuid` |  |  |  |  |  | 32 |  |
|  | early_late | `varchar` |  |  | ✓ |  |  |  |  |
|  | public | `boolean` |  |  |  |  |  |  |  |
|  | artist_id | `integer` | [Bands](#bands) |  |  |  |  |  | ✓ |
|  | brucebase_url | `text` |  |  | ✓ |  |  |  |  |
|  | venue_id | `integer` | [Venues](#venues) |  |  |  |  |  | ✓ |
|  | tour_id | `integer` | [Tours](#tours) |  |  |  |  |  | ✓ |
|  | leg_id | `integer` | [TourLegs](#tourlegs) |  | ✓ |  |  |  | ✓ |
|  | run_id | `integer` | [Runs](#runs) |  | ✓ |  |  |  | ✓ |
|  | type_id | `integer` | [EventTypes](#eventtypes) |  | ✓ |  |  |  | ✓ |
|  | title | `varchar` |  |  | ✓ |  |  |  |  |
|  | event_certainty | `varchar` |  |  | ✓ |  |  |  |  |
|  | setlist_certainty | `varchar` |  |  | ✓ |  |  |  |  |
|  | note | `text` |  |  | ✓ |  |  |  |  |
|  | summary | `varchar` |  |  |  |  |  | 255 |  |
|  | bootleg | `boolean` |  |  |  |  |  |  |  |
|  | is_stats_eligible | `boolean` |  |  |  |  |  |  |  |
|  | official_id | `integer` | [Releases](#releases) |  | ✓ |  |  |  | ✓ |
|  | nugs_id | `integer` | [NugsReleases](#nugsreleases) |  | ✓ |  |  |  | ✓ |
|  | start_time | `timestamp with time zone` |  |  | ✓ |  |  |  |  |
|  | end_time | `timestamp with time zone` |  |  | ✓ |  |  |  |  |
|  | scheduled_time | `timestamp with time zone` |  |  | ✓ |  |  |  |  |
|  | length | `time` |  |  | ✓ |  |  |  |  |
|  | sales | `bigint` |  |  | ✓ |  |  |  |  |
|  | capacity | `bigint` |  |  | ✓ |  |  |  |  |
|  | gross | `bigint` |  |  | ✓ |  |  |  |  |
|  | ticket_min | `numeric` |  |  | ✓ |  |  |  |  |
|  | ticket_max | `numeric` |  |  | ✓ |  |  |  |  |
|  | box_office_source | `text` |  |  | ✓ |  |  |  |  |
|  | box_office_note | `text` |  |  | ✓ |  |  |  |  |
|  | sellout | `boolean` |  |  | ✓ |  |  |  |  |
|  | ticket_range | `text` |  |  | ✓ |  |  |  |  |
|  | promo_company | `text` |  |  | ✓ |  |  |  |  |

#### NugsReleases[#](#nugsreleases)

`NugsReleases(created_at, updated_at, id, uuid, nugs_id, event, date, url, thumbnail, name, first_friday)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  | ✓ |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | uuid | `uuid` |  |  |  |  |  | 32 |  |
|  | nugs_id | `integer` |  |  |  |  |  |  |  |
|  | event_id | `integer` | [Events](#events) |  |  |  |  |  | ✓ |
|  | date | `timestamp with time zone` |  |  | ✓ |  |  |  |  |
|  | url | `text` |  |  |  |  |  |  |  |
|  | thumbnail | `text` |  |  |  |  |  |  |  |
|  | name | `text` |  |  | ✓ |  |  |  |  |
|  | first_friday | `boolean` |  |  |  |  |  |  |  |

#### Relations[#](#relations)

`Relations(created_at, updated_at, id, uuid, mbid, brucebase_url, name, appearances, first_event, last_event, instruments, start_date, end_date, show_cal)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  | ✓ |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | uuid | `uuid` |  |  |  |  |  | 32 |  |
|  | mbid | `uuid` |  |  | ✓ |  |  | 32 |  |
|  | brucebase_url | `text` |  |  | ✓ |  |  |  |  |
|  | name | `text` |  |  | ✓ |  |  |  |  |
|  | appearances | `integer` |  |  |  |  |  |  |  |
|  | first_event_id | `integer` | [Events](#events) |  | ✓ |  |  |  | ✓ |
|  | last_event_id | `integer` | [Events](#events) |  | ✓ |  |  |  | ✓ |
|  | instruments | `text` |  |  | ✓ |  |  |  |  |
|  | start_date | `date` |  |  |  |  |  |  |  |
|  | end_date | `date` |  |  |  |  |  |  |  |
|  | show_cal | `boolean` |  |  |  |  |  |  |  |

#### RelationAliases[#](#relationaliases)

`RelationAliases(created_at, updated_at, id, relation, name, type)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `uuid` |  |  |  |  |  | 32 |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | relation_id | `integer` | [Relations](#relations) |  | ✓ |  |  |  | ✓ |
|  | name | `text` |  |  |  |  |  |  |  |
|  | type | `text` |  |  |  |  |  |  |  |

#### Onstage[#](#onstage)

`Onstage(created_at, updated_at, id, uuid, event, relation, band, note, guest)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  |  |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | uuid | `uuid` |  |  |  |  |  | 32 |  |
|  | event_id | `integer` | [Events](#events) |  |  |  |  |  | ✓ |
|  | relation_id | `integer` | [Relations](#relations) |  |  |  |  |  | ✓ |
|  | band_id | `integer` | [Bands](#bands) |  |  |  |  |  | ✓ |
|  | note | `text` |  |  | ✓ |  |  |  |  |
|  | guest | `boolean` |  |  |  |  |  |  |  |

#### ReleaseTracks[#](#releasetracks)

`ReleaseTracks(created_at, updated_at, id, uuid, release, discnum, disc, track, position, song, event, note, setlist, length)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  |  |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | uuid | `uuid` |  |  |  |  |  | 32 |  |
|  | release_id | `integer` | [Releases](#releases) |  |  |  |  |  | ✓ |
|  | discnum | `integer` |  |  |  |  |  |  |  |
|  | disc_id | `uuid` | [ReleaseDiscs](#releasediscs) |  | ✓ |  |  |  | ✓ |
|  | track | `varchar` |  |  |  |  |  | 255 |  |
|  | position | `integer` |  |  |  |  |  |  |  |
|  | song_id | `integer` | [Songs](#songs) |  |  |  |  |  | ✓ |
|  | event_id | `integer` | [Events](#events) |  | ✓ |  |  |  | ✓ |
|  | note | `text` |  |  | ✓ |  |  |  |  |
|  | setlist_id | `integer` | [Setlists](#setlists) |  |  |  |  |  | ✓ |
|  | length | `time` |  |  |  |  |  |  |  |

#### Releases[#](#releases)

`Releases(created_at, updated_at, id, uuid, brucebase_id, name, length, spotify_link, type, format, date, short_name, thumb, note, mbid, event)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  | ✓ |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | uuid | `uuid` |  |  |  |  |  | 32 |  |
|  | brucebase_id | `text` |  |  | ✓ |  |  |  |  |
|  | name | `text` |  |  | ✓ |  |  |  |  |
|  | length | `time` |  |  |  |  |  |  |  |
|  | spotify_link | `text` |  |  | ✓ |  |  |  |  |
|  | type | `varchar` |  |  |  |  |  | 50 |  |
|  | format | `varchar` |  |  |  |  |  | 50 |  |
|  | date | `date` |  |  |  |  |  |  |  |
|  | short_name | `text` |  |  | ✓ |  |  |  |  |
|  | thumb | `text` |  |  | ✓ |  |  |  |  |
|  | note | `text` |  |  | ✓ |  |  |  |  |
|  | mbid | `uuid` |  |  | ✓ |  |  | 32 |  |
|  | event_id | `integer` | [Events](#events) |  | ✓ |  |  |  | ✓ |

#### SetlistNotes[#](#setlistnotes)

`SetlistNotes(setlist, event, num, note)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | setlist_id | `integer` | [Setlists](#setlists) |  |  | ✓ |  |  | ✓ |
|  | event_id | `integer` | [Events](#events) |  |  |  |  |  | ✓ |
|  | num | `integer` |  |  |  |  |  |  |  |
|  | note | `text` |  |  | ✓ |  |  |  |  |

#### Songs[#](#songs)

`Songs(created_at, updated_at, id, uuid, brucebase_url, name, short_name, slug, first_event, last_event, num_plays_public, num_plays_private, num_plays_snippet, opener, closer, sniponly, original_artist, original, lyrics, category, category_slug, spotify_id, mbid, length, album, aliases, sort_song_name)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  | ✓ |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | uuid | `uuid` |  |  |  |  |  | 32 |  |
|  | brucebase_url | `text` |  |  | ✓ |  |  |  |  |
|  | name | `text` |  |  |  |  |  |  |  |
|  | short_name | `text` |  |  | ✓ |  |  |  |  |
|  | slug | `text` |  |  | ✓ |  |  |  |  |
|  | first_event_id | `integer` | [Events](#events) |  | ✓ |  |  |  | ✓ |
|  | last_event_id | `integer` | [Events](#events) |  | ✓ |  |  |  | ✓ |
|  | num_plays_public | `integer` |  |  |  |  |  |  |  |
|  | num_plays_private | `integer` |  |  |  |  |  |  |  |
|  | num_plays_snippet | `integer` |  |  |  |  |  |  |  |
|  | opener | `integer` |  |  |  |  |  |  |  |
|  | closer | `integer` |  |  |  |  |  |  |  |
|  | sniponly | `integer` |  |  |  |  |  |  |  |
|  | original_artist | `text` |  |  | ✓ |  |  |  |  |
|  | original | `boolean` |  |  |  |  |  |  |  |
|  | lyrics | `boolean` |  |  |  |  |  |  |  |
|  | category | `text` |  |  | ✓ |  |  |  |  |
|  | category_slug | `text` |  |  | ✓ |  |  |  |  |
|  | spotify_id | `text` |  |  | ✓ |  |  |  |  |
|  | mbid | `uuid` |  |  | ✓ |  |  | 32 |  |
|  | length | `time` |  |  | ✓ |  |  |  |  |
|  | album_id | `integer` | [Releases](#releases) |  | ✓ |  |  |  | ✓ |
|  | aliases | `text` |  |  | ✓ |  |  |  |  |
|  | sort_song_name | `text` |  |  |  |  |  |  |  |

#### Setlists[#](#setlists)

`Setlists(created_at, updated_at, id, uuid, event, set_name, song_num, song, note, segue, premiere, debut, instrumental, nobruce, position, last, next, tour_num, tour_total, ltp, sign_request, is_opener, is_closer, is_set_opener, is_set_closer, is_last_in_show, is_main_set_closer)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  | ✓ |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | uuid | `uuid` |  |  |  |  |  | 32 |  |
|  | event_id | `integer` | [Events](#events) |  |  |  |  |  | ✓ |
|  | set_name | `varchar` |  |  |  |  |  | 50 |  |
|  | song_num | `integer` |  |  | ✓ |  |  |  |  |
|  | song_id | `integer` | [Songs](#songs) |  |  |  |  |  | ✓ |
|  | note | `text` |  |  |  |  |  |  |  |
|  | segue | `boolean` |  |  |  |  |  |  |  |
|  | premiere | `boolean` |  |  |  |  |  |  |  |
|  | debut | `boolean` |  |  |  |  |  |  |  |
|  | instrumental | `boolean` |  |  |  |  |  |  |  |
|  | nobruce | `boolean` |  |  |  |  |  |  |  |
|  | position | `varchar` |  |  | ✓ |  |  | 50 |  |
|  | last | `integer` |  |  |  |  |  |  |  |
|  | next | `integer` |  |  |  |  |  |  |  |
|  | tour_num | `integer` |  |  |  |  |  |  |  |
|  | tour_total | `integer` |  |  |  |  |  |  |  |
|  | ltp_id | `integer` | [Events](#events) |  | ✓ |  |  |  | ✓ |
|  | sign_request | `boolean` |  |  |  |  |  |  |  |
|  | is_opener | `boolean` |  |  |  |  |  |  |  |
|  | is_closer | `boolean` |  |  |  |  |  |  |  |
|  | is_set_opener | `boolean` |  |  |  |  |  |  |  |
|  | is_set_closer | `boolean` |  |  |  |  |  |  |  |
|  | is_last_in_show | `boolean` |  |  |  |  |  |  |  |
|  | is_main_set_closer | `boolean` |  |  |  |  |  |  |  |

#### SetlistsBySetAndDate[#](#setlistsbysetanddate)

`SetlistsBySetAndDate(id, set_order, event, set_name, setlist, setlist_no_note)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  |  |  |  |  |
|  | set_order | `integer` |  |  |  |  |  |  |  |
|  | event_id | `integer` | [Events](#events) |  |  |  |  |  | ✓ |
|  | set_name | `text` |  |  | ✓ |  |  |  |  |
|  | setlist | `text` |  |  | ✓ |  |  |  |  |
|  | setlist_no_note | `text` |  |  | ✓ |  |  |  |  |

#### Snippets[#](#snippets)

`Snippets(created_at, updated_at, id, uuid, setlist, snippet, position, note)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  |  |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | uuid | `uuid` |  |  |  |  |  | 32 |  |
|  | setlist_id | `integer` | [Setlists](#setlists) |  |  |  |  |  | ✓ |
|  | snippet_id | `integer` | [Songs](#songs) |  |  |  |  |  | ✓ |
|  | position | `integer` |  |  |  |  |  |  |  |
|  | note | `text` |  |  | ✓ |  |  |  |  |

#### Tours[#](#tours)

`Tours(created_at, updated_at, id, uuid, brucebase_id, brucebase_tag, band, name, slug, note, first_event, last_event, num_shows, num_songs, num_legs)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  | ✓ |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | uuid | `uuid` |  |  |  |  |  | 32 |  |
|  | brucebase_id | `text` |  |  | ✓ |  |  |  |  |
|  | brucebase_tag | `text` |  |  | ✓ |  |  |  |  |
|  | band_id | `integer` | [Bands](#bands) |  | ✓ |  |  |  | ✓ |
|  | name | `text` |  |  |  |  |  |  |  |
|  | slug | `text` |  |  | ✓ |  |  |  |  |
|  | note | `text` |  |  | ✓ |  |  |  |  |
|  | first_event_id | `integer` | [Events](#events) |  | ✓ |  |  |  | ✓ |
|  | last_event_id | `integer` | [Events](#events) |  | ✓ |  |  |  | ✓ |
|  | num_shows | `integer` |  |  |  |  |  |  |  |
|  | num_songs | `integer` |  |  |  |  |  |  |  |
|  | num_legs | `integer` |  |  |  |  |  |  |  |

#### TourLegs[#](#tourlegs)

`TourLegs(created_at, updated_at, id, uuid, tour, name, first_event, last_event, num_shows, num_songs, note)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  | ✓ |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | uuid | `uuid` |  |  |  |  |  | 32 |  |
|  | tour_id | `integer` | [Tours](#tours) |  |  |  |  |  | ✓ |
|  | name | `text` |  |  | ✓ |  |  |  |  |
|  | first_event_id | `integer` | [Events](#events) |  |  |  |  |  | ✓ |
|  | last_event_id | `integer` | [Events](#events) |  |  |  |  |  | ✓ |
|  | num_shows | `integer` |  |  |  |  |  |  |  |
|  | num_songs | `integer` |  |  |  |  |  |  |  |
|  | note | `text` |  |  | ✓ |  |  |  |  |

#### Runs[#](#runs)

`Runs(created_at, updated_at, id, uuid, band, venue, name, num_shows, num_songs, first_event, last_event, note, total_sales, total_capacity, total_gross, ticket_min, ticket_max, ticket_range, box_office_source, box_office_note, sellout, promo_company, num_sellout)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  | ✓ |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | uuid | `uuid` |  |  |  |  |  | 32 |  |
|  | band_id | `integer` | [Bands](#bands) |  | ✓ |  |  |  | ✓ |
|  | venue_id | `integer` | [Venues](#venues) |  | ✓ |  |  |  | ✓ |
|  | name | `text` |  |  |  |  |  | 255 |  |
|  | num_shows | `integer` |  |  | ✓ |  |  |  |  |
|  | num_songs | `integer` |  |  | ✓ |  |  |  |  |
|  | first_event_id | `integer` | [Events](#events) |  | ✓ |  |  |  | ✓ |
|  | last_event_id | `integer` | [Events](#events) |  | ✓ |  |  |  | ✓ |
|  | note | `text` |  |  | ✓ |  |  |  |  |
|  | total_sales | `integer` |  |  |  |  |  |  |  |
|  | total_capacity | `integer` |  |  |  |  |  |  |  |
|  | total_gross | `bigint` |  |  |  |  |  |  |  |
|  | ticket_min | `numeric` |  |  | ✓ |  |  |  |  |
|  | ticket_max | `numeric` |  |  | ✓ |  |  |  |  |
|  | ticket_range | `text` |  |  |  |  |  |  |  |
|  | box_office_source | `text` |  |  |  |  |  |  |  |
|  | box_office_note | `text` |  |  |  |  |  |  |  |
|  | sellout | `boolean` |  |  |  |  |  |  |  |
|  | promo_company | `text` |  |  |  |  |  |  |  |
|  | num_sellout | `integer` |  |  |  |  |  |  |  |

#### EventRankStat[#](#eventrankstat)

`EventRankStat(event, tour_num, tour_total, tour_leg_num, tour_leg_total, run_num, run_total, venue_num, venue_total, city_num, city_total, length_rank)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | event_id | `integer` | [Events](#events) |  |  |  |  |  | ✓ |
|  | tour_num | `integer` |  |  |  |  |  |  |  |
|  | tour_total | `integer` |  |  |  |  |  |  |  |
|  | tour_leg_num | `integer` |  |  |  |  |  |  |  |
|  | tour_leg_total | `integer` |  |  |  |  |  |  |  |
|  | run_num | `integer` |  |  |  |  |  |  |  |
|  | run_total | `integer` |  |  |  |  |  |  |  |
|  | venue_num | `integer` |  |  |  |  |  |  |  |
|  | venue_total | `integer` |  |  |  |  |  |  |  |
|  | city_num | `integer` |  |  |  |  |  |  |  |
|  | city_total | `integer` |  |  |  |  |  |  |  |
|  | length_rank | `integer` |  |  |  |  |  |  |  |

#### StudioSessions[#](#studiosessions)

`StudioSessions(created_at, updated_at, id, uuid, band, name, num_events, num_songs, first_event, last_event, release)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  |  |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | uuid | `uuid` |  |  |  |  |  | 32 |  |
|  | band_id | `integer` | [Bands](#bands) |  | ✓ |  |  |  | ✓ |
|  | name | `text` |  |  |  |  |  |  |  |
|  | num_events | `integer` |  |  |  |  |  |  |  |
|  | num_songs | `integer` |  |  | ✓ |  |  |  |  |
|  | first_event_id | `integer` | [Events](#events) |  | ✓ |  |  |  | ✓ |
|  | last_event_id | `integer` | [Events](#events) |  | ✓ |  |  |  | ✓ |
|  | release_id | `integer` | [Releases](#releases) |  | ✓ |  |  |  | ✓ |

#### UserAttendedShows[#](#userattendedshows)

`UserAttendedShows(created_at, updated_at, id, uuid, user, event)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  |  |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | uuid | `uuid` |  |  |  |  |  | 32 |  |
|  | user_id | `bigint` | [CustomUser](#customuser) |  |  |  |  |  | ✓ |
|  | event_id | `integer` | [Events](#events) |  |  |  |  |  | ✓ |

#### Guests[#](#guests)

`Guests(created_at, updated_at, id, uuid, setlist, guest, note)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  |  |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | uuid | `uuid` |  |  |  |  |  | 32 |  |
|  | setlist_id | `integer` | [Setlists](#setlists) |  |  |  |  |  | ✓ |
|  | guest_id | `integer` | [Relations](#relations) |  |  |  |  |  | ✓ |
|  | note | `text` |  |  | ✓ |  |  |  |  |

#### Lyrics[#](#lyrics)

`Lyrics(created_at, updated_at, id, uuid, song, version, num, source, text, language, note, translator)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  |  |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | uuid | `uuid` |  |  |  |  |  | 32 |  |
|  | song_id | `integer` | [Songs](#songs) |  | ✓ |  |  |  | ✓ |
|  | version | `text` |  |  | ✓ |  |  |  |  |
|  | num | `text` |  |  |  |  |  |  |  |
|  | source | `text` |  |  | ✓ |  |  |  |  |
|  | text | `text` |  |  |  |  |  |  |  |
|  | language | `text` |  |  | ✓ |  |  |  |  |
|  | note | `text` |  |  | ✓ |  |  |  |  |
|  | translator | `text` |  |  | ✓ |  |  |  |  |

#### Updates[#](#updates)

`Updates(id, item_id, item, value, view, msg, created_at)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  |  |  |  |  |
|  | item_id | `text` |  |  |  |  |  |  |  |
|  | item | `text` |  |  |  |  |  |  |  |
|  | value | `text` |  |  |  |  |  |  |  |
|  | view | `text` |  |  |  |  |  |  |  |
|  | msg | `text` |  |  |  |  |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  |  |

#### SiteUpdates[#](#siteupdates)

`SiteUpdates(created_at, updated_at, id, description, uuid)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  |  |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | description | `text` |  |  |  |  |  |  |  |
|  | uuid | `uuid` |  |  |  |  |  | 32 |  |

#### OnstageBandMembers[#](#onstagebandmembers)

`OnstageBandMembers(id, relation, band, count, first, last)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  |  |  |  |  |
|  | relation_id | `integer` | [Relations](#relations) |  |  |  |  |  | ✓ |
|  | band_id | `integer` | [Bands](#bands) |  |  |  |  |  | ✓ |
|  | count | `integer` |  |  |  |  |  |  |  |
|  | first_id | `integer` | [Events](#events) |  |  |  |  |  | ✓ |
|  | last_id | `integer` | [Events](#events) |  |  |  |  |  | ✓ |

#### ReleaseDiscs[#](#releasediscs)

`ReleaseDiscs(created_at, id, release, disc_num, name, uuid, updated_at)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  |  |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | release_id | `integer` | [Releases](#releases) |  |  |  |  |  | ✓ |
|  | disc_num | `integer` |  |  |  |  |  |  |  |
|  | name | `text` |  |  |  |  |  |  |  |
|  | uuid | `uuid` |  |  |  | ✓ |  | 32 |  |
|  | updated_at | `timestamp with time zone` |  |  | ✓ |  |  |  |  |

#### SetlistEntries[#](#setlistentries)

`SetlistEntries(id, event, show_opener, s1_closer, s2_opener, main_closer, encore_opener, show_closer)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  |  |  |  |  |
|  | event_id | `integer` | [Events](#events) |  |  |  |  |  | ✓ |
|  | show_opener_id | `integer` | [Songs](#songs) |  |  |  |  |  | ✓ |
|  | s1_closer_id | `integer` | [Songs](#songs) |  |  |  |  |  | ✓ |
|  | s2_opener_id | `integer` | [Songs](#songs) |  |  |  |  |  | ✓ |
|  | main_closer_id | `integer` | [Songs](#songs) |  |  |  |  |  | ✓ |
|  | encore_opener_id | `integer` | [Songs](#songs) |  |  |  |  |  | ✓ |
|  | show_closer_id | `integer` | [Songs](#songs) |  |  |  |  |  | ✓ |

#### Notes[#](#notes)

`Notes(created_at, id, event, num, note, gap, last, last_date, uuid, updated_at, setlist)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  |  |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | event_id | `integer` | [Events](#events) |  |  |  |  |  | ✓ |
|  | num | `integer` |  |  |  |  |  |  |  |
|  | note | `text` |  |  |  |  |  |  |  |
|  | gap | `text` |  |  |  |  |  |  |  |
|  | last | `text` |  |  |  |  |  |  |  |
|  | last_date | `text` |  |  |  |  |  |  |  |
|  | uuid | `uuid` |  |  |  |  |  | 32 |  |
|  | updated_at | `timestamp with time zone` |  |  | ✓ |  |  |  |  |
|  | setlist_id | `integer` | [Setlists](#setlists) |  |  |  |  |  | ✓ |

#### Contact[#](#contact)

`Contact(created_at, updated_at, id, email, is_user, subject, message)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  |  |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | email | `varchar` |  |  |  |  |  | 254 |  |
|  | is_user | `boolean` |  |  |  |  |  |  |  |
|  | subject | `varchar` |  |  |  |  |  | 50 |  |
|  | message | `text` |  |  |  |  |  |  |  |

#### TourCount[#](#tourcount)

`TourCount(setlist, num, total)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | setlist_id | `integer` | [Setlists](#setlists) |  |  |  |  |  | ✓ |
|  | num | `integer` |  |  |  |  |  |  |  |
|  | total | `integer` |  |  |  |  |  |  |  |

#### SetlistPositions[#](#setlistpositions)

`SetlistPositions(id, position)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id_id | `integer` | [Setlists](#setlists) |  |  |  |  |  | ✓ |
|  | position | `text` |  |  |  |  |  |  |  |

#### SongsPage[#](#songspage)

`SongsPage(id, prev, next)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id_id | `integer` | [Setlists](#setlists) | | | ✓ | | | ✓ |
| | prev_id | `integer` | [Setlists](#setlists) | | ✓ | | | | ✓ |
| | next_id | `integer` | [Setlists](#setlists) | | ✓ | | | | ✓ |

#### SetlistStats[#](#setliststats)

`SetlistStats(setlist, song_num, set_name, event, total_event_songs, global_first, global_last, set_first, set_last, is_the_main_closer, show_has_encore, gap, ltp, premiere, debut, band_premiere, tour_num, tour_total)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | setlist_id | `integer` | [Setlists](#setlists) |  |  | ✓ |  |  | ✓ |
|  | song_num | `integer` |  |  |  |  |  |  |  |
|  | set_name | `text` |  |  |  |  |  |  |  |
|  | event_id | `integer` | [Events](#events) |  | ✓ |  |  |  | ✓ |
|  | total_event_songs | `integer` |  |  |  |  |  |  |  |
|  | global_first | `boolean` |  |  |  |  |  |  |  |
|  | global_last | `boolean` |  |  |  |  |  |  |  |
|  | set_first | `boolean` |  |  |  |  |  |  |  |
|  | set_last | `boolean` |  |  |  |  |  |  |  |
|  | is_the_main_closer | `boolean` |  |  |  |  |  |  |  |
|  | show_has_encore | `boolean` |  |  |  |  |  |  |  |
|  | gap | `integer` |  |  |  |  |  |  |  |
|  | ltp_id | `integer` | [Events](#events) |  | ✓ |  |  |  | ✓ |
|  | premiere | `boolean` |  |  |  |  |  |  |  |
|  | debut | `boolean` |  |  |  |  |  |  |  |
|  | band_premiere | `boolean` |  |  | ✓ |  |  |  |  |
|  | tour_num | `integer` |  |  |  |  |  |  |  |
|  | tour_total | `integer` |  |  |  |  |  |  |  |

#### EventTypes[#](#eventtypes)

`EventTypes(created_at, updated_at, id, name, slug, uuid)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  | ✓ |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | name | `text` |  |  |  |  |  |  |  |
|  | slug | `text` |  |  |  |  |  |  |  |
|  | uuid | `uuid` |  |  |  |  |  | 32 |  |

#### BlogCategory[#](#blogcategory)

`BlogCategory(id, name, slug, uuid, created_at, updated_at)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  | ✓ |  |  |  |
|  | name | `varchar` |  |  |  |  |  | 100 |  |
|  | slug | `varchar` |  |  |  |  |  | 50 | ✓ |
|  | uuid | `uuid` |  |  |  |  |  | 32 |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |

#### BlogTags[#](#blogtags)

`BlogTags(created_at, updated_at, id, name, slug)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  | ✓ |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | name | `varchar` |  |  |  |  |  | 100 |  |
|  | slug | `varchar` |  |  |  |  |  | 50 | ✓ |

#### BlogPosts[#](#blogposts)

`BlogPosts(created_at, updated_at, id, title, slug, author, body, excerpt, published, published_at)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  | ✓ |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | title | `varchar` |  |  |  |  |  | 255 |  |
|  | slug | `varchar` |  |  |  |  |  | 50 | ✓ |
|  | author_id | `bigint` | [CustomUser](#customuser) |  |  |  |  |  | ✓ |
|  | body | `text` |  |  |  |  |  |  |  |
|  | excerpt | `varchar` |  |  |  |  |  | 255 |  |
|  | published | `boolean` |  |  |  |  |  |  |  |
|  | published_at | `timestamp with time zone` |  |  | ✓ |  |  |  |  |

#### BlogPostTags[#](#blogposttags)

`BlogPostTags(id, post, tag)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `bigint` |  |  |  |  |  |  |  |
|  | post_id | `integer` | [BlogPosts](#blogposts) |  |  |  |  |  | ✓ |
|  | tag_id | `integer` | [BlogTags](#blogtags) |  |  |  |  |  | ✓ |

#### BlogPostCategories[#](#blogpostcategories)

`BlogPostCategories(id, post, category)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `bigint` |  |  |  |  |  |  |  |
|  | post_id | `integer` | [BlogPosts](#blogposts) |  |  |  |  |  | ✓ |
|  | category_id | `integer` | [BlogCategory](#blogcategory) |  |  |  |  |  | ✓ |

#### BlogAuthors[#](#blogauthors)

`BlogAuthors(id, created_at, updated_at, author, uuid)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `bigint` |  |  |  |  |  |  |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  | ✓ |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | author_id | `bigint` | [CustomUser](#customuser) |  |  |  |  |  | ✓ |
|  | uuid | `uuid` |  |  |  |  |  | 32 |  |

#### Tags[#](#tags)

`Tags(id, name, slug, uuid, created_at, updated_at)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  | ✓ |  |  |  |
|  | name | `text` |  |  |  |  |  |  |  |
|  | slug | `text` |  |  | ✓ |  |  |  |  |
|  | uuid | `uuid` |  |  |  |  |  | 32 |  |
|  | created_at | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | updated_at | `timestamp with time zone` |  |  |  |  |  |  |  |

#### EventTags[#](#eventtags)

`EventTags(id, event, tag)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  |  |  |  |  |
|  | event_id | `integer` | [Events](#events) |  |  |  |  |  | ✓ |
|  | tag_id | `integer` | [Tags](#tags) |  |  |  |  |  | ✓ |

### sites

#### Site[#](#site)

`Site(id, domain, name)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `integer` |  |  |  |  |  |  |  |
|  | domain | `varchar` |  |  |  |  |  | 100 |  |
|  | name | `varchar` |  |  |  |  |  | 50 |  |

### shortener

#### UrlMap[#](#urlmap)

`UrlMap(id, user, full_url, short_url, usage_count, max_count, lifespan, date_created, date_expired)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `bigint` |  |  |  |  |  |  |  |
|  | user_id | `bigint` | [CustomUser](#customuser) |  |  |  |  |  | ✓ |
|  | full_url | `text` |  |  |  |  |  |  |  |
|  | short_url | `varchar` |  |  |  |  |  | 50 | ✓ |
|  | usage_count | `integer` |  |  |  |  |  |  |  |
|  | max_count | `integer` |  |  |  |  |  |  |  |
|  | lifespan | `integer` |  |  |  |  |  |  |  |
|  | date_created | `timestamp with time zone` |  |  |  |  |  |  |  |
|  | date_expired | `timestamp with time zone` |  |  |  |  |  |  |  |

#### UrlProfile[#](#urlprofile)

`UrlProfile(id, user, enabled, max_urls, max_concurrent_urls, default_lifespan, default_max_uses)`

| pk | field_name | data_type | related_model | description | nullable | unique | choices | max_length | db_index |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ✓ | id | `bigint` |  |  |  |  |  |  |  |
|  | user_id | `bigint` | [CustomUser](#customuser) |  |  |  |  |  | ✓ |
|  | enabled | `boolean` |  |  | ✓ |  |  |  |  |
|  | max_urls | `integer` |  |  | ✓ |  |  |  |  |
|  | max_concurrent_urls | `integer` |  |  | ✓ |  |  |  |  |
|  | default_lifespan | `integer` |  |  | ✓ |  |  |  |  |
|  | default_max_uses | `integer` |  |  | ✓ |  |  |  |  |
