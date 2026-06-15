# test_runner.py
from django.db import connection
from django.test.runner import DiscoverRunner


class PostgresViewTestRunner(DiscoverRunner):
    def setup_databases(self, **kwargs):
        # 1. Let Django build the standard tables first
        config = super().setup_databases(**kwargs)

        # 2. Inject the Materialized View schema right into the test database
        print("\n🔨 Creating test database materialized views...")
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE MATERIALIZED VIEW "public".venues_text AS
                WITH
                aliases AS (
                    SELECT
                    v.venue_id,
                    string_agg(v.name, ', '::text) AS alias_list
                    FROM
                    venue_aliases v
                    GROUP BY
                    v.venue_id
                ),
                base_data AS (
                    SELECT
                    v.id,
                    v.name,
                    v.detail,
                    c.name AS city,
                    s.name AS state,
                    s.state_abbrev,
                    c1.name AS country,
                    c1.alpha_2 AS country_abbrev,
                    count(DISTINCT e.id) AS event_count,
                    concat_ws(
                        ', '::text,
                        NULLIF(v.detail, ''::text),
                        v.name,
                        c.name
                    ) AS location,
                    CASE
                        WHEN min(c1.id) = ANY (ARRAY[2, 6, 37]) THEN concat_ws(
                        ', '::text,
                        NULLIF(v.detail, ''::text),
                        v.name,
                        c.name,
                        s.state_abbrev
                        )
                        ELSE concat_ws(
                        ', '::text,
                        NULLIF(v.detail, ''::text),
                        v.name,
                        c.name,
                        c1.name
                        )
                    END AS full_location,
                    COALESCE(v1.alias_list, ''::text) AS aliases,
                    COALESCE(min(e.event_date::text), NULL::text) AS first_event_date,
                    COALESCE(max(e.event_date::text), NULL::text) AS last_event_date,
                    min(e.event_id) AS first_event_id,
                    max(e.event_id) AS last_event_id
                    FROM
                    venues v
                    LEFT JOIN aliases v1 ON v1.venue_id = v.id
                    LEFT JOIN events e ON e.venue_id = v.id
                    LEFT JOIN cities c ON c.id = v.city
                    LEFT JOIN states s ON s.id = c.state
                    LEFT JOIN countries c1 ON c1.id = c.country
                    GROUP BY
                    v.id,
                    v.name,
                    v.detail,
                    c.name,
                    s.name,
                    s.state_abbrev,
                    c1.name,
                    c1.alpha_2,
                    (COALESCE(v1.alias_list, ''::text))
                    ORDER BY
                    v.id
                )
                SELECT
                id,
                name,
                detail,
                city,
                state,
                state_abbrev,
                country,
                country_abbrev,
                event_count,
                location,
                full_location,
                aliases,
                first_event_date,
                last_event_date,
                first_event_id,
                last_event_id
                FROM
                base_data;
            """)

        return config
