# Installation


### Python 3.12 Installation

```bash
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.12
sudo apt-get install python3.12-dev python3.12-venv
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3.12 get-pip.py
python3.12 -m pip install --upgrade pip
```

### Environment setup

```bash
cd ./ocl-api
python3.12 -m venv .venv
source .venv/bin/activate
python3.12 -m pip install -r requirements.txt
python3.12 -m pip install -r requirements-dev.txt
```

## VS Code

### Linting and formatting

- For this project we’re going to use flake8 for linting and black for code formatting. In VS Code  simply install their respective extensions.
- Press alt-shift-f to auto format the currently open file
- Add the following line to flake8’s args in the settings UI so that it aligns with black
```
--max-line-length=88
```



- A ruler is helpful with staying inside the line length limit. Add the following to the settings.json of your workspace
```
{
    "editor.rulers" : [88],
}
```
## Poetry
This project uses poetry for package management.

Install pipx
```console
sudo apt install pipx
pipx ensurepath
```
Installation with pipx
```console
python3.12 -m pip install poetry
```



to add a dependency:
```console
poetry add fastapi@0.115.4
```

to add a test dependency
```console
poetry add black@24.10.0 --group test
```

to remove a dependency:
```console
poetry remove black --group test
```

to install all dependencies:
```console
poetry lock --no-update
poetry install
```

to install dependencies without testing dependencies:
```console
poetry install --without test
```
## Migrations

Make sure you create a "revision" of your models and that you "upgrade" your database with that revision every time you change them. As this is what will update the tables in your database. Otherwise, your application will have errors.

* Run the stack
```console
docker compose --profile dev up -d --build
```

* After changing a model (for example, adding a column), inside the container, create a revision, e.g.:

```console
$ docker compose exec api-dev alembic revision --autogenerate -m "Added user and item tables"

# Example output
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.autogenerate.compare] Detected added table 'users'
INFO  [alembic.autogenerate.compare] Detected added index ''ix_users_email'' on '('email',)'
INFO  [alembic.autogenerate.compare] Detected added table 'items'
  Generating /usr/src/app/alembic/versions/90deb8c510f7_added_user_and_item_tables.py ...  done
```


* Alembic is already configured to import your SQLAlchemy models from `./src/app/models/db/`.

* Copy the files from the container to your local host

```console
docker compose cp api-dev:/usr/src/app/alembic/versions/90deb8c510f7_added_user_and_item_tables.py ./src/app/alembic/versions/
```
* Do a sanity check on the generated file. If you restart the compose from this point onwards the migration will automatically run
* Commit the files generated in the alembic directory to the git repository.
* Restart the compose

```console
docker compose --profile dev down
docker compose --profile dev up -d --build
```