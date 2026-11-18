# 📚 GramediaBook Monitor

GramediaBook Monitor merupakan aplikasi berbasis web yang digunakan untuk mengambil, mengelola, dan memantau informasi katalog serta perubahan harga buku dari website M&C! Gramedia.

Aplikasi ini memanfaatkan teknik web scraping untuk mengumpulkan data buku, menyimpan informasi ke dalam database, serta menyediakan dashboard untuk menampilkan katalog dan analisis perubahan harga. Sistem juga terintegrasi dengan Telegram Bot untuk menjalankan proses scraping secara manual dan mengirimkan notifikasi perubahan harga buku.

## ✨ Fitur Utama

- **Katalog Buku:** Menampilkan informasi buku berupa judul, penulis, ISBN, harga, kategori, dan cover buku.
- **Web Scraping:** Mengambil data buku dari website M&C! Gramedia.
- **Pemantauan Harga:** Mencatat dan memantau perubahan harga buku dari waktu ke waktu.
- **Analisis Harga:** Menampilkan perbandingan dan riwayat perubahan harga buku.
- **Telegram Bot:** Menjalankan scraping secara manual dan menerima notifikasi perubahan harga.
- **Dashboard:** Menampilkan ringkasan data buku dan hasil pemantauan melalui antarmuka web.

## 🛠️ Teknologi yang Digunakan

- Python
- Flask
- Requests
- BeautifulSoup
- SQLite
- Telegram Bot API
- HTML
- CSS

## 🎯 Tujuan Proyek

Proyek ini dikembangkan sebagai penerapan pembelajaran web scraping, pengolahan data, pengelolaan database, serta pengembangan aplikasi web melalui sistem pemantauan katalog dan harga buku.

## 🚀 Cara Menjalankan

1. Clone repository.
2. Buat dan aktifkan virtual environment.
3. Install seluruh dependensi menggunakan `pip install -r requirements.txt`.
4. Buat file `.env` dan masukkan token Telegram Bot.
5. Jalankan aplikasi dashboard menggunakan `python app.py`.
6. Jalankan Telegram Bot menggunakan `python bot.py`.

## 👩‍💻 Pengembangan

GramediaBook Monitor dikembangkan sebagai proyek pembelajaran dan masih dapat dikembangkan dengan penambahan fitur pemantauan katalog serta analisis harga buku.
