# Инструкция по установке Honey Sticks Management System

## Системные требования

### Минимальные требования
- **ОС**: Ubuntu 20.04+ / CentOS 8+ / Windows 10+
- **Python**: 3.8+
- **PostgreSQL**: 12+
- **Node.js**: 14+ (для фронтенд компонентов)
- **RAM**: 4GB (рекомендуется 8GB+)
- **Диск**: 20GB свободного места

### Рекомендуемые требования
- **ОС**: Ubuntu 22.04 LTS
- **Python**: 3.9+
- **PostgreSQL**: 14+
- **Node.js**: 16+
- **RAM**: 8GB+
- **Диск**: 50GB+ SSD

## Установка

### 1. Подготовка системы

#### Ubuntu/Debian
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка зависимостей
sudo apt install -y python3 python3-pip python3-dev python3-venv
sudo apt install -y postgresql postgresql-contrib
sudo apt install -y nodejs npm
sudo apt install -y git wget curl
sudo apt install -y libxml2-dev libxslt1-dev libevent-dev
sudo apt install -y libsasl2-dev libldap2-dev libpq-dev
sudo apt install -y libjpeg-dev libpng-dev libfreetype6-dev
sudo apt install -y liblcms2-dev libwebp-dev libharfbuzz-dev
sudo apt install -y libfribidi-dev libxcb1-dev
```

#### CentOS/RHEL
```bash
# Обновление системы
sudo yum update -y

# Установка EPEL репозитория
sudo yum install -y epel-release

# Установка зависимостей
sudo yum install -y python3 python3-pip python3-devel
sudo yum install -y postgresql postgresql-server postgresql-contrib
sudo yum install -y nodejs npm
sudo yum install -y git wget curl
sudo yum install -y libxml2-devel libxslt-devel libevent-devel
sudo yum install -y openldap-devel postgresql-devel
sudo yum install -y libjpeg-devel libpng-devel freetype-devel
sudo yum install -y lcms2-devel libwebp-devel harfbuzz-devel
sudo yum install -y fribidi-devel libxcb-devel
```

### 2. Установка Odoo Community Edition

```bash
# Создание пользователя odoo
sudo useradd -m -s /bin/bash odoo
sudo usermod -aG sudo odoo

# Переключение на пользователя odoo
sudo su - odoo

# Создание директории для проекта
mkdir -p /home/odoo/honey-sticks
cd /home/odoo/honey-sticks

# Клонирование Odoo Community Edition
git clone https://github.com/odoo/odoo.git --depth 1 --branch 15.0
cd odoo

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей Python
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Настройка PostgreSQL

```bash
# Переключение на пользователя postgres
sudo su - postgres

# Создание базы данных
createdb honey_sticks
createuser odoo --createdb --pwprompt
# Введите пароль для пользователя odoo

# Предоставление прав
psql -c "GRANT ALL PRIVILEGES ON DATABASE honey_sticks TO odoo;"
psql -c "ALTER USER odoo CREATEDB;"

# Выход из postgres
exit
```

### 4. Копирование модулей Honey Sticks

```bash
# Переключение на пользователя odoo
sudo su - odoo
cd /home/odoo/honey-sticks

# Создание директории для кастомных модулей
mkdir -p odoo/custom_addons

# Копирование модулей (предполагается, что модули уже скачаны)
cp -r honey_participants odoo/custom_addons/
cp -r honey_sales odoo/custom_addons/
cp -r honey_production odoo/custom_addons/
cp -r honey_logistics odoo/custom_addons/
cp -r honey_dashboards odoo/custom_addons/

# Установка дополнительных зависимостей
cd odoo
source venv/bin/activate
pip install qrcode[pil] Pillow pandas numpy
```

### 5. Настройка конфигурации

```bash
# Создание конфигурационного файла
cat > /home/odoo/honey-sticks/odoo/odoo.conf << EOF
[options]
addons_path = addons,custom_addons
admin_passwd = admin
csv_internal_sep = ,
data_dir = ./data
db_host = localhost
db_maxconn = 64
db_name = honey_sticks
db_password = odoo
db_port = 5432
db_sslmode = prefer
db_template = template0
db_user = odoo
dbfilter = honey_sticks
http_interface = 0.0.0.0
http_port = 8069
limit_memory_hard = 2684354560
limit_memory_soft = 2147483648
limit_request = 8192
limit_time_cpu = 600
limit_time_real = 1200
limit_time_real_cron = 300
list_db = True
log_db = False
log_handler = :INFO
log_level = info
logfile = ./odoo.log
max_cron_threads = 1
osv_memory_age_limit = 1.0
osv_memory_count_limit = False
proxy_mode = False
server_wide_modules = base,web
translate_modules = ['all']
unaccent = False
without_demo = False
workers = 0
EOF
```

### 6. Создание systemd сервиса

```bash
# Создание сервисного файла
sudo cat > /etc/systemd/system/honey-sticks.service << EOF
[Unit]
Description=Honey Sticks Odoo Server
After=postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=odoo
Group=odoo
WorkingDirectory=/home/odoo/honey-sticks/odoo
ExecStart=/home/odoo/honey-sticks/odoo/venv/bin/python3 odoo-bin -c odoo.conf
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Перезагрузка systemd
sudo systemctl daemon-reload
sudo systemctl enable honey-sticks
```

### 7. Первый запуск и установка модулей

```bash
# Запуск Odoo для инициализации базы данных
cd /home/odoo/honey-sticks/odoo
source venv/bin/activate
python3 odoo-bin -c odoo.conf -d honey_sticks -i honey_participants,honey_sales,honey_production,honey_logistics,honey_dashboards --stop-after-init

# Запуск сервиса
sudo systemctl start honey-sticks
sudo systemctl status honey-sticks
```

### 8. Настройка веб-сервера (Nginx)

```bash
# Установка Nginx
sudo apt install nginx -y

# Создание конфигурации
sudo cat > /etc/nginx/sites-available/honey-sticks << EOF
upstream honey_sticks {
    server 127.0.0.1:8069;
}

server {
    listen 80;
    server_name your-domain.com;  # Замените на ваш домен

    client_max_body_size 200M;

    location / {
        proxy_pass http://honey_sticks;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /web/static/ {
        proxy_cache_valid 200 90m;
        proxy_buffering on;
        expires 864000;
        proxy_pass http://honey_sticks;
    }
}
EOF

# Активация сайта
sudo ln -s /etc/nginx/sites-available/honey-sticks /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 9. Настройка SSL (Let's Encrypt)

```bash
# Установка Certbot
sudo apt install certbot python3-certbot-nginx -y

# Получение SSL сертификата
sudo certbot --nginx -d your-domain.com

# Автоматическое обновление
sudo crontab -e
# Добавьте строку:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

## Настройка системы

### 1. Первоначальная настройка

1. Откройте браузер и перейдите по адресу: `http://your-domain.com` или `http://localhost:8069`
2. Создайте базу данных с именем `honey_sticks`
3. Установите модули в следующем порядке:
   - honey_participants
   - honey_sales
   - honey_production
   - honey_logistics
   - honey_dashboards

### 2. Настройка ролей пользователей

1. Перейдите в **Настройки > Пользователи и компании > Пользователи**
2. Создайте пользователей для каждой роли:
   - Директор
   - Менеджер продаж
   - Агент продаж
   - Производство
   - Логистика

3. Назначьте соответствующие группы доступа:
   - `Honey Director` - для директора
   - `Honey Manager` - для менеджера
   - `Honey Agent` - для агента
   - `Honey Production` - для производства
   - `Honey Logistics` - для логистики

### 3. Настройка регионов и агентов

1. Перейдите в **Honey Sticks > Participants > Regions**
2. Создайте регионы продаж
3. Назначьте менеджеров регионов
4. Создайте агентов и привяжите их к регионам

### 4. Настройка комиссий

1. Перейдите в **Honey Sticks > Participants > Commission Rules**
2. Создайте правила начисления комиссий
3. Настройте проценты для разных типов клиентов

## Резервное копирование

### Автоматическое резервное копирование

```bash
# Создание скрипта резервного копирования
sudo cat > /home/odoo/backup_honey_sticks.sh << EOF
#!/bin/bash
BACKUP_DIR="/home/odoo/backups"
DATE=\$(date +%Y%m%d_%H%M%S)
DB_NAME="honey_sticks"

# Создание директории для бэкапов
mkdir -p \$BACKUP_DIR

# Создание бэкапа базы данных
pg_dump -h localhost -U odoo \$DB_NAME > \$BACKUP_DIR/\${DB_NAME}_\${DATE}.sql

# Создание бэкапа файлов
tar -czf \$BACKUP_DIR/honey_sticks_files_\${DATE}.tar.gz /home/odoo/honey-sticks/odoo/data

# Удаление старых бэкапов (старше 30 дней)
find \$BACKUP_DIR -name "*.sql" -mtime +30 -delete
find \$BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
EOF

# Права на выполнение
sudo chmod +x /home/odoo/backup_honey_sticks.sh

# Добавление в crontab
sudo crontab -e
# Добавьте строку для ежедневного бэкапа в 2:00:
# 0 2 * * * /home/odoo/backup_honey_sticks.sh
```

## Мониторинг и логи

### Просмотр логов

```bash
# Логи Odoo
sudo journalctl -u honey-sticks -f

# Логи Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Логи PostgreSQL
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

### Мониторинг производительности

```bash
# Установка htop для мониторинга
sudo apt install htop -y

# Мониторинг использования ресурсов
htop

# Мониторинг дискового пространства
df -h

# Мониторинг использования памяти
free -h
```

## Обновление системы

### Обновление модулей

```bash
# Остановка сервиса
sudo systemctl stop honey-sticks

# Создание бэкапа
/home/odoo/backup_honey_sticks.sh

# Обновление кода
cd /home/odoo/honey-sticks/odoo
git pull origin 15.0

# Обновление зависимостей
source venv/bin/activate
pip install -r requirements.txt

# Обновление модулей
python3 odoo-bin -c odoo.conf -d honey_sticks -u all --stop-after-init

# Запуск сервиса
sudo systemctl start honey-sticks
```

## Устранение неполадок

### Частые проблемы

1. **Ошибка подключения к базе данных**
   - Проверьте статус PostgreSQL: `sudo systemctl status postgresql`
   - Проверьте настройки в odoo.conf

2. **Ошибки прав доступа**
   - Проверьте права на файлы: `sudo chown -R odoo:odoo /home/odoo/honey-sticks/`

3. **Проблемы с модулями**
   - Проверьте логи: `sudo journalctl -u honey-sticks -n 100`
   - Переустановите модули: `-i honey_participants,honey_sales,honey_production,honey_logistics,honey_dashboards`

4. **Проблемы с производительностью**
   - Увеличьте количество воркеров в odoo.conf
   - Оптимизируйте настройки PostgreSQL

### Контакты поддержки

- **Email**: support@honeysticks.com
- **Документация**: https://docs.honeysticks.com
- **GitHub**: https://github.com/honeysticks/odoo-system

---

*Версия инструкции: 1.2.0*  
*Дата обновления: 2024*
