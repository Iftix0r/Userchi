import aiosqlite
from config import DB_PATH


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS keywords (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword  TEXT UNIQUE NOT NULL,
                kw_type  TEXT NOT NULL DEFAULT 'yolovchi',
                added_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS monitored_groups (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id   INTEGER UNIQUE NOT NULL,
                group_name TEXT,
                added_by   INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT
            );
        """)
        # migration: add kw_type to existing databases
        try:
            await db.execute("ALTER TABLE keywords ADD COLUMN kw_type TEXT NOT NULL DEFAULT 'yolovchi'")
            await db.commit()
        except Exception:
            pass


# ── Keywords ──────────────────────────────────────────────────────────────────

async def get_keywords(kw_type: str | None = None) -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        if kw_type:
            async with db.execute(
                "SELECT keyword FROM keywords WHERE kw_type = ? ORDER BY keyword", (kw_type,)
            ) as cur:
                return [r[0] for r in await cur.fetchall()]
        async with db.execute("SELECT keyword FROM keywords ORDER BY keyword") as cur:
            return [r[0] for r in await cur.fetchall()]


async def add_keyword(keyword: str, added_by: int, kw_type: str = "yolovchi") -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                "INSERT INTO keywords (keyword, kw_type, added_by) VALUES (?, ?, ?)",
                (keyword.lower().strip(), kw_type, added_by),
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False


async def delete_keyword(keyword: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "DELETE FROM keywords WHERE keyword = ?", (keyword.lower().strip(),)
        )
        await db.commit()
        return cur.rowcount > 0


# ── Monitored groups ──────────────────────────────────────────────────────────

async def get_monitored_groups() -> list[tuple[int, str]]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT group_id, group_name FROM monitored_groups ORDER BY group_name"
        ) as cur:
            return await cur.fetchall()


async def add_monitored_group(group_id: int, group_name: str, added_by: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                "INSERT INTO monitored_groups (group_id, group_name, added_by) VALUES (?, ?, ?)",
                (group_id, group_name, added_by),
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False


async def remove_monitored_group(group_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "DELETE FROM monitored_groups WHERE group_id = ?", (group_id,)
        )
        await db.commit()
        return cur.rowcount > 0


# ── Settings ──────────────────────────────────────────────────────────────────

async def get_setting(key: str, default: str | None = None) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT value FROM settings WHERE key = ?", (key,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else default


async def set_setting(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value)
        )
        await db.commit()
