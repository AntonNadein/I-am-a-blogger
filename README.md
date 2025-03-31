# Personal diary, or blog?

## Описание:

Personal diary, or blog? - веб-приложение для ведения личного дневника, или блога если вы открыты и
готовы зарабатывать на своей информации!

Веб-приложение на языке Python с использованием фреймворка Django, которое позволяет пользователям управлять
своим личным дневником, или блогом. На данном этапе в приложении реализована функциональность для создания, просмотра,
редактирования и удаления записей и пользователей. У каждой запись есть возможность установки цены,
для приёма и обработки электронных платежей используется stripe(*https://stripe.com/*)

## Установка:
[Для проверки работоспособности и функционала лучше использовать 
Docker установка и настройка далее по тексту.](#docker-start)

* Клонируем репозиторий *git@github.com:AntonNadein/I-am-a-blogger.git*
* Устанавливаем зависимости **pyproject.toml**
  * Для работы на Windows добавлен пакет eventlet
* Переименовываем файл .env.sample в .env и заполняем его своими данными
    * SECRET_KEY=
    * DEBUG=
      * *Настройки подключения к базе данных*
      * POSTGRES_DB=
      * POSTGRES_USER=
      * POSTGRES_PASSWORD=
      * POSTGRES_HOST=
      * PORT=
      * *Настройки подключения к почтовому сервису*
      * EMAIL_HOST=
      * EMAIL_PORT=
      * EMAIL_HOST_USER=
      * EMAIL_HOST_PASSWORD=
      * EMAIL_USE_TLS=
      * EMAIL_USE_SSL=

  * REDIS=
* Если у вас не установлен Redis воспользуйтесь:
* Windows  https://github.com/microsoftarchive/redis/releases
* Для macOS 
``` 
brew install redis 
```
* Для Linux 
```
sudo apt update
sudo apt install 
```
## Использование:

Запуск:
* Запуск Redis (worker) для получения задач и их выполнения. 
  * *```redis-server```*
* Проверка работы Redis.
  * *```redis-cli ping```* Вы должны увидеть ответ: 'PONG'
* Выполнение миграций Django командой ``` python manage.py makemigrations  ```
* Для формы ввода текста ``` python manage.py collectstatic  ```
* Добавление демонстрационных данных ``` python manage.py add_start_data  ```
* Добавление демонстрационных данных ``` python manage.py add_today_data  ```
* Запуск Django командой ``` python manage.py runserver  ```
* Если вы все сделали правильно, то увидите работающее приложение по ссылке http://127.0.0.1:8000/

## Структура проекта:

#### Приложение состоит из двух основных модулей:

1. *blog* - приложение управления своими записями и просмотра записей. Содержит модели, формы, представления с 
основными CRUD операциями.

2. *users* - приложение управления пользователями и группами. Содержит модели, формы, представления с основными CRUD
   операциями с пользователями. В данном приложении реализована система регистрации(с подтверждением своего email) и
   аутентификации пользователей, так же реализован функционал восстановления пароля.

* *config* - настройки проекта(settings.py) и настройки маршрутов (urls.py).


<h2 id="docker-start">Запуск проекта с помощью Docker Compose</h2>

**Подготовка к запуску проекта:**
1. Установите Docker.
2. Установите Docker Compose.
3. Убедитесь, что Docker запущен и работает.

**Запуск проекта**
1. Клонируйте репозиторий:
```
git@github.com:AntonNadein/I-am-a-blogger.git
```
2. Переименовываем файл .env.sample в .env и заполняем его своими данными.
3. Запустите проект, выполнив команду для запуска в фоновом режиме:
```
docker-compose up -d
или
docker-compose up -d --build
```

После запуска веб-приложение будет доступно по адресу: **http://localhost:8000** с минимальным набором тестовых данных
для демонстрации.

**Дополнительные команды:**
- Для просмотра запущенных контейнеров:
```
docker-compose ps
```
- Для просмотра логов всех контейнеров:
```
docker-compose logs
```
- Для остановки сервисов:
```
docker-compose down
```
## Настройка CI/CD и деплой.

## Настройка сервера и ручной деплой приложения с использованием Docker.

1. ###  ***Настройка сервера на примере операционной системы Linux Ubuntu.***
- Откройте терминал и выполните команду для обновления списка пакетов:
```
sudo apt update
```
- Обновления всех установленных пакетов до их последних версий. Эта команда может потребовать подтверждения перед
началом обновления.
```
sudo apt upgrade
```
- ***Установка Docker*** https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository
  - Добавить официальный ключ GPG Docker (Выполняйте построчно): 
```
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
```
- Добавьте репозиторий в источники Apt (Эта команда может потребовать подтверждения):
```

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
```
- Установка Docker последней версии.
```
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```
- Проверка выполнения установки.
```
sudo docker run hello-world
```
- В ответе вы должны получить *Hello from Docker!*
- ***Настройка файрвола***
- Сначала проверьте состояние файрвола с помощью команды
```
sudo ufw status
```
- Если файрвол отключен, активируйте его
```
sudo ufw enable
```
- Теперь откройте необходимые порты
- Порт 80 для HTTP:
```
sudo ufw allow 80/tcp
```
- Порт 443 для HTTPS:
```
sudo ufw allow 443/tcp
```
- Порт Порт 22 нужен для работы протокола Secure Shell (SSH):
```
sudo ufw allow 22/tcp
```
- Проверьте настройки файрвола, чтобы убедиться, что правила применились (порты 80,443 и 22 находятся в состоянии 
ALLOW).
```
sudo ufw status
```
2. ### ***Ручной деплой приложения с использованием Docker.***
- Перейдите в директорию, где вы хотите разместить код вашего приложения.
- Затем выполните команду для клонирования репозитория (если вы клонируете главную ветку main):
```
https://github.com/AntonNadein//I-am-a-blogger.git
```
- Если вы клонируете НЕ главную ветку. В этом случае будут загружены все ветки репозитория, но проверка будет 
выполнена в указанной, и эта ветка станет настроенной локальной веткой:
```
git clone --branch <имя_ветки> https://github.com/AntonNadein//I-am-a-blogger.git
```
- Добавьте переменные окружения для данного репозитория.
```
cd I-am-a-blogger
```
```
nano .env
```
***Данные требующиеся для запуска приложения***
```
SECRET_KEY=

DEBUG=

POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_HOST=
PORT=
POSGTRES_USER=

EMAIL_HOST=
EMAIL_PORT=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=
EMAIL_USE_SSL=

REDIS=
```
- Выполните команду для запуска контейнеров.
```
docker-compose up -d
```
- Если команда не сработала, попробуйте команду от имени пользователя, являющегося администратором системы.
```
sudo docker-compose up -d
```
- Остановка контейнеров.
```
docker-compose stop
```
- Удаление контейнеров.
```
docker-compose down
```
**Возможные проблемы:**
- Добавить текущего пользователя, который вошёл в систему, в группу Docker. Если нужно добавить другого пользователя,
то значение $USER следует заменить на желаемое имя пользователя
```
sudo usermod -aG docker $USER
```
-  Установить Docker Compose из репозитория Ubuntu.
```
sudo apt install docker-compose
```

## Тестирование:
* ```coverage run manage.py test```
* ```coverage report```

Test coverage 94%

## Лицензия:
Этот проект не имеет лицензий.