
# Скрипт для очистки репозитория через веб-интерфейс GitHub
# Запустите в PowerShell: .\clear_repository_web.ps1

Write-Host "🌐 Инструкция по очистке репозитория через веб-интерфейс" -ForegroundColor Cyan

Write-Host "`n📋 Пошаговая инструкция:" -ForegroundColor Yellow
Write-Host "1. Откройте https://github.com/ahmed11551/custom-core-odoo" -ForegroundColor White
Write-Host "2. Перейдите в Settings (настройки)" -ForegroundColor White
Write-Host "3. Прокрутите вниз до раздела 'Danger Zone'" -ForegroundColor White
Write-Host "4. Нажмите 'Delete this repository'" -ForegroundColor White
Write-Host "5. Введите название репозитория для подтверждения" -ForegroundColor White
Write-Host "6. Нажмите 'I understand the consequences, delete this repository'" -ForegroundColor White

Write-Host "`n🔄 После удаления создайте новый репозиторий:" -ForegroundColor Yellow
Write-Host "1. Перейдите на https://github.com/new" -ForegroundColor White
Write-Host "2. Название: custom-core-odoo" -ForegroundColor White
Write-Host "3. Описание: Honey Sticks Management System" -ForegroundColor White
Write-Host "4. Сделайте репозиторий Public" -ForegroundColor White
Write-Host "5. НЕ добавляйте README, .gitignore или лицензию" -ForegroundColor White
Write-Host "6. Нажмите 'Create repository'" -ForegroundColor White

Write-Host "`n🚀 После создания пустого репозитория запустите:" -ForegroundColor Green
Write-Host "   .\deploy_to_github.ps1" -ForegroundColor White

Write-Host "`n⚠️  Альтернативный способ (через Git):" -ForegroundColor Red
Write-Host "   .\clear_repository_safe.ps1" -ForegroundColor White

# Открываем репозиторий в браузере
Write-Host "`n🌐 Открываю репозиторий в браузере..." -ForegroundColor Cyan
Start-Process "https://github.com/ahmed11551/custom-core-odoo"
