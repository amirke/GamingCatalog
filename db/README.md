# Embedded PS4 Games Database

This copy is served at `GamingCatalog/db/`. Open `index.html` or use **Jump to DB** in the portal; **Jump to portal** returns to `../index.html`. Both directions work over HTTP and when opening the files locally. Includes the local loading and 50-record pagination fixes. Database records are separate from the personal portal catalog and do not change saved notes or Gist state.

Upstream: https://github.com/huggingfacer04/ps4-games-database — copyright (c) 2025 huggingfacer04, MIT; original license retained in `LICENSE`. Imported from the user's local `PS44` copy on 2026-09-30. The nested Git repository and deployment workflow are not included; the parent GamingCatalog repository deploys this directory.

---

# 🎮 PS4 Games Complete Database

> **6,001+ PS4 games with 38,690+ direct download links**  
> Free PKG files for jailbroken PS4 consoles (Firmware 9.00 - 11.00)

[![Games](https://img.shields.io/badge/Games-6,001-blue)](https://huggingfacer04.github.io/ps4-games-database/)
[![Download Links](https://img.shields.io/badge/Download%20Links-38,690-green)](https://huggingfacer04.github.io/ps4-games-database/)
[![Success Rate](https://img.shields.io/badge/Success%20Rate-100%25-brightgreen)](https://huggingfacer04.github.io/ps4-games-database/)
[![Built with](https://img.shields.io/badge/Built%20with-Galaxy.ai-purple)](https://galaxy.ai/?via=start-building)

---

## 🌟 Features

- **6,001 PS4 Games** - Complete database from dlpsgame.com
- **38,690 Download Links** - Mediafire, 1File, Mega, Google Drive, and more
- **Real-time Search** - Find any game instantly
- **Alphabetical Organization** - Browse by letter (A-Z)
- **Multiple Mirrors** - Each game has multiple download options
- **Mobile Responsive** - Works on all devices
- **100% Free** - No registration, no payment, no ads

---

## Catalog performance (2026-09-28)

All three views render 50 records per page. Previous/Next and a page-number input navigate the result set. Search matches titles across the full database, including records on other pages; typing is debounced by 150 ms and Enter searches immediately. Search does not scan rendered DOM nodes. Clearing search returns to page one of the full catalog. No database records were removed.

## Local loading fix (2026-09-28)

Open `index.html` directly in a browser, keeping all files in this folder together. All three catalog HTML pages support both direct file opening and HTTP hosting. Local file mode uses `ps4-games-data.js`; HTTP mode reads `ps4_games_expanded.json`. `games-loader.js` normalizes missing link categories in memory, preserves records without links and includes additional hosts under Mirror/Link.

The database contains 17,065 records, including entries without download links and some entries that are not game titles. Rendering all records does not verify the accuracy or availability of their links. The source JSON is not modified by the loader.

After changing the JSON, run `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Update-LocalData.ps1` to refresh the local-file copy as well.

## 🚀 Quick Start

### Option 1: Use the Live Site
Visit: **[https://huggingfacer04.github.io/ps4-games-database/](https://huggingfacer04.github.io/ps4-games-database/)**

### Option 2: Run Locally
```bash
# Clone the repository
git clone https://github.com/huggingfacer04/ps4-games-database.git
cd ps4-games-database

# Open in browser
open index.html
# or
python -m http.server 8000
# Then visit: http://localhost:8000
```

---

## 📊 Database Statistics

### Total Content
- **Games:** 6,001
- **Download Links:** 38,690
- **Mediafire Links:** 21,267 (54.9%)
- **1File Links:** 16,805 (43.4%)
- **Other Mirrors:** 618 (1.6%)

### Top Games with Most Links
1. **EA Sports FC 25** - 128 links
2. **FIFA 22** - 101 links
3. **FIFA 23** - 88 links
4. **Prince of Persia: The Lost Crown** - 80 links
5. **Elden Ring: Shadow of The Erdtree** - 72 links
6. **God of War Ragnarök** - 66 links
7. **Final Fantasy I–VI Pixel Remaster** - 59 links
8. **Dying Light 2 Stay Human** - 58 links
9. **Dragon Ball Z: Kakarot** - 54 links
10. **Grand Theft Auto V** - 53 links

### Games by Category
- **Action/Adventure:** ~1,500 games
- **RPG:** ~600 games
- **Sports:** ~500 games
- **Racing:** ~300 games
- **Fighting:** ~250 games
- **Shooter:** ~400 games
- **Others:** ~2,451 games

---

## 🔍 How to Use

### 1. Search for a Game
- Type the game name in the search box
- Results filter in real-time
- Example: "God of War", "Spider-Man", "Final Fantasy"

### 2. Browse by Letter
- Scroll through alphabetically organized sections
- Click on any game to see download options

### 3. Download
- Each game has multiple download links
- Choose your preferred host (Mediafire, 1File, etc.)
- Click the download button
- Wait 8 seconds on the redirect page
- Download begins automatically

---

## 📁 File Structure

```
ps4-games-database/
├── index.html                      # Main database interface
├── redirect.html                   # Download interstitial page
├── ps4_games_with_downloads.json   # Complete database (110,392 lines)
└── README.md                       # This file
```

---

## 🎯 Popular Game Series

### Action/Adventure
- Assassin's Creed (10+ games)
- Batman Arkham series
- God of War series
- Grand Theft Auto V
- Spider-Man
- The Last of Us
- Uncharted series

### RPG
- Final Fantasy (20+ games)
- Dark Souls series
- Bloodborne
- Persona 5
- The Witcher 3
- Yakuza series (10+ games)

### Sports
- FIFA (10+ games)
- NBA 2K (10+ games)
- WWE 2K (10+ games)
- Madden NFL series

### Shooter
- Call of Duty (12+ games)
- Battlefield series
- Destiny series
- Borderlands series

---

## 🛠️ Technical Details

### Built With
- **HTML5/CSS3** - Modern web standards
- **JavaScript** - Dynamic functionality
- **JSON** - Database format
- **GitHub Pages** - Free hosting
- **Galaxy.ai** - AI-powered development

### Browser Support
- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Mobile browsers

### Performance
- **Load Time:** < 2 seconds
- **Search Speed:** Real-time (< 100ms)
- **Database Size:** 6.5 MB (compressed)

---

## 📱 Mobile Support

Fully responsive design works on:
- 📱 Smartphones (320px+)
- 📱 Tablets (768px+)
- 💻 Laptops (1024px+)
- 🖥️ Desktops (1920px+)

---

## ⚠️ Important Notes

### Legal Disclaimer
- This database is for **educational purposes only**
- All games are sourced from [dlpsgame.com](https://dlpsgame.com)
- Requires **jailbroken PS4** (firmware 9.00 - 11.00)
- We do not host any files - all links are external
- Use at your own risk

### Requirements
- Jailbroken PS4 console
- Compatible firmware (9.00 - 11.00)
- Internet connection for downloads
- USB drive or FTP for file transfer

---

## 🤝 Contributing

### Report Issues
Found a broken link or error? [Open an issue](https://github.com/huggingfacer04/ps4-games-database/issues)

### Suggest Improvements
Have ideas for new features? [Start a discussion](https://github.com/huggingfacer04/ps4-games-database/discussions)

### Update Database
Want to help keep the database current? See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

## 📈 Project Stats

- **Created:** 2025-10-15
- **Last Updated:** 2025-10-15
- **Total Commits:** 1
- **Contributors:** 1
- **Stars:** ⭐ (Star this repo!)
- **Forks:** 🍴 (Fork to customize!)

---

## 🔗 Related Projects

- **[Documentation Site](https://huggingfacer04.github.io/ps4-database-project/)** - How this was built
- **[Galaxy.ai](https://galaxy.ai/?via=start-building)** - AI tool used to build this
- **[dlpsgame.com](https://dlpsgame.com)** - Original source

---

## 📞 Support

### Need Help?
- 📖 Read the [Deployment Guide](DEPLOYMENT_GUIDE.md)
- 💬 [Open an issue](https://github.com/huggingfacer04/ps4-games-database/issues)
- 🌐 Visit [dlpsgame.com](https://dlpsgame.com) for game-specific help

### Want to Build Something Similar?
Check out **[Galaxy.ai](https://galaxy.ai/?via=start-building)** - the AI tool that built this entire project from a single prompt!

---

## 📜 License

This project is open source and available under the [MIT License](LICENSE).

**Note:** Game files and download links are property of their respective owners. This database only provides links to publicly available content.

---

## 🎉 Acknowledgments

- **dlpsgame.com** - For providing the game database
- **Galaxy.ai** - For making this project possible
- **Open Source Community** - For tools and libraries used
- **You** - For using this database!

---

## 🌟 Star This Repo!

If you find this database useful, please ⭐ star this repository to show your support!

---

<div align="center">

**Built with ❤️ using [Galaxy.ai](https://galaxy.ai/?via=start-building)**

[🎮 View Database](https://huggingfacer04.github.io/ps4-games-database/) | 
[📖 Documentation](https://huggingfacer04.github.io/ps4-database-project/) | 
[🚀 Galaxy.ai](https://galaxy.ai/?via=start-building)

</div>

