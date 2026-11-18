
import sqlite3

from flask import Flask, render_template, request, abort
from config import DATABASE_PATH

app = Flask(__name__)


# =====================================
# DATABASE CONNECTION
# =====================================

def get_db_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


# =====================================
# DASHBOARD
# =====================================

@app.route("/")
def dashboard():
    connection = get_db_connection()

    total_books = connection.execute(
        "SELECT COUNT(*) FROM books"
    ).fetchone()[0]

    total_price_changes = connection.execute(
        "SELECT COUNT(*) FROM price_history"
    ).fetchone()[0]

    latest_scrape = connection.execute("""
        SELECT *
        FROM scrape_history
        ORDER BY id DESC
        LIMIT 1
    """).fetchone()

    latest_books = connection.execute("""
        SELECT *
        FROM books
        ORDER BY id DESC
        LIMIT 5
    """).fetchall()

    scrape_history = connection.execute("""
        SELECT *
        FROM scrape_history
        ORDER BY id DESC
        LIMIT 5
    """).fetchall()

    connection.close()

    return render_template(
        "index.html",
        total_books=total_books,
        total_price_changes=total_price_changes,
        latest_scrape=latest_scrape,
        latest_books=latest_books,
        scrape_history=scrape_history
    )


# =====================================
# BOOK CATALOG
# =====================================

@app.route("/catalog")
def catalog():
    connection = get_db_connection()

    search_query = request.args.get("q", "").strip()

    if search_query:
        books = connection.execute("""
            SELECT *
            FROM books
            WHERE title LIKE ?
               OR author LIKE ?
               OR isbn LIKE ?
            ORDER BY title ASC
        """, (
            f"%{search_query}%",
            f"%{search_query}%",
            f"%{search_query}%"
        )).fetchall()
    else:
        books = connection.execute("""
            SELECT *
            FROM books
            ORDER BY title ASC
        """).fetchall()

    total_books = connection.execute(
        "SELECT COUNT(*) FROM books"
    ).fetchone()[0]

    result_count = len(books)

    connection.close()

    return render_template(
        "catalog.html",
        books=books,
        total_books=total_books,
        result_count=result_count,
        search_query=search_query,
        keyword=search_query
    )


# =====================================
# BOOK DETAIL
# =====================================

@app.route("/book/<int:book_id>")
def book_detail(book_id):
    connection = get_db_connection()

    book = connection.execute("""
        SELECT *
        FROM books
        WHERE id = ?
    """, (book_id,)).fetchone()

    if book is None:
        connection.close()
        abort(404)

    price_history = connection.execute("""
        SELECT *
        FROM price_history
        WHERE book_id = ?
        ORDER BY recorded_at ASC, id ASC
    """, (book_id,)).fetchall()

    connection.close()

    return render_template(
        "detail.html",
        book=book,
        price_history=price_history
    )


# =====================================
# PRICE ANALYSIS
# =====================================

@app.route("/analysis")
def price_analysis():
    connection = get_db_connection()

    books = connection.execute("""
        SELECT
            b.id,
            b.title,
            b.author,
            b.image,

            (
                SELECT ph.price
                FROM price_history ph
                WHERE ph.book_id = b.id
                ORDER BY ph.recorded_at ASC, ph.id ASC
                LIMIT 1
            ) AS first_price,

            (
                SELECT ph.price
                FROM price_history ph
                WHERE ph.book_id = b.id
                ORDER BY ph.recorded_at DESC, ph.id DESC
                LIMIT 1
            ) AS latest_price,

            (
                SELECT ph.recorded_at
                FROM price_history ph
                WHERE ph.book_id = b.id
                ORDER BY ph.recorded_at DESC, ph.id DESC
                LIMIT 1
            ) AS latest_recorded_at,

            (
                SELECT COUNT(*)
                FROM price_history ph
                WHERE ph.book_id = b.id
            ) AS history_count

        FROM books b
        ORDER BY b.title ASC
    """).fetchall()

    connection.close()

    # Pisahkan buku berdasarkan perubahan harga
    increased_books = []
    decreased_books = []
    unchanged_books = []

    for book in books:
        # Minimal dua catatan harga untuk dibandingkan
        if book["history_count"] < 2:
            continue

        first_price = book["first_price"]
        latest_price = book["latest_price"]

        if first_price is None or latest_price is None:
            continue

        difference = latest_price - first_price

        if first_price != 0:
            percentage = (difference / first_price) * 100
        else:
            percentage = 0

        book_data = {
            "id": book["id"],
            "title": book["title"],
            "author": book["author"],
            "image": book["image"],
            "first_price": first_price,
            "latest_price": latest_price,
            "difference": difference,
            "percentage": percentage,
            "latest_recorded_at": book["latest_recorded_at"]
        }

        if difference > 0:
            increased_books.append(book_data)

        elif difference < 0:
            decreased_books.append(book_data)

        else:
            unchanged_books.append(book_data)

    # Urutkan berdasarkan besarnya perubahan
    increased_books.sort(
        key=lambda item: item["difference"],
        reverse=True
    )

    decreased_books.sort(
        key=lambda item: item["difference"]
    )

    biggest_changes = sorted(
        increased_books + decreased_books,
        key=lambda item: abs(item["difference"]),
        reverse=True
    )

    return render_template(
        "analysis.html",
        increased_books=increased_books,
        decreased_books=decreased_books,
        unchanged_books=unchanged_books,
        biggest_changes=biggest_changes,
        total_increased=len(increased_books),
        total_decreased=len(decreased_books),
        total_unchanged=len(unchanged_books),
        total_analyzed=(
            len(increased_books)
            + len(decreased_books)
            + len(unchanged_books)
        )
    )


# =====================================
# RUN APPLICATION
# =====================================

if __name__ == "__main__":
    app.run(debug=True)
