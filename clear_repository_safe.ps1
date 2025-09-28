# Безопасный PowerShell скрипт для очистки GitHub репозитория
# Использует orphan ветку для полной очистки истории
# Запустите в PowerShell: .\clear_repository_safe.ps1

Write-Host "🗑️ Безопасная очистка GitHub репозитория..." -ForegroundColor Red

# Переходим в папку проекта
Set-Location "C:\Users\Dev-Ops\Desktop\odoo"

# Проверяем, что мы в Git репозитории
if (-not (Test-Path ".git")) {
    Write-Host "❌ Это не Git репозиторий! Инициализируем..." -ForegroundColor Yellow
    git init
}

# Добавляем удаленный репозиторий
Write-Host "🔗 Подключение к GitHub репозиторию..." -ForegroundColor Yellow
git remote remove origin 2>$null
git remote add origin https://github.com/ahmed11551/custom-core-odoo.git

# Создаем orphan ветку (без истории)
Write-Host "🌿 Создание новой ветки без истории..." -ForegroundColor Yellow
git checkout --orphan new-main

# Удаляем все файлы
Write-Host "🗑️ Удаление всех файлов..." -ForegroundColor Yellow
git rm -rf . 2>$null

# Создаем пустой README
Write-Host "📄 Создание пустого README..." -ForegroundColor Yellow
@"
# Custom Core Odoo

Репозиторий готов для загрузки нового проекта.

## Готов к использованию

Этот репозиторий был очищен и готов для загрузки нового проекта Honey Sticks Management System.

"@ | Out-File -FilePath "README.md" -Encoding UTF8

# Создаем .gitignore
Write-Host "📋 Создание .gitignore..." -ForegroundColor Yellow
@"
# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
*.so
*.egg-info/
dist/
build/

# Odoo
*.log
*.pot
*.mo
.installed.cfg

# Environment
.env
.venv/
venv/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Database
*.db
*.sqlite3
"@ | Out-File -FilePath ".gitignore" -Encoding UTF8

# Добавляем файлы
Write-Host "📦 Добавление файлов в Git..." -ForegroundColor Yellow
git add .

# Создаем первый коммит
Write-Host "💾 Создание первого коммита..." -ForegroundColor Yellow
git commit -m "Initial commit - empty repository ready for new project"

# Переименовываем ветку в main
Write-Host "🌿 Переименование ветки в main..." -ForegroundColor Yellow
git branch -M main

# Отправляем в GitHub
Write-Host "⬆️ Отправка в GitHub..." -ForegroundColor Yellow
git push origin main --force

Write-Host "✅ Репозиторий успешно очищен!" -ForegroundColor Green
Write-Host "🌐 Проверьте: https://github.com/ahmed11551/custom-core-odoo" -ForegroundColor Cyan
Write-Host "📋 Репозиторий теперь пустой и готов для нового проекта" -ForegroundColor White

Write-Host "`n🚀 Для загрузки нового проекта используйте:" -ForegroundColor Cyan
Write-Host "   .\deploy_to_github.ps1" -ForegroundColor White
