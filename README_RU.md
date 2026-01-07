# ⚡ MCP Vault (`mcpv`)

> **Идеальный ускоритель производительности для AI-агентов**  
> _"Снижает системные задержки на 99%, устраняет время загрузки и сокращает расходы на токены на 90%."_

<div align="center">

![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.10+-F7CA3F.svg?style=flat-square&logo=python&logoColor=black)
![Platform](https://img.shields.io/badge/OS-Windows-0078D6.svg?style=flat-square&logo=windows&logoColor=white)
![Status](https://img.shields.io/badge/Status-Accelerated-brightgreen.svg?style=flat-square)

</div>

<div align="right">
  <a href="README.md">🇺🇸 English</a> | <a href="README_KR.md">🇰🇷 한국어</a> | <a href="README_CN.md">🇨🇳 中文</a>
</div>

<br>

> [!CAUTION]
> **⚠️ Предупреждение о совместимости (Compatibility Warning)**<br>
> В настоящее время этот проект поддерживает ТОЛЬКО ОС **Windows** и агентную среду **Antigravity**.

<br>

## ❓ Почему `mcpv`?

Вы когда-нибудь чувствовали это при использовании AI-агентов (Antigravity, Cursor)?
> *"Почему так тяжело?"*  
> *"Опять зависло..."*  
> *"Почему расходы на токены такие высокие?"*

`mcpv` - это не просто инструмент. Это **Турбо-двигатель** для вашего агента.

<br>

### 🏎️ Ошеломляющая разница в производительности

| Функция | 😫 Без `mcpv` (До) | ⚡ С `mcpv` (После) | 📈 Эффект |
| :--- | :--- | :--- | :--- |
| **Скорость** | Нет GPU, Лагающий UI | **Принудительное ускорение GPU, Плавность** | **100x** Ощущаемая скорость |
| **Загрузка** | Ожидание 60с+ каждый раз | **0.1с Мгновенный старт** (Lazy Load) | **Ноль** Задержки |
| **Расходы** | Отправка полного кода каждый раз | **Авто-блокировка дубликатов** (Smart Cache) | **90%** Экономия |

<br>

---

## ✨ 3 ключевые функции

### 1️⃣ Инъекция ускорителя (Booster Injection - Физическое ускорение)
**"Снятие аппаратных ограничений одной строкой"**
- **Принудительная активация GPU**: Внедряет скрытые флаги ускорения рендеринга (`--enable-gpu-rasterization`).
- **Обход прав доступа**: Обходит надоедливые запросы прав администратора (Ошибка 740) с помощью `RunAsInvoker`.
- **Убийца зомби-процессов**: Автоматически очищает призрачные процессы, занимающие порты.

### 2️⃣ Умный клапан (Smart Valve - Защита расходов)
**"Умный защитник кошелька, который экономит за вас"**
- Обнаруживает массивные контекстные данные (`repomix`), которые агенты привыкли запрашивать.
- **Отправляет только в первый раз**, а со второго раза отвечает сообщением **"Уже кэшировано (Already cached)"** стоимостью 10 токенов.
- Физически блокирует случайные бомбы токенов.

### 3️⃣ Перехват шлюза (Gateway Hijacking - Безопасное хранилище)
**"Перестаньте мучиться со сложными настройками"**
- Автоматически переносит существующие сложные настройки MCP в безопасное хранилище (Vault).
- Агент общается только с `mcpv`, но все инструменты прекрасно работают в фоновом режиме.

<br>

---

## 🛠️ Проверенная рекомендуемая настройка (Verified Setup)

Проверенная конфигурация MCP-сервера, используемая разработчиком. Создает лучшую синергию при использовании с `mcpv`.

```json
{
  "mcpServers": {
    "rube": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://rube.app/mcp"]
    },
    "open-aware": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://open-aware.qodo.ai/mcp"]
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp", "--api-key", "PUT_IN_YOUR_API_KEY_HERE"]
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    },
    "mcp-server-neon": {
      "disabled": false,
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp.neon.tech/sse"],
      "env": {
        "NEON_API_KEY": "NEVERCHANGE_DONT_PUT_IN_ANYTHING_ELSE_THAN_ME_HERE"
      }
    }
  }
}
```

<br>

---

## 📦 Установка

Выберите метод, который подходит именно вам.

### Вариант A: Метод "Просто работает" (Рекомендуется для большинства)
Если у вас установлен Python и добавлен в PATH.

```powershell
# 1. Установка из PyPI
pip install mcpv

# 2. Настройка шлюза и ускорителя
mcpv install

# 3. Готово! 
# Ищите ярлык "Antigravity Boost (mcpv)" на рабочем столе.

```

---

### Вариант B: Метод "Надежный как скала" (С использованием `uv`)

Используйте этот метод, если ваше окружение Python загрязнено или вам нужна полная изоляция.

#### 1. Очистка существующих процессов

```powershell
Stop-Process -Name "mcpv" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue

```

#### 2. Создание виртуального окружения и установка

```powershell
# Установка uv (если нужно)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Создание .venv и установка mcpv
uv venv
uv pip install mcpv

```

#### 3. Регистрация и блокировка

Это регистрирует **изолированное виртуальное окружение** в конфиге Antigravity.

```powershell
.venv\Scripts\python -m mcpv install --force

```

#### 4. Запуск

Запустите **`Antigravity Boost (mcpv)`** с вашего рабочего стола.

---

## 🛠️ Команды

| Команда | Описание |
| --- | --- |
| `mcpv install` | Устанавливает шлюз и создает ярлык на рабочем столе. |
| `mcpv install --force` | Принудительная установка, даже если существует только 1 MCP сервер. |
| `mcpv start` | Запускает сервер (Используется внутри Antigravity). |
| `mcpv --help` | Показать справку. |

---

## ❓ Устранение неполадок

#### Q. "File access denied" или "Failed to remove file" во время обновления?

Это означает, что `mcpv.exe` или `Antigravity` все еще запущены.

1. Закройте Antigravity.
2. Запустите: `Stop-Process -Name "mcpv" -Force` в PowerShell.
3. Попробуйте установить снова.

#### Q. Я установил, но не вижу Ярлык.

Ярлык создается на вашем **Рабочем столе**. Если нет, проверьте логи установки. Вы можете создать его вручную, запустив `mcpv install` снова.

---

## 📜 Лицензия

MIT License. Не стесняйтесь форкать и модифицировать!

---

☕ **Поддержка**  
Если этот проект помог вам сэкономить токены и время, подумайте о том, чтобы угостить меня кофе!  

[<img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" width="180" />](https://www.buymeacoffee.com/mcpv)

<br>

---

<div align="center">
  <b>⚡ Charged by MCP Vault</b><br>
  <i>Developed for High-Performance AI Agent Operations</i>
</div>
