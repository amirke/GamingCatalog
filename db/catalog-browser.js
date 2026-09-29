// Keep the rendered page small; search the full in-memory catalog by title.
(function () {
    window.initGameBrowser = function (games, render) {
        var size = 50, currentPage = 1, timer = null, composing = false;
        var input = document.getElementById('searchInput');
        var container = document.getElementById('gamesContainer');
        var info = document.getElementById('searchInfo');
        // Preserve the original letter grouping and order within each letter.
        var groups = {};
        games.forEach(function (game) {
            var first = game.name.charAt(0).toUpperCase();
            var letter = /^[A-Z]$/.test(first) ? first : '#';
            if (!groups[letter]) groups[letter] = [];
            groups[letter].push({game: game, search: game.name.toUpperCase()});
        });
        var entries = [];
        Object.keys(groups).sort().forEach(function (letter) { entries = entries.concat(groups[letter]); });
        var matches = entries;
        var nav = document.createElement('nav');
        nav.className = 'catalog-pagination'; nav.setAttribute('aria-label', 'Search result pages');
        nav.innerHTML = '<button type="button" id="previousPage">Previous</button>' +
            '<label>Page <input id="pageNumber" type="number" min="1" value="1" aria-label="Page number"></label>' +
            '<span id="pageTotal"></span><button type="button" id="nextPage">Next</button>';
        container.parentNode.insertBefore(nav, container.nextSibling);
        var previous = document.getElementById('previousPage');
        var next = document.getElementById('nextPage');
        var pageNumber = document.getElementById('pageNumber');
        info.setAttribute('aria-live', 'polite');
        function show() {
            var pages = Math.max(1, Math.ceil(matches.length / size));
            currentPage = Math.max(1, Math.min(currentPage, pages));
            var start = (currentPage - 1) * size;
            render(matches.slice(start, start + size).map(function (entry) { return entry.game; }));
            if (!matches.length) container.textContent = 'No matching records.';
            container.scrollTop = 0;
            document.getElementById('scrollTop').classList.remove('show');
            previous.disabled = currentPage === 1;
            next.disabled = currentPage === pages;
            pageNumber.value = currentPage; pageNumber.max = pages; pageNumber.disabled = !matches.length;
            document.getElementById('pageTotal').textContent = 'of ' + pages;
            info.textContent = matches.length ? 'Showing ' + (start + 1).toLocaleString() + '-' +
                Math.min(start + size, matches.length).toLocaleString() + ' of ' + matches.length.toLocaleString() +
                (input.value.trim() ? ' matching records' : ' records') : 'No matching records';
        }
        function search() {
            clearTimeout(timer);
            var query = input.value.trim().toUpperCase();
            matches = query ? entries.filter(function (entry) { return entry.search.indexOf(query) !== -1; }) : entries;
            currentPage = 1; show();
        }
        input.addEventListener('input', function () {
            if (composing) return;
            clearTimeout(timer); timer = setTimeout(search, 150);
        });
        input.addEventListener('compositionstart', function () { composing = true; clearTimeout(timer); });
        input.addEventListener('compositionend', function () { composing = false; search(); });
        input.addEventListener('keydown', function (event) { if (event.key === 'Enter' && !composing) search(); });
        previous.addEventListener('click', function () { if (timer !== null) search(); currentPage--; show(); });
        next.addEventListener('click', function () { if (timer !== null) search(); currentPage++; show(); });
        pageNumber.addEventListener('change', function () {
            var requested = parseInt(pageNumber.value, 10) || 1;
            if (timer !== null) search(); currentPage = requested; show();
        });
        // Retain the callable search entry point used by older integrations.
        window.searchGames = search;
        search();
    };
}());
