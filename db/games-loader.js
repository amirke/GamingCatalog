// Shared ES5 loader: HTTP uses JSON; file:// uses the generated script copy.
(function () {
    function normalize(rows) {
        if (!Array.isArray(rows)) throw new Error('Database must be an array');
        return rows.map(function (row) {
            var source = row.download_links || {};
            var links = {mediafire: [], '1file': [], other: []};
            Object.keys(source).forEach(function (host) {
                if (!Array.isArray(source[host])) return;
                var destination = host === 'mediafire' || host === '1file' ? host : 'other';
                source[host].forEach(function (url) {
                    if (typeof url === 'string' && /^https?:\/\//i.test(url)) links[destination].push(url);
                });
            });
            return {name: String(row.name || 'Untitled'), page_url: row.page_url || '',
                download_links: links,
                total_links: links.mediafire.length + links['1file'].length + links.other.length};
        });
    }
    window.loadPS4Games = function (done, progress) {
        function finish(rows) {
            var games;
            try { games = normalize(rows); } catch (error) { done(error); return; }
            done(null, games);
        }
        if (window.location.protocol === 'file:') {
            if (window.PS4_GAMES_DATA) { finish(window.PS4_GAMES_DATA); return; }
            var script = document.createElement('script');
            script.src = 'ps4-games-data.js';
            script.onload = function () { finish(window.PS4_GAMES_DATA); };
            script.onerror = function () { done(new Error('Local data file is missing: ps4-games-data.js')); };
            document.head.appendChild(script);
            return;
        }
        var xhr = new XMLHttpRequest();
        xhr.open('GET', 'ps4_games_expanded.json', true);
        xhr.timeout = 60000;
        xhr.onprogress = function (event) {
            if (progress && event.lengthComputable) progress(100 * event.loaded / event.total);
        };
        xhr.onload = function () {
            if (xhr.status < 200 || xhr.status >= 300) { done(new Error('Database request failed (HTTP ' + xhr.status + ')')); return; }
            var rows;
            try { rows = JSON.parse(xhr.responseText); } catch (error) { done(error); return; }
            finish(rows);
        };
        xhr.onerror = function () { done(new Error('Cannot load the games database')); };
        xhr.ontimeout = function () { done(new Error('Database request timed out')); };
        xhr.send();
    };
}());
