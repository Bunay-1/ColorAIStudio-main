# ICAP Release Process

Този документ описва как да се създаде ново издание на ICAP с автоматична версия, changelog и Git таг.

## Стъпки за release

1. Уверете се, че работното дърво е чисто:
   ```bash
   git status
   ```

2. Изберете нова семантична версия, например `8.9.8`.

3. Изпълнете release helper скрипта:
   ```bash
   python scripts/release.py \
     --new 8.9.8 \
     --added "Добавено ново наблюдение на health/readiness и release automation." \
     --changed "Актуализирани CI validation и release workflow." \
     --commit \
     --tag
   ```

4. Проверете дали файловете са актуализирани правилно:
   - `utils/version.py`
   - `README.md`
   - `Dockerfile`
   - `docker-compose.yml`
   - `docker-compose.prod.yml`
   - `k8s/icap-deployment.yaml`
   - `postman/ICAP_Enterprise_Collection.json`
   - `requirements.txt`
   - `CHANGELOG.md`
   - `irm_api.py`

5. Ако искате да push-нете и тагнете автоматично, добавете `--push`:
   ```bash
   python scripts/release.py --new 8.9.8 --added "..." --changed "..." --commit --tag --push
   ```

## GitHub Actions release workflow

Създадохме `./github/workflows/release.yml`.
Това позволява ръчно стартиране от GitHub Actions с входни параметри `version`, `added`, `changed`, `commit`, `tag` и `push`.

## Валидация

След release helper-а, workflow-ът изпълнява `python scripts/validate_versioning.py` за да гарантира, че всички version-relevant файлове са синхронизирани.

## Забележки

- `utils/version.py` е единственият авторитетен източник за текущата ICAP версия.
- `CHANGELOG.md` трябва да има валидна секция `### Добавено` и `### Променено` без `TODO:` маркери.
- Ако workflow се стартира с `--push`, GitHub токенът използва checkout credentials за push към remote.
- Нов workflow `./github/workflows/publish-release.yml` публикува GitHub release автоматично при push на таг `v*`, използвайки текста на текущата секция от `CHANGELOG.md`.
