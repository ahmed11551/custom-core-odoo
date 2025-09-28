# PowerShell скрипт для очистки GitHub репозитория
# Запустите в PowerShell: .\clear_repository.ps1

Write-Host "🗑️ Очистка GitHub репозитория..." -ForegroundColor Red

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

# Создаем пустой коммит для очистки
Write-Host "📝 Создание пустого коммита..." -ForegroundColor Yellow

# Удаляем все файлы кроме .git
Get-ChildItem -Path . -Exclude .git | Remove-Item -Recurse -Force

# Создаем пустой README
Write-Host "📄 Создание пустого README..." -ForegroundColor Yellow
@"
# Custom Core Odoo

Репозиторий готов для загрузки нового проекта.

"@ | Out-File -FilePath "README.md" -Encoding UTF8

# Добавляем .gitignore
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

# Добавляем все изменения
Write-Host "📦 Добавление изменений в Git..." -ForegroundColor Yellow
git add .

# Создаем коммит
Write-Host "💾 Создание коммита очистки..." -ForegroundColor Yellow
git commit -m "Clear repository - ready for new project"

# Принудительно отправляем в GitHub (перезаписываем историю)
Write-Host "⬆️ Отправка в GitHub (перезапись истории)..." -ForegroundColor Yellow
git push origin main --force

Write-Host "✅ Репозиторий успешно очищен!" -ForegroundColor Green
Write-Host "🌐 Проверьте: https://github.com/ahmed11551/custom-core-odoo" -ForegroundColor Cyan
Write-Host "📋 Теперь репозиторий пустой и готов для нового проекта" -ForegroundColor White

Write-Host "`n🚀 Для загрузки нового проекта используйте:" -ForegroundColor Cyan
Write-Host "   .\deploy_to_github.ps1" -ForegroundColor White
