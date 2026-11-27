Deploy this Flask project on Render
==================================

The deployment entry point is `run:app`. All 47 SQLAlchemy tables and demo data are
created automatically when the application starts with an empty database.

1. Upload the project to a separate GitHub repository
--------------------------------------------------

Create a new repository at https://github.com/new, for example `karahi-house`.

Extract `artifacts/Restaurant-Render.zip`, then upload the **contents** of its
`Restaurant-Render` folder using GitHub's **uploading an existing file** link (or
**Add file > Upload files** in a populated repository). Drag the contents into
the upload area and commit the upload.

The top level of the repository must contain:

```
app/
tests/
run.py
requirements.txt
.python-version
render.yaml
README.md
DEPLOY_RENDER.md
```

Do not upload the ZIP itself as the application. Do not wrap everything inside
another folder. Do not upload `.venv`, `instance`, `.env`, caches or audit artifacts.
The prepared ZIP already excludes those items.

The current Restaurant folder is inside a Desktop-level Git repository belonging
to a different project. Do not run `git add .` from Desktop or push to that
repository to deploy this restaurant. The GitHub upload method above keeps this
project separate without changing the existing repository.

2. Create the Render web service
-------------------------------

Open https://dashboard.render.com, sign in, and select **New > Web Service**.
Connect GitHub and select the restaurant repository. Use these settings:

| Setting | Value |
| --- | --- |
| Name | `karahi-house` or another available name |
| Language / Runtime | Python 3 |
| Branch | Your repository's default branch, usually `main` |
| Root Directory | Leave blank when `run.py` is at the repository root |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn --workers 1 --threads 2 --bind 0.0.0.0:$PORT run:app` |
| Instance Type | Free |
| Health Check Path | `/` |

The `.python-version` file selects the same Python 3.12.7 version used locally.
Gunicorn is installed on Render's Linux runtime and skipped on Windows.
Using one worker avoids concurrent first-run seeding of the SQLite database.

Under **Environment Variables**, add `SECRET_KEY` with a generated random value.
Use Render's Generate option if it is offered. Otherwise generate a value locally:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

Paste that value into Render's environment variable field, not into source code.
Leave `DATABASE_URL` unset for this classroom demo, so the existing SQLite setup
is used. Then click **Deploy Web Service**.

Alternatively, **New > Blueprint** can use `render.yaml` to configure the same
free service and generate `SECRET_KEY` automatically. Choose one creation method,
not both, so you do not create duplicate services.

3. Check the live website
------------------------

Once the service shows **Live**, open the `https://...onrender.com` URL displayed
by Render. The exact URL depends on your chosen available service name.

Check the homepage, food images, menu search, login, cart and checkout. Use the
seeded accounts for the class demonstration:

| Role | Email | Password |
| --- | --- | --- |
| Admin | admin@karahihouse.test | Admin12345 |
| Customer | ayesha@example.com | Customer123 |

No payment gateway is connected. Select **Pay at counter** for demonstrations.

Open the website a few minutes before the online class. Free Render services
sleep after 15 minutes without traffic; the next visit can take about a minute
to wake the service.

SQLite on Render's free web service is temporary. Newly created users and orders
are lost when Render replaces the filesystem during a restart, redeploy or
spin-down. The seed menu and demonstration accounts are recreated automatically.
For persistent records, configure a supported external database or a paid service
with a persistent disk as a separate deployment change.

Troubleshooting
---------------

- `gunicorn: command not found`: confirm the updated `requirements.txt` was
  uploaded, then redeploy.
- `No module named run`: ensure `run.py` is at the service root; correct Root
  Directory if the repository has a wrapper folder.
- Missing pictures: confirm `app/static/img/food/` was uploaded with its files.
- Build failure: read the first actual error in Render's Logs. Do not use
  `python run.py` or `flask run` as the production start command.

Official documentation:

- https://render.com/docs/deploy-flask
- https://render.com/docs/python-version
- https://render.com/docs/free

This setup prepares a classroom deployment. The backend findings recorded in the
earlier project audit are separate from hosting configuration.
