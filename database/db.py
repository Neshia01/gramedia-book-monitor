
import sqlite3
import os
from datetime import datetime

from config import DATABASE_PATH


def init_db():
    # Pastikan folder database tersedia
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT,
            price INTEGER,
            isbn TEXT,
            pages TEXT,
            size TEXT,
            age_rating TEXT,
            published_date TEXT,
            categories TEXT,
            url TEXT UNIQUE,
            image TEXT,
            last_updated TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER,
            price INTEGER,
            recorded_at TEXT,
            FOREIGN KEY (book_id) REFERENCES books(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scrape_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scraped_at TEXT,
            total_books INTEGER,
            new_books INTEGER,
            price_changes INTEGER
        )
    """)

    connection.commit()
    connection.close()


def save_books(books):
    init_db()

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_books = 0
    price_changes = 0
    changes = []

    try:
        for book in books:
            cursor.execute(
                "SELECT id, title, price, image FROM books WHERE url = ?",
                (book["url"],)
            )

            existing = cursor.fetchone()

            if existing is None:
                # Buku baru
                cursor.execute("""
                    INSERT INTO books (
                        title, author, price, isbn, pages, size,
                        age_rating, published_date, categories,
                        url, image, last_updated
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    book["title"],
                    book["author"],
                    book["price"],
                    book["isbn"],
                    book["pages"],
                    book["size"],
                    book["age_rating"],
                    book["published_date"],
                    book["categories"],
                    book["url"],
                    book["image"],
                    now
                ))

                book_id = cursor.lastrowid
                new_books += 1

                # Simpan harga awal buku
                if book["price"] is not None:
                    cursor.execute("""
                        INSERT INTO price_history (
                            book_id, price, recorded_at
                        )
                        VALUES (?, ?, ?)
                    """, (book_id, book["price"], now))

            else:
                # Buku sudah ada
                book_id = existing["id"]
                old_price = existing["price"]
                new_price = book["price"]

                # Jika scraper tidak mendapatkan harga,
                # pertahankan harga lama agar tidak terhapus
                if new_price is None:
                    new_price = old_price

                # Harga awal baru ditemukan
                if old_price is None and new_price is not None:
                    cursor.execute("""
                        INSERT INTO price_history (
                            book_id, price, recorded_at
                        )
                        VALUES (?, ?, ?)
                    """, (book_id, new_price, now))

                # Harga benar-benar berubah
                elif (
                    old_price is not None
                    and new_price is not None
                    and old_price != new_price
                ):
                    cursor.execute("""
                        INSERT INTO price_history (
                            book_id, price, recorded_at
                        )
                        VALUES (?, ?, ?)
                    """, (book_id, new_price, now))

                    difference = new_price - old_price
                    percentage = (
                        (difference / old_price) * 100
                        if old_price != 0 else 0
                    )

                    changes.append({
                        "title": book["title"],
                        "old_price": old_price,
                        "new_price": new_price,
                        "difference": difference,
                        "percentage": percentage,
                        "direction": (
                            "naik" if difference > 0 else "turun"
                        )
                    })

                    price_changes += 1

                # Perbarui informasi buku
                cursor.execute("""
                    UPDATE books SET
                        title = ?,
                        author = ?,
                        price = ?,
                        isbn = ?,
                        pages = ?,
                        size = ?,
                        age_rating = ?,
                        published_date = ?,
                        categories = ?,
                        image = ?,
                        last_updated = ?
                    WHERE id = ?
                """, (
                    book["title"],
                    book["author"],
                    new_price,
                    book["isbn"],
                    book["pages"],
                    book["size"],
                    book["age_rating"],
                    book["published_date"],
                    book["categories"],
                    book["image"] or existing["image"],
                    now,
                    book_id
                ))

        # Simpan riwayat scraping
        cursor.execute("""
            INSERT INTO scrape_history (
                scraped_at, total_books, new_books, price_changes
            )
            VALUES (?, ?, ?, ?)
        """, (now, len(books), new_books, price_changes))

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    return {
        "total_books": len(books),
        "new_books": new_books,
        "price_changes": price_changes,
        "changes": changes
    }


if __name__ == "__main__":
    init_db()
    print("Database berhasil disiapkan!")
