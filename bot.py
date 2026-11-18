
import os
import asyncio

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)

from scraper import scrape_books
from database.db import save_books

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


def format_rupiah(amount):
    return f"Rp{amount:,.0f}".replace(",", ".")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "Halo! 👋 Selamat datang di GramediaBook Monitor.\n\n"
        "Bot ini membantu memantau data buku dari M&C! Gramedia.\n\n"
        "Perintah yang tersedia:\n"
        "/scrape - Mulai scraping buku\n"
        "/start - Menampilkan menu bantuan"
    )

    await update.message.reply_text(message)


async def scrape(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⏳ Scraping sedang dimulai. Mohon tunggu..."
    )

    try:
        # Ambil data buku
        books = await asyncio.to_thread(
            scrape_books,
            100
        )

        if not books:
            await update.message.reply_text(
                "⚠️ Scraping tidak menghasilkan data buku."
            )
            return

        # Simpan dan bandingkan harga
        stats = await asyncio.to_thread(
            save_books,
            books
        )

        # Ringkasan scraping
        message = (
            "✅ SCRAPING SELESAI!\n\n"
            f"📚 Total buku ditemukan: {stats['total_books']}\n"
            f"🆕 Buku baru: {stats['new_books']}\n"
            f"💰 Perubahan harga: {stats['price_changes']}\n\n"
            "Data berhasil diperbarui ke database."
        )

        await update.message.reply_text(message)

        # Kirim notifikasi perubahan harga
        changes = stats.get("changes", [])

        if changes:
            await update.message.reply_text(
                "🔔 NOTIFIKASI PERUBAHAN HARGA"
            )

            for change in changes:
                old_price = change["old_price"]
                new_price = change["new_price"]
                difference = abs(change["difference"])
                percentage = abs(change["percentage"])

                if change["direction"] == "naik":
                    icon = "📈"
                    status = "HARGA NAIK"
                else:
                    icon = "📉"
                    status = "HARGA TURUN"

                notification = (
                    f"{icon} {status}\n\n"
                    f"📚 {change['title']}\n\n"
                    f"Harga sebelumnya: {format_rupiah(old_price)}\n"
                    f"Harga terbaru: {format_rupiah(new_price)}\n\n"
                    f"Perubahan: {format_rupiah(difference)} "
                    f"({percentage:.2f}%)"
                )

                await update.message.reply_text(notification)

        else:
            await update.message.reply_text(
                "📊 HARGA BUKU MASIH STABIL\n\n"
                "Tidak ditemukan perubahan harga "
                "pada buku yang diperiksa."
            )

    except Exception as error:
        print("Terjadi kesalahan:", error)

        await update.message.reply_text(
            "❌ Terjadi kesalahan saat scraping. "
            "Silakan periksa terminal."
        )


def main():
    if not TOKEN:
        raise ValueError(
            "TELEGRAM_BOT_TOKEN belum diatur di file .env"
        )

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scrape", scrape))

    print("GramediaBook Monitor Bot sedang berjalan...")

    app.run_polling()


if __name__ == "__main__":
    main()
