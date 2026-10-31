from django.conf import settings
from django.http import HttpResponse

FALLBACK = """<!doctype html><meta charset="utf-8"><title>Chayabari</title>
<body style="font-family:system-ui;padding:2rem">
<h1>Chayabari API is running</h1>
<p>The Vue frontend has not been built yet. Run <code>npm run build</code> in <code>frontend/</code>,
then <code>python manage.py collectstatic</code>. During development use the Vite dev server
(<code>npm run dev</code>, http://localhost:5173).</p>
<p><a href="/admin/">Admin</a> · <a href="/api/">API</a></p></body>"""


def spa_index(request):
    index = settings.SPA_DIST_DIR / "index.html"
    if index.exists():
        return HttpResponse(index.read_text(encoding="utf-8"))
    return HttpResponse(FALLBACK)
