# Karahi House — Glass storefront update

Based on RestroIQ V5 Render Ready. This update changes shared public templates and assets only; no models, seed logic, passwords, deployment variables, management layouts or database migrations were changed.

- Floating full-width header over the cinematic homepage with true CSS backdrop blur, gold outline, cream text, active page styling and denser tint after scrolling.
- Original responsive vector logo, optimized WebP hero and responsive HTML typography/buttons. Hero image is an AI-generated illustration, not an actual venue photo.
- Mobile hamburger navigation and authenticated account dropdown retain existing destination URLs and CSRF logout. Guest login and cart drawer are retained. Discover More scrolls to the original section. On inner pages the header uses a stronger tint for contrast on light backgrounds.
- Corrected duplicate promotion markup that was incorrectly inside the menu document title; the offers section at the bottom remains.

## Verification
- `python tools/check_premium_pages.py --browser artifacts/premium`: isolated SQLite seed and 15 Jinja templates, browser overflow at 1440/390, 24 menu cards above fold, cart and reservation-step controls, no browser errors.
- `python tools/check_glass_header.py artifacts/glass`: isolated Jinja fixture browser checks at 320, 390, 768, 1024, 1151, 1440 and 1920 px for guests and signed-in customers, active menu, true backdrop blur, scroll tint and sticky behavior, mobile navigation, account dropdown and cart dialog.
- Flask and Flask-SQLAlchemy could not be installed in the review runtime, so live HTTP/authentication and deployment testing were not executed. These tests render real synthetic seed records via isolated SQLAlchemy and Jinja rather than a running Flask app.

## Update existing GitHub repository
Extract the patch ZIP into the existing repository root and replace matching files. Review `git status`, then commit and push. The patch does not include database or environment files. Alternatively the complete ZIP is a replacement project based on the prior V5 Render Ready package. Preserve existing `.git`, `.env`, local databases and credentials. Render's ephemeral SQLite data may reset on redeployment; back up valuable data first. No environment variable changes are needed for this design update.
