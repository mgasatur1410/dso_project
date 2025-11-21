# AppArmor Profile для secdev-app

## Установка (только Linux)

```bash
# 1. Копировать профиль в системную директорию
sudo cp docker-secdev-app /etc/apparmor.d/

# 2. Загрузить профиль
sudo apparmor_parser -r -W /etc/apparmor.d/docker-secdev-app

# 3. Проверить загрузку
sudo aa-status | grep docker-secdev-app
```

## Проверка применения

```bash
# Запустить контейнер
docker compose up -d

# Проверить AppArmor profile
docker inspect secdev-app --format '{{.AppArmorProfile}}'
# Ожидается: docker-secdev-app
```

## Отладка

```bash
# Режим complain (логировать нарушения без блокировки)
sudo aa-complain /etc/apparmor.d/docker-secdev-app

# Просмотр логов нарушений
sudo journalctl -xe | grep apparmor

# Вернуть в режим enforce
sudo aa-enforce /etc/apparmor.d/docker-secdev-app
```

## Примечание для Windows/Mac

AppArmor доступен только на Linux. На Windows/Mac Docker использует виртуализацию (WSL2/HyperKit), где AppArmor может быть недоступен.

Для демонстрации на Windows/Mac можно:
1. Закомментировать `apparmor=docker-secdev-app` в `compose.yaml`
2. Показать файл профиля преподавателю
3. Объяснить что профиль готов для Linux-продакшена
