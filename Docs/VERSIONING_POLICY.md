# ICAP Versioning and Change Documentation Policy

Всяка промяна, която засяга технологичния стек на ICAP, трябва да следва следния процес:

1. Актуализиране на версията на платформата.
   - Централен version constant файл: `utils/version.py`.
   - Основен application metadata: `irm_api.py`, health endpoint и tracing metadata.
2. Актуализиране на контейнерните артефакти.
   - `Dockerfile`: добавяне/обновяване на метаданни и label за версия.
   - `docker-compose.yml` и `docker-compose.prod.yml`: добавете/обновете `ICAP_VERSION` и образи.
3. Актуализиране на документацията.
   - Основният `README.md` трябва да отразява актуалната версия и build/run инструкции.
   - Ако промяната засяга модул, добавете или актуализирайте съответната документация в `Docs/`.
4. Актуализиране на CHANGELOG.
   - Записвайте всяка значима промяна в `CHANGELOG.md`.
   - Новият release трябва да се добави като отделна секция с дата и ключови промени.

## Обхват

Този процес е задължителен за всички промени, свързани с:
- нови функции или подобрения на инфраструктурата
- промени в Docker/compose/deployment manifests
- промени в API, наблюдаемост или tracing
- промени в CI/CD, build pipeline или packaging

## Цел

Гарантиране на консистентна версия, прозрачност за инженерите и адекватна документация за всяка промяна в ICAP.

## CI интеграция

Всяка промяна в кода вече преминава през CI проверка за версия:
- `scripts/validate_versioning.py` валидира, че `utils/version.py` е синхронизиран с `README.md`, `Dockerfile`, `docker-compose.yml`, `docker-compose.prod.yml`, `k8s/icap-deployment.yaml`, `CHANGELOG.md`, `postman/ICAP_Enterprise_Collection.json` и `requirements.txt`.
- Ако версията е несъответстваща или ако липсва запис в changelog-а, CI pipeline ще се провали.

## Автоматичен version bump

За да актуализирате версията на платформата, използвайте:

```bash
python scripts/bump_version.py --patch
python scripts/bump_version.py --minor
python scripts/bump_version.py --major
python scripts/bump_version.py --new 8.9.7
```

След изпълнение:
- `utils/version.py` и всички артефакти ще бъдат синхронизирани автоматично.
- `CHANGELOG.md` ще получи ново заглавие с дата и placeholders за описание.
- Прегледайте TODO секциите в changelog-а преди commit.
