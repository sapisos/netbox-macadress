# Testing

The tests run inside a NetBox checkout, against PostgreSQL and Redis, the same way CI does
(see `.github/workflows/ci.yaml`). They never call the macadress.com API: lookups go through
the fake client in `netbox_macadress/tests/fakes.py`.

```bash
git clone --depth 1 --branch v4.7.2 https://github.com/netbox-community/netbox.git
pip install -r netbox/requirements.txt
pip install -e /path/to/netbox-macadress
cp /path/to/netbox-macadress/testing/configuration.py netbox/netbox/netbox/configuration.py

cd netbox/netbox
python manage.py migrate
python manage.py test netbox_macadress.tests --keepdb
```

`testing/configuration.py` reads `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` and `REDIS_HOST`
from the environment. After changing `models.py`, check for a missing migration with
`python manage.py makemigrations --check netbox_macadress`.

Lint and formatting:

```bash
make lint
make format
```
