"""
Seed script for populating restaurants, menu categories, and menu items from CSV files.

Usage (run inside Docker container):
    docker compose -p nextgencater -f docker-compose.full.yml exec search-service python scripts/seed_data.py
"""
import asyncio
import csv
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional
from uuid import UUID

# Add /app to Python path so we can import shared modules
sys.path.insert(0, "/app")

import asyncpg
import os

# CSV file paths - CSV files are in seed-data directory within search-service
CSV_BASE_PATH = Path("/app/seed-data")
RESTAURANTS_CSV = CSV_BASE_PATH / "df_restaurants.csv"
MENU_CATEGORIES_CSV = CSV_BASE_PATH / "df_menu_categories.csv"
MENU_ITEMS_CSV = CSV_BASE_PATH / "df_menuitems.csv"


def parse_price(price_str: str) -> float:
    """Parse price string like '$2.19' to float."""
    if not price_str:
        return 0.0
    # Remove $ and commas, convert to float
    cleaned = price_str.replace("$", "").replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def parse_search_keywords(keywords_str: str) -> List[str]:
    """Parse search keywords from string representation of list."""
    if not keywords_str or keywords_str == "nan":
        return []
    try:
        # Handle string like "['word1', 'word2']"
        keywords_str = keywords_str.strip()
        if keywords_str.startswith("[") and keywords_str.endswith("]"):
            # Remove brackets and parse
            inner = keywords_str[1:-1]
            # Split by comma and clean
            keywords = [k.strip().strip("'\"") for k in inner.split(",")]
            return [k for k in keywords if k]
        return []
    except Exception:
        return []


def parse_list_field(value: str) -> List[str]:
    """Parse list field from CSV (handles string representation of lists)."""
    if not value or value == "nan" or value.strip() == "":
        return []
    try:
        # Handle string like "['dairy']" or "['halal']"
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1]
            items = [item.strip().strip("'\"") for item in inner.split(",")]
            return [item for item in items if item]
        return []
    except Exception:
        return []


def parse_json_field(value: str) -> Optional[Dict]:
    """Parse JSON field from CSV."""
    if not value or value == "nan" or value.strip() == "":
        return None
    try:
        # Handle empty dict string "{}"
        if value.strip() == "{}":
            return {}
        # Try to parse as JSON
        return json.loads(value)
    except Exception:
        return None


def parse_address(address_str: str, lat: float, lng: float) -> Dict:
    """Parse address string into structured format."""
    # Simple parsing - can be enhanced
    parts = address_str.split(",")
    return {
        "street": parts[0].strip() if len(parts) > 0 else "",
        "city": parts[1].strip() if len(parts) > 1 else "",
        "state": parts[2].strip() if len(parts) > 2 else "",
        "zip": parts[3].strip() if len(parts) > 3 else "",
        "country": "USA",
        "lat": float(lat) if lat else None,
        "lng": float(lng) if lng else None,
    }


def generate_slug(name: str) -> str:
    """Generate URL-friendly slug from restaurant name."""
    slug = name.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = re.sub(r"^-+|-+$", "", slug)
    return slug


async def seed_restaurants(conn: asyncpg.Connection) -> Dict[str, UUID]:
    """Seed restaurants from CSV and return mapping of restaurant_id -> UUID."""
    print("📦 Seeding restaurants...")
    restaurant_map: Dict[str, UUID] = {}

    with open(RESTAURANTS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        restaurants = []
        for row in reader:
            restaurant_id_str = row["restaurant_id"]
            name = row["name"]
            description = row.get("description", "")
            address_str = row.get("address", "")
            image_url = row.get("image_url", "")
            lat = float(row.get("latitude", 0)) if row.get("latitude") else None
            lng = float(row.get("longitude", 0)) if row.get("longitude") else None

            # Generate slug
            slug = generate_slug(name)

            # Parse address
            address = parse_address(address_str, lat, lng)

            # Extract cuisine types from description (simple heuristic)
            cuisine_types = []
            if "Italian" in description or "Pizza" in description or "Pasta" in description:
                cuisine_types.append("Italian")
            if "Indian" in description or "Curry" in description:
                cuisine_types.append("Indian")
            if "Mexican" in description or "Taco" in description:
                cuisine_types.append("Mexican")
            if "Chinese" in description or "Asian" in description:
                cuisine_types.append("Chinese")
            if "American" in description or "Burger" in description:
                cuisine_types.append("American")
            if not cuisine_types:
                cuisine_types = ["American"]  # Default

            restaurant_uuid = UUID(restaurant_id_str)
            restaurant_map[restaurant_id_str] = restaurant_uuid

            restaurants.append(
                {
                    "id": restaurant_uuid,
                    "name": name,
                    "slug": slug,
                    "description": description or None,
                    "cuisine_types": cuisine_types,
                    "status": "active",
                    "owner_email": f"owner-{slug}@example.com",
                    "address": json.dumps(address),
                    "cover_image_url": image_url or None,
                    "operating_hours": json.dumps({}),
                    "delivery_zones": json.dumps([]),
                    "minimum_order_amount": 0.00,
                    "delivery_fee": 0.00,
                }
            )

        # Bulk insert restaurants
        if restaurants:
            await conn.executemany(
                """
                INSERT INTO restaurants (
                    id, name, slug, description, cuisine_types, status, owner_email,
                    address, cover_image_url, operating_hours, delivery_zones,
                    minimum_order_amount, delivery_fee, rating_average, rating_count, onboarding_status
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16
                ) ON CONFLICT (id) DO NOTHING
                """,
                [
                    (
                        r["id"],
                        r["name"],
                        r["slug"],
                        r["description"],
                        r["cuisine_types"],
                        r["status"],
                        r["owner_email"],
                        r["address"],
                        r["cover_image_url"],
                        r["operating_hours"],
                        r["delivery_zones"],
                        r["minimum_order_amount"],
                        r["delivery_fee"],
                        0.00,  # rating_average default
                        0,     # rating_count default
                        "completed",  # onboarding_status default
                    )
                    for r in restaurants
                ],
            )
            # After inserting restaurants, backfill the PostGIS location column from address JSON
            await conn.execute(
                """
                UPDATE restaurants
                SET location = ST_SetSRID(
                    ST_MakePoint(
                        (address->>'lng')::double precision,
                        (address->>'lat')::double precision
                    ),
                    4326
                )
                WHERE location IS NULL
                  AND (address::jsonb) ? 'lat'
                  AND (address::jsonb) ? 'lng'
                  AND (address->>'lat') IS NOT NULL
                  AND (address->>'lng') IS NOT NULL;
                """
            )
        print(f"✅ Inserted {len(restaurants)} restaurants")

    return restaurant_map


async def seed_menu_categories(
    conn: asyncpg.Connection, restaurant_map: Dict[str, UUID]
) -> Dict[str, UUID]:
    """Seed menu categories and return mapping of (restaurant_id, category_name) -> UUID."""
    print("📦 Seeding menu categories...")
    category_map: Dict[str, UUID] = {}

    with open(MENU_CATEGORIES_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        categories = []
        for row in reader:
            restaurant_id_str = row["restaurant_id"]
            name = row["name"]

            restaurant_uuid = restaurant_map.get(restaurant_id_str)
            if not restaurant_uuid:
                continue  # Skip if restaurant not found

            # Generate deterministic UUID for category based on restaurant_id and name
            from uuid import uuid5, NAMESPACE_DNS
            category_uuid = uuid5(NAMESPACE_DNS, f"{restaurant_id_str}-{name}")
            
            # Create a composite key for mapping: restaurant_id:category_name
            category_key = f"{restaurant_id_str}:{name}"
            category_map[category_key] = category_uuid

            categories.append(
                {
                    "id": category_uuid,
                    "restaurant_id": restaurant_uuid,
                    "name": name,
                    "display_order": 0,
                    "is_active": True,
                    "menu_type": "regular",
                }
            )

    # Bulk insert categories
    if categories:
        await conn.executemany(
            """
            INSERT INTO menu_categories (
                id, restaurant_id, name, display_order, is_active, menu_type
            ) VALUES ($1, $2, $3, $4, $5, $6) ON CONFLICT (id) DO NOTHING
            """,
            [
                (
                    c["id"],
                    c["restaurant_id"],
                    c["name"],
                    c["display_order"],
                    c["is_active"],
                    c["menu_type"],
                )
                for c in categories
            ],
        )
        print(f"✅ Inserted {len(categories)} menu categories")

    return category_map


async def seed_menu_items(
    conn: asyncpg.Connection,
    restaurant_map: Dict[str, UUID],
    category_map: Dict[str, UUID],
) -> None:
    """Seed menu items."""
    print("📦 Seeding menu items...")

    with open(MENU_ITEMS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        menu_items = []
        for row in reader:
            restaurant_id_str = row["restaurant_id"]
            category_id_str = row.get("category_id", "")
            name = row["name"]
            description = row.get("description", "")
            price_str = row.get("price", "0")
            image_url = row.get("image_url", "")
            category = row.get("category", "")
            search_keywords_str = row.get("search_keywords", "")
            # Parse rating_average safely
            rating_avg = 0.0
            try:
                rating_avg_str = row.get("rating_average", "")
                if rating_avg_str and rating_avg_str != "nan" and rating_avg_str.strip():
                    rating_avg = float(rating_avg_str)
            except (ValueError, TypeError):
                rating_avg = 0.0

            # Parse rating_count safely
            rating_count = 0
            try:
                rating_count_str = row.get("rating_count", "")
                if rating_count_str and rating_count_str != "nan" and rating_count_str.strip():
                    rating_count = int(float(rating_count_str))  # Handle float strings like "566.0"
            except (ValueError, TypeError):
                rating_count = 0
            menu_type = row.get("menu_type", "regular")

            # Parse allergens, dietary_tags, and nutritional_info from CSV
            allergens = parse_list_field(row.get("allergens", ""))
            dietary_tags = parse_list_field(row.get("dietary_tags", ""))
            nutritional_info = parse_json_field(row.get("nutritional_info", ""))

            # Handle cuisine_type - add it to tags since it's not in the schema
            cuisine_type = row.get("cuisine_type", "").strip()
            tags = []
            if cuisine_type and cuisine_type != "nan" and cuisine_type.lower() != "unknown":
                tags.append(f"cuisine:{cuisine_type.lower()}")  # Store as "cuisine:asian", "cuisine:fast food", etc.

            restaurant_uuid = restaurant_map.get(restaurant_id_str)
            if not restaurant_uuid:
                continue  # Skip if restaurant not found

            # Look up category by category_id from CSV, or by restaurant_id:category_name if category_id not available
            category_uuid = None
            if category_id_str:
                # Try to find category by the category_id from menu items CSV
                # Since categories CSV doesn't have category_id, we need to match by restaurant_id and category name
                category_name = row.get("category", "")
                if category_name:
                    category_key = f"{restaurant_id_str}:{category_name}"
                    category_uuid = category_map.get(category_key)

            price = parse_price(price_str)
            search_keywords = parse_search_keywords(search_keywords_str)

            # Generate UUID for menu item (or use a deterministic one if needed)
            from uuid import uuid5, NAMESPACE_DNS

            menu_item_id = uuid5(NAMESPACE_DNS, f"{restaurant_id_str}-{name}-{category}")

            menu_items.append(
                {
                    "id": menu_item_id,
                    "restaurant_id": restaurant_uuid,
                    "category_id": category_uuid,
                    "name": name,
                    "description": description or None,
                    "price": price,
                    "image_url": image_url or None,
                    "category": category or None,
                    "dietary_tags": dietary_tags,  # Now reading from CSV
                    "allergens": allergens,  # Now reading from CSV
                    "spice_level": 0,
                    "is_available": True,
                    "minimum_quantity": 1,
                    "tags": tags,  # Now includes cuisine_type
                    "search_keywords": search_keywords,
                    "rating_average": rating_avg,
                    "rating_count": rating_count,
                    "order_count": 0,
                    "menu_type": menu_type,
                    "nutritional_info": nutritional_info,  # Now reading from CSV
                }
            )

    # Bulk insert menu items (in batches to avoid memory issues)
    batch_size = 500
    total_inserted = 0
    for i in range(0, len(menu_items), batch_size):
        batch = menu_items[i : i + batch_size]
        await conn.executemany(
            """
            INSERT INTO menu_items (
                id, restaurant_id, category_id, name, description, price, image_url,
                category, dietary_tags, allergens, spice_level, is_available,
                minimum_quantity, tags, search_keywords, rating_average, rating_count,
                order_count, menu_type, nutritional_info
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20
            ) ON CONFLICT (id) DO NOTHING
            """,
            [
                (
                    m["id"],
                    m["restaurant_id"],
                    m["category_id"],
                    m["name"],
                    m["description"],
                    m["price"],
                    m["image_url"],
                    m["category"],
                    m["dietary_tags"],
                    m["allergens"],
                    m["spice_level"],
                    m["is_available"],
                    m["minimum_quantity"],
                    m["tags"],
                    m["search_keywords"],
                    m["rating_average"],
                    m["rating_count"],
                    m["order_count"],
                    m["menu_type"],
                    json.dumps(m["nutritional_info"]) if m["nutritional_info"] else None,  # Convert dict to JSON string
                )
                for m in batch
            ],
        )
        total_inserted += len(batch)
        print(f"  Inserted batch {i // batch_size + 1}: {len(batch)} items")

    print(f"✅ Inserted {total_inserted} menu items")


async def main():
    """Main seeding function."""
    database_url = os.environ.get("DATABASE_URL", "postgresql://postgres:password@localhost:5432/smart_food")

    # Connect to database
    print(f"🔌 Connecting to database...")
    conn = await asyncpg.connect(database_url)

    try:
        # Check if data already exists
        count = await conn.fetchval("SELECT COUNT(*) FROM restaurants")
        if count > 0:
            print(f"⚠️  Database already contains {count} restaurants.")
            # For non-interactive mode, skip if data exists
            # Uncomment below to force re-seed:
            # print("⚠️  Clearing existing data...")
            # await conn.execute("TRUNCATE TABLE menu_items, menu_categories, restaurants CASCADE")
            print("ℹ️  To re-seed, truncate tables first or use --force flag (not implemented yet)")
            return

        # Seed in order: restaurants -> categories -> items
        restaurant_map = await seed_restaurants(conn)
        category_map = await seed_menu_categories(conn, restaurant_map)
        await seed_menu_items(conn, restaurant_map, category_map)

        print("\n✅ Seeding completed successfully!")

    except Exception as e:
        print(f"❌ Error during seeding: {e}", file=sys.stderr)
        raise
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())

