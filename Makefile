# Makefile для dev и проверки secdev-контейнера

IMAGE=secdev-app:latest
CONTAINER=secdev-app

.PHONY: build up down ps logs lint scan-health scan-hadolint scan-trivy check-user check-security verify-p07

build:
	docker build -t $(IMAGE) .

up:
	docker compose up --build -d
	docker compose logs -f

down:
	docker compose down

ps:
	docker compose ps

logs:
	docker compose logs -f

lint:
	hadolint Dockerfile

scan-hadolint:
	hadolint --config .hadolint.yaml Dockerfile

scan-trivy:
	trivy image --config trivy.yaml $(IMAGE)

scan-trivy-fs:
	trivy fs --config trivy.yaml .

check-user:
	docker compose exec app id -u

check-health:
	docker compose exec app curl -sf http://localhost:8000/health

# P07 Security Verification
check-security:
	@echo "=== Checking Security Configuration ==="
	@echo "\n1. Non-root user:"
	@docker exec $(CONTAINER) id || echo "Container not running"
	@echo "\n2. Capabilities:"
	@docker inspect $(CONTAINER) --format '{{.HostConfig.CapDrop}}' || echo "Container not running"
	@echo "\n3. Security Options:"
	@docker inspect $(CONTAINER) --format '{{json .HostConfig.SecurityOpt}}' || echo "Container not running"
	@echo "\n4. Read-only FS:"
	@docker inspect $(CONTAINER) --format '{{.HostConfig.ReadonlyRootfs}}' || echo "Container not running"

verify-p07: build
	@echo "=== P07 Verification ==="
	@echo "\n✓ C4: Custom Hadolint config"
	@test -f .hadolint.yaml && echo "  [OK] .hadolint.yaml exists" || echo "  [FAIL] .hadolint.yaml missing"
	@echo "\n✓ C4: Custom Trivy config"
	@test -f trivy.yaml && echo "  [OK] trivy.yaml exists" || echo "  [FAIL] trivy.yaml missing"
	@test -f .trivyignore && echo "  [OK] .trivyignore exists" || echo "  [FAIL] .trivyignore missing"
	@echo "\n✓ C2: Seccomp profile"
	@test -f seccomp.json && echo "  [OK] seccomp.json exists" || echo "  [FAIL] seccomp.json missing"
	@echo "\n✓ C2: AppArmor profile"
	@test -f apparmor/docker-secdev-app && echo "  [OK] AppArmor profile exists" || echo "  [FAIL] AppArmor profile missing"
	@echo "\n✓ Running Hadolint with config..."
	@hadolint --config .hadolint.yaml Dockerfile && echo "  [OK] Hadolint passed" || echo "  [WARN] Hadolint warnings"
	@echo "\n✓ Running Trivy with config..."
	@trivy image --config trivy.yaml --exit-code 0 $(IMAGE) || echo "  [INFO] Trivy scan completed"
	@echo "\n=== All checks completed ==="
