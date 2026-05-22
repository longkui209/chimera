# ============================================================
# Chimera Makefile
# ============================================================

.PHONY: help install test serve daemon stop status scan doctor clean lint loc

PROJECT := chimera
PYTHON := python3
PIP := pip3
PORT := 8004
HOST := 0.0.0.0

# 默认目标
help:
	@echo "🦁🐐🐍  Chimera Makefile"
	@echo ""
	@echo "用法: make <target>"
	@echo ""
	@echo "开发:"
	@echo "  install     安装依赖"
	@echo "  test        运行测试"
	@echo "  serve       启动 API 服务（前台）"
	@echo "  daemon      启动后台服务"
	@echo "  stop        停止服务"
	@echo "  status      服务状态"
	@echo ""
	@echo "诊断:"
	@echo "  scan        扫描工具链"
	@echo "  doctor      系统诊断"
	@echo "  loc         统计代码行数"
	@echo "  lint        代码检查"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build   构建镜像"
	@echo "  docker-up      启动容器"
	@echo "  docker-down    停止容器"

# === 开发 ===

install:
	@echo "📦 安装依赖..."
	$(PIP) install -r requirements.txt
	@echo "✅ 完成"

test:
	@echo "🧪 运行测试..."
	$(PYTHON) -m pytest tests/test_core.py -v --tb=short \
		-k "not test_discover_games and not test_analyze_ittakestwo and not test_extract_ittakestwo and not test_full_pipeline_mock"

test-all:
	@echo "🧪 运行全部测试..."
	$(PYTHON) -m pytest tests/test_core.py -v --tb=short

test-quick:
	@echo "🧪 快速测试..."
	$(PYTHON) -m pytest tests/test_core.py -q --tb=line \
		-k "not discover_games and not analyze_ittakestwo and not extract_ittakestwo and not full_pipeline"

serve:
	@echo "🚀 启动 Chimera API 服务..."
	$(PYTHON) cli.py serve --reload

daemon:
	@echo "🔧 后台启动..."
	bash scripts/start.sh daemon

stop:
	bash scripts/start.sh stop

status:
	bash scripts/start.sh status

# === 诊断 ===

scan:
	$(PYTHON) cli.py scan

doctor:
	$(PYTHON) cli.py doctor

loc:
	@echo "📊 Chimera 代码统计"
	@echo "===================="
	@echo -n "Python:    "; find . -name "*.py" -not -path "*__pycache__*" -exec cat {} \; | wc -l
	@echo -n "Shell:     "; find . -name "*.sh" -exec cat {} \; | wc -l
	@echo -n "HTML/CSS:  "; find . -name "*.html" -exec cat {} \; | wc -l
	@echo -n "YAML:      "; find . -name "*.yml" -o -name "*.yaml" | xargs cat 2>/dev/null | wc -l
	@echo -n "Docker:    "; find . -name "Dockerfile" -exec cat {} \; | wc -l
	@echo -n "Config:    "; find . -name "*.conf" -o -name "*.cfg" -o -name "*.ini" | xargs cat 2>/dev/null | wc -l
	@echo -n "Make:      "; cat Makefile | wc -l
	@echo -n "README:    "; cat README.md | wc -l
	@echo "===================="
	@echo -n "总行数:    "; find . -type f \( -name "*.py" -o -name "*.sh" -o -name "*.html" -o -name "*.yml" -o -name "*.md" -o -name "*.conf" -o -name "Dockerfile" -o -name "Makefile" \) -not -path "*__pycache__*" -not -path "*pytest_cache*" -exec cat {} \; 2>/dev/null | wc -l
	@echo -n "文件数:    "; find . -type f \( -name "*.py" -o -name "*.sh" -o -name "*.html" -o -name "*.yml" -o -name "*.md" -o -name "*.conf" -o -name "Dockerfile" -o -name "Makefile" \) -not -path "*__pycache__*" -not -path "*pytest_cache*" | wc -l

lint:
	@echo "🔍 代码检查..."
	$(PYTHON) -m flake8 agents/ core/ api/ --max-line-length=120 --ignore=E501,W503,E203 2>/dev/null || true
	@echo "✅ 完成（忽略风格警告）"

# === Docker ===

docker-build:
	docker-compose -f docker/docker-compose.yml build

docker-up:
	docker-compose -f docker/docker-compose.yml up -d chimera
	@echo "✅ Chimera 已启动: http://localhost:$(PORT)"

docker-down:
	docker-compose -f docker/docker-compose.yml down

docker-logs:
	docker-compose -f docker/docker-compose.yml logs -f chimera

# === 清理 ===

clean:
	@echo "🧹 清理..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ 完成"

clean-all: clean
	rm -rf knowledge/*.jsonl 2>/dev/null || true
	rm -rf logs/*.log 2>/dev/null || true
	rm -f /tmp/chimera.pid
	@echo "✅ 全部清理完成"
