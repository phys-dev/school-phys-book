# Сборка пособия. Используйте `make` для обычной сборки и `make clean build`
# после правок в пакете phys/ — Sphinx не отслеживает изменения в нём сам.

PY := .venv/bin/python
JB := .venv/bin/jupyter-book

.PHONY: build clean rebuild serve open lessons

build:            ## собрать сайт в _build/html
	$(JB) build .

clean:            ## удалить результаты сборки и кэш выполнения тетрадей
	rm -rf _build

rebuild: clean build   ## полная пересборка (нужна после правок в phys/)

serve: build      ## поднять локальный сервер на http://localhost:8321 (Ctrl+C — остановить)
	@echo "Сайт: http://localhost:8321  —  остановить: Ctrl+C"
	$(PY) -m http.server 8321 --directory _build/html

open: build       ## просто открыть готовый сайт в браузере, без сервера
	open _build/html/index.html

lessons:          ## пересобрать тетради из исходников MyST, если они используются
	@echo "Уроки хранятся в lessons/*.ipynb и правятся напрямую в JupyterLab"
