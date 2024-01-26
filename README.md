# fts-telegram

> This project is in early development stage, highly experimental.

Telegram crawler for Feats.

## Installation

1. Install [Python 3.11](https://www.python.org/downloads/release/python-3117/) directly or using [pyenv](https://github.com/pyenv/pyenv).
   It still doesn't work with the latest Python 3.12 (some packages don't install).
2. Install [pipx](https://github.com/pypa/pipx).
3. Install this project using pipx:
    ```shell
    pipx install --python python3.11 git+https://github.com/andreoliwa/fts-telegram
   ```
4. Follow the steps to obtain a Telegram API ID and hash on [Creating your Telegram Application](https://core.telegram.org/api/obtaining_api_id).
5. Fill in the environment variables:
    ```shell
    export TELEGRAM_PHONE=+4911999999999
    export TELEGRAM_API_ID=1234567
    export TELEGRAM_API_HASH=1234567890abcdef1234567890abcdef
    export TELEGRAM_PASSWORD=YourPasswordFromTelegramWebsite
    ```
6. On the first execution, `fts-telegram` will use these environment variables to log in and create a `fts-telegram.session` file at the current directory.
7. Occasionally, you will be asked to enter a login code sent to your Telegram.

## Usage

To get help:

```shell
❯ fts-telegram --help
Usage: fts-telegram [OPTIONS] COMMAND [ARGS]...

  Telegram crawler for Feats.

Options:
  --install-completion [bash|zsh|fish|powershell|pwsh]
                                  Install completion for the specified shell.
  --show-completion [bash|zsh|fish|powershell|pwsh]
                                  Show completion for the specified shell, to
                                  copy it or customize the installation.
  --help                          Show this message and exit.

Commands:
  chats     List chats by partial name.
  messages  List messages of multiple chats, as JSON.
```

### Chats

List all chats that contain `blabla` in the name:

```shell
fts-telegram chats blabla
```

For all available options, see:

```shell
fts-telegram chats --help
```

### Messages

Return the last 10 messages of the chat named `mygroup` in JSON format:

```shell
fts-telegram messages mygroup --limit 10
```

The attributes follow [the Message schema](https://schema.org/Message):

```json
{
  "dateSent": "2024-01-26T13:40:52+00:00",
  "identifier": "21086",
  "sender": "Someone",
  "text": "Here's the message from your Telegram chat."
}
```

For all available options, see:

```shell
fts-telegram messages --help
```
