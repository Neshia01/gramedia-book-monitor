
import requests
import time

from bs4 import BeautifulSoup
from urllib.parse import urljoin

from config import SEARCH_URL
from database.db import save_books


def get_image_url(product):
    """
    Mengambil URL cover buku dari beberapa kemungkinan atribut gambar.
    Mendukung lazy loading.
    """

    image = product.select_one(".productSlider__img img")

    if not image:
        return ""

    image_url = (
        image.get("src")
        or image.get("data-src")
        or image.get("data-lazy-src")
        or image.get("data-original")
        or ""
    )

    # Jika URL belum ditemukan, periksa srcset
    if not image_url and image.get("srcset"):
        srcset = image["srcset"].split(",")

        if srcset:
            image_url = srcset[0].strip().split()[0]

    # Abaikan gambar kosong atau data URI
    if not image_url or image_url.startswith("data:"):
        return ""

    # Ubah URL relatif menjadi URL lengkap
    return urljoin("https://www.mncgramedia.id", image_url)


def scrape_books(max_pages=100):
    session = requests.Session()

    session.headers.update({
        "User-Agent": "Mozilla/5.0"
    })

    unique_books = {}

    try:
        for page in range(1, max_pages + 1):

            url = f"{SEARCH_URL}?page={page}"
            response = None

            # Coba mengambil halaman maksimal 3 kali
            for attempt in range(1, 4):
                try:
                    response = session.get(
                        url,
                        timeout=30
                    )

                    response.raise_for_status()
                    break

                except requests.RequestException as error:
                    print(
                        f"Halaman {page} gagal "
                        f"(percobaan {attempt}/3): {error}"
                    )

                    if attempt < 3:
                        time.sleep(2 * attempt)

            # Jika tetap gagal, lanjut ke halaman berikutnya
            if response is None:
                print(f"Halaman {page} dilewati.")
                time.sleep(1)
                continue

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            products = soup.select(".productBox")

            # Halaman terakhir memiliki 3 buku katalog
            limit = 3 if page == 673 else 5

            products = products[:limit]

            if not products:
                print(
                    f"Halaman {page} tidak memiliki produk."
                )

                time.sleep(1)
                continue

            for product in products:

                title = product.select_one(
                    ".productTitle"
                )

                author = product.select_one(
                    ".productAuthor"
                )

                price = product.select_one(
                    ".productPrice"
                )

                link = product.select_one(
                    'a[href*="/books/"]'
                )

                # Judul dan link wajib tersedia
                if not title or not link:
                    continue

                # Mengambil detail buku
                details = {}

                for row in product.select(
                    ".productTable tr"
                ):

                    cells = row.find_all("td")

                    if len(cells) >= 3:
                        key = cells[0].get_text(
                            strip=True
                        )

                        value = cells[2].get_text(
                            strip=True
                        )

                        details[key] = value

                # Mengambil kategori buku
                categories = [
                    tag.get_text(strip=True)
                    for tag in product.select(
                        ".productTag__link"
                    )
                ]

                # Mengambil harga
                price_text = (
                    price.get_text(strip=True)
                    if price else ""
                )

                price_number = (
                    int(
                        "".join(
                            filter(str.isdigit, price_text)
                        )
                    )
                    if price_text else None
                )

                # Mengambil URL buku
                book_url = urljoin(
                    "https://www.mncgramedia.id",
                    link.get("href", "")
                )

                # Mengambil URL cover
                image_url = get_image_url(product)

                # Menyusun data buku
                book = {
                    "title": title.get_text(strip=True),

                    "author": (
                        author.get_text(strip=True)
                        if author else "-"
                    ),

                    "price": price_number,

                    "isbn": details.get(
                        "ISBN", "-"
                    ),

                    "pages": details.get(
                        "Jumlah Halaman", "-"
                    ),

                    "size": details.get(
                        "Size", "-"
                    ),

                    "age_rating": details.get(
                        "Jenis Rate", "-"
                    ),

                    "published_date": details.get(
                        "Published Date", "-"
                    ),

                    "categories": ", ".join(categories),

                    "url": book_url,

                    "image": image_url
                }

                # Mencegah duplikasi berdasarkan URL buku
                unique_books[book_url] = book

            print(
                f"Halaman {page}/{max_pages} selesai | "
                f"Total buku unik: {len(unique_books)}"
            )

            # Jeda antar-request
            time.sleep(1)

    finally:
        session.close()

    return list(unique_books.values())


if __name__ == "__main__":

    results = scrape_books(max_pages=100)

    print(
        f"\nTotal buku berhasil diambil: {len(results)}"
    )

    if results:

        stats = save_books(results)

        print("\n=== HASIL PENYIMPANAN DATABASE ===")

        print(
            f"Total buku diproses : {stats['total_books']}"
        )

        print(
            f"Buku baru           : {stats['new_books']}"
        )

        print(
            f"Perubahan harga     : {stats['price_changes']}"
        )

    for index, book in enumerate(results, start=1):

        print(
            f"{index}. {book['title']} "
            f"- Rp{book['price']} "
            f"| Cover: {'Ada' if book['image'] else 'Tidak ada'}"
        )
