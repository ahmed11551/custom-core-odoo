# PowerShell скрипт для загрузки проекта в GitHub
# Запустите в PowerShell: .\deploy_to_github.ps1

Write-Host "🚀 Загрузка Honey Sticks Management System в GitHub..." -ForegroundColor Green

# Переходим в папку проекта
Set-Location "C:\Users\Dev-Ops\Desktop\odoo"

# Инициализируем Git репозиторий
Write-Host "📁 Инициализация Git репозитория..." -ForegroundColor Yellow
git init

# Добавляем все файлы
Write-Host "📦 Добавление файлов в Git..." -ForegroundColor Yellow
git add .

# Создаем коммит
Write-Host "💾 Создание коммита..." -ForegroundColor Yellow
git commit -m "Initial commit: Honey Sticks Management System v1.2 - Complete production system with HACCP control, WhatsApp integration, and payment-based commissions"

# Устанавливаем основную ветку
Write-Host "🌿 Настройка основной ветки..." -ForegroundColor Yellow
git branch -M main

# Добавляем удаленный репозиторий
Write-Host "🔗 Подключение к GitHub репозиторию..." -ForegroundColor Yellow
git remote add origin https://github.com/ahmed11551/custom-core-odoo.git

# Загружаем в GitHub
Write-Host "⬆️ Загрузка в GitHub..." -ForegroundColor Yellow
git push -u origin main

Write-Host "✅ Проект успешно загружен в GitHub!" -ForegroundColor Green
Write-Host "🌐 Теперь можно развернуть на Railway:" -ForegroundColor Cyan
Write-Host "   1. Перейдите на https://railway.app" -ForegroundColor White
Write-Host "   2. Создайте новый проект" -ForegroundColor White
Write-Host "   3. Подключите GitHub репозиторий" -ForegroundColor White
Write-Host "   4. Добавьте PostgreSQL базу данных" -ForegroundColor White
Write-Host "   5. Railway автоматически развернет систему!" -ForegroundColor White

Write-Host "📋 Структура проекта:" -ForegroundColor Cyan
Write-Host "   - custom_addons/ - Все модули системы" -ForegroundColor White
Write-Host "   - odoo.conf - Конфигурация для Railway" -ForegroundColor White
Write-Host "   - requirements.txt - Python зависимости" -ForegroundColor White
Write-Host "   - railway.json - Настройки Railway" -ForegroundColor White
Write-Host "   - Procfile - Команда запуска" -ForegroundColor White

Write-Host "🍯 Система готова к развертыванию!" -ForegroundColor Green
