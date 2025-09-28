# 🚀 Развертывание Honey Sticks Management System

## На Railway (Рекомендуется)

### Быстрое развертывание

1. **Подготовка репозитория**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Honey Sticks Management System"
   git branch -M main
   git remote add origin https://github.com/ahmed11551/custom-core-odoo.git
   git push -u origin main
   ```

2. **Создание проекта на Railway**
   - Перейдите на [railway.app](https://railway.app)
   - Войдите в аккаунт
   - Нажмите "New Project"
   - Выберите "Deploy from GitHub repo"
   - Подключите репозиторий `ahmed11551/custom-core-odoo`

3. **Настройка базы данных**
   - В проекте Railway добавьте PostgreSQL
   - Railway автоматически создаст переменные окружения

4. **Переменные окружения**
   Railway автоматически настроит:
   - `RAILWAY_DATABASE_HOST`
   - `RAILWAY_DATABASE_NAME`
   - `RAILWAY_DATABASE_PASSWORD`
   - `RAILWAY_DATABASE_PORT`
   - `RAILWAY_DATABASE_USER`
   - `PORT`

5. **Развертывание**
   - Railway автоматически развернет проект
   - Получите URL через 2-3 минуты
   - Система будет доступна по адресу: `https://your-project.railway.app`

### Первоначальная настройка

1. **Вход в систему**
   - Откройте URL вашего проекта
   - Создайте базу данных
   - Установите пароль администратора

2. **Установка модулей**
   - Перейдите в "Apps"
   - Найдите "Honey Sticks Management System"
   - Установите модуль

3. **Настройка пользователей**
   - Создайте пользователей для каждой роли:
     - Директор
     - Менеджер продаж
     - Агент продаж
     - Производство
     - Логистика

4. **Настройка регионов**
   - Перейдите в "Honey Sticks" → "Participants" → "Regions"
   - Создайте регионы продаж

5. **Настройка агентов**
   - Перейдите в "Honey Sticks" → "Participants" → "Agents"
   - Создайте агентов продаж

## Локальное развертывание

### Требования
- Python 3.8+
- PostgreSQL 12+
- Odoo 15.0+

### Установка

1. **Клонирование репозитория**
   ```bash
   git clone https://github.com/ahmed11551/custom-core-odoo.git
   cd custom-core-odoo
   ```

2. **Установка зависимостей**
   ```bash
   pip install -r requirements.txt
   ```

3. **Настройка базы данных**
   ```bash
   createdb honey_sticks
   ```

4. **Запуск Odoo**
   ```bash
   odoo --config=odoo.conf
   ```

5. **Открытие в браузере**
   - Перейдите на http://localhost:8069
   - Создайте базу данных
   - Установите модули

## Структура проекта

```
custom-core-odoo/
├── custom_addons/           # Кастомные модули
│   ├── honey_participants/  # Управление участниками
│   ├── honey_sales/         # Продажи и комиссии
│   ├── honey_production/    # Производство с HACCP
│   ├── honey_logistics/     # Логистика
│   ├── honey_dashboards/    # Дашборды по ролям
│   ├── honey_whatsapp/      # WhatsApp интеграция
│   └── honey_reports/       # Отчёты и печать
├── odoo.conf               # Конфигурация Odoo
├── requirements.txt        # Python зависимости
├── railway.json           # Конфигурация Railway
├── Procfile              # Команда запуска
└── README.md             # Документация
```

## Поддержка

При возникновении проблем:
1. Проверьте логи в Railway
2. Убедитесь, что все модули установлены
3. Проверьте права доступа пользователей
4. Обратитесь к документации Odoo

## Обновление

Для обновления системы:
1. Обновите код в репозитории
2. Railway автоматически переразвернет проект
3. Обновите модули в Odoo

---

**Система готова к работе!** 🍯
