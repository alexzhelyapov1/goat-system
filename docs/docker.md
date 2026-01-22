# Развертывание с помощью Docker

В данном руководстве приведены инструкции по развертыванию приложения на сервере с использованием Docker и Docker Compose. Данная конфигурация оптимизирована для легковесной многопроцессорной среды с использованием SQLite.

## Предварительные требования

Прежде чем начать, убедитесь, что на вашем сервере установлены:

*   **Docker:** [Установка Docker Engine](https://docs.docker.com/engine/install/)
*   **Docker Compose:** [Установка Docker Compose](https://docs.docker.com/compose/install/)
*   **Git:** Для клонирования репозитория.

```
sudo apt update
sudo apt install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER
```


## 1. Начальная настройка сервера

### Клонирование репозитория

Сначала клонируйте репозиторий проекта на свой сервер.

```sh
git clone https://github.com/alexzhelyapov1/goat-system.git
cd goat-system
```

### Настройка переменных окружения

Приложение настраивается с помощью файла `.env`. Пример файла находится в `.env.example`.

1.  **Создайте собственный файл `.env`:**

    ```sh
    cp .env.example .env
    ```

2.  **Отредактируйте файл `.env`**, указав свои настройки. Вы **обязательно** должны указать секретные ключи и токен Telegram-бота.

    ```dotenv
    # .env

    # Настройки приложения
    SECRET_KEY=очень-секретный-ключ-который-нужно-изменить
    TELEGRAM_BOT_TOKEN=ваш-токен-телеграм-бота
    TELEGRAM_BOT_USERNAME=имя-вашего-бота

    # URL сервисов Docker для SQLite и Redis
    DATABASE_URL=sqlite:////app/data/app.db
    REDIS_URL=redis://redis:6379/0
    ```

    *   `SECRET_KEY`: Длинная случайная строка для обеспечения безопасности сессий.
    *   `TELEGRAM_BOT_TOKEN`: Ваш токен, полученный от BotFather в Telegram.
    *   Параметры `DATABASE_URL` и `REDIS_URL` уже настроены для среды Docker, их изменять не следует.

## 2. Сборка и запуск приложения

После настройки файла `.env` вы можете собрать и запустить весь стек приложений одной командой.

```sh
# old
# docker-compose up --build -d

# v2 -> same cmd
# sudo ln -s /usr/libexec/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose
docker compose up --build -d
```

*   `--build`: Этот флаг указывает Docker Compose собрать образы из `Dockerfile` перед запуском сервисов.
*   `-d`: Этот флаг запускает контейнеры в фоновом (отсоединенном) режиме.

При первом запуске будут загружены базовые образы Python и Redis, а также собран образ приложения. Последующие запуски будут проходить гораздо быстрее.

## 3. Управление и мониторинг приложения

### Проверка статуса контейнеров

Чтобы проверить, запущены ли все ваши сервисы (`web`, `bot`, `worker`, `redis`), используйте команду:

```sh
docker compose ps
```

Для всех контейнеров в колонке `State` должно быть указано `Up`.

### Просмотр логов

Чтобы просмотреть логи конкретного сервиса в реальном времени (например, сервиса `web`):

```sh
docker compose logs -f web
```

Чтобы просмотреть логи бота или воркера, замените `web` на `bot` или `worker`. Это очень полезно для отладки.

### Миграции базы данных

Сервис `web` настроен на автоматическое применение всех ожидающих миграций базы данных при запуске. Команда `flask db upgrade` выполняется непосредственно перед запуском сервера Gunicorn.

### Остановка приложения

Чтобы остановить и удалить контейнеры, выполните:

```sh
docker compose down
```

**Примечание:** Эта команда **не** удаляет базу данных. Ваша база данных SQLite хранится в постоянном томе (volume) Docker.

## 4. Хранение данных

База данных SQLite (`app.db`) хранится в именованном томе Docker под названием `sqlite_data`. Это гарантирует сохранность ваших данных даже при удалении контейнеров с помощью команды `docker-compose down`.

Вы можете просмотреть список всех томов Docker:

```sh
docker volume ls
```

Чтобы полностью удалить все данные, включая базу данных, можно выполнить команду `docker-compose down -v`. **Внимание: Это действие необратимо и приведет к потере всех данных.**

Monitoring:
```sh
docker stats --no-stream
docker ps -as
docker system df
```