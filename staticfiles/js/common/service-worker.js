self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open('vvecon-viptravels-cache').then(function(cache) {
            return cache.addAll([
                `statics/css/light/all.min.css`,
                `statics/css/light/animate.min.css`,
                `statics/js/util/bootstrap/bootstrap.min.js`,
                `statics/js/util/jquery/jquery.min.js`,
                `statics/fonts/light/inter/inter.css`,
                `statics/icons/light/photoshop/styles.min.css`
            ]);
        })
    );
});
self.addEventListener('activate', function(event) {
    const cacheWhitelist = ['vvecon-viptravels-cache'];
    event.waitUntil(
        caches.keys().then(function(cacheNames) {
            return Promise.all(
                cacheNames.map(function(cacheName) {
                    if (cacheWhitelist.indexOf(cacheName) === -1) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});
self.addEventListener('fetch', function(event) {
    event.respondWith(
        caches.match(event.request).then(function(response) {
            return response || fetch(event.request);
        })
    );
});
