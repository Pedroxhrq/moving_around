# Moving Around

## English

`move_when_idle.py` is a small Windows Python script that watches your mouse cursor and moves it only when the cursor has been idle for more than one minute.

The script does not click, drag, type, or interact with windows. It only changes the cursor position.

### Behavior

- Runs only during these local time windows:
  - 08:00 to 12:00
  - 13:12 to 18:00
- Starts counting idle time when the cursor is not moving.
- After 60 seconds of no cursor movement, it starts moving the cursor in smooth, human-like paths.
- If you move the mouse at any time, the automatic movement pauses immediately.
- After your mouse stops again, the script starts a new 60-second idle countdown.
- Outside the configured time windows, the script stays running but does not move the cursor.
- If Windows is locked, the script pauses until the session is unlocked, then resumes without counting the locked time as idle time.
- CLI action messages include the local time in `HH:MM:SS` format.

### Requirements

- Windows
- Python 3.10 or newer

The script uses the Windows cursor API through Python's built-in `ctypes` module, so no external Python packages are required.

### How to Run

From the `Dev` folder, run:

```powershell
python .\moving_around\move_when_idle.py
```

Or, from inside the `moving_around` folder, run:

```powershell
python .\move_when_idle.py
```

### How to Stop

Press `Ctrl+C` in the terminal where the script is running.

### Configuration

The main settings are near the top of `move_when_idle.py`:

```python
IDLE_SECONDS = 60
POLL_SECONDS = 0.5
USER_MOVE_TOLERANCE_PIXELS = 4

ACTIVE_WINDOWS = (
    (time(8, 0), time(12, 0)),
    (time(13, 12), time(18, 0)),
)
```

You can edit these values to change the idle delay, polling frequency, mouse movement tolerance, or active time windows.

---

## Português do Brasil

`move_when_idle.py` é um pequeno script Python para Windows que monitora o cursor do mouse e só move o cursor quando ele fica parado por mais de um minuto.

O script não clica, não arrasta, não digita e não interage com janelas. Ele apenas muda a posição do cursor.

### Comportamento

- Funciona apenas nestas janelas de horário local:
  - 08:00 até 12:00
  - 13:12 até 18:00
- Começa a contar o tempo ocioso quando o cursor não está se movendo.
- Depois de 60 segundos sem movimento do cursor, começa a mover o cursor com trajetórias suaves e parecidas com movimento humano.
- Se você mover o mouse em qualquer momento, o movimento automático pausa imediatamente.
- Depois que o mouse parar novamente, o script começa uma nova contagem de 60 segundos.
- Fora das janelas de horário configuradas, o script continua rodando, mas não move o cursor.
- Se o Windows estiver bloqueado, o script pausa até a sessão ser desbloqueada e depois continua sem contar o tempo bloqueado como tempo ocioso.
- As mensagens de ação no CLI incluem o horário local no formato `HH:MM:SS`.

### Requisitos

- Windows
- Python 3.10 ou mais recente

O script usa a API de cursor do Windows através do módulo `ctypes`, que já vem com o Python. Por isso, nenhum pacote externo é necessário.

### Como Executar

A partir da pasta `Dev`, execute:

```powershell
python .\moving_around\move_when_idle.py
```

Ou, de dentro da pasta `moving_around`, execute:

```powershell
python .\move_when_idle.py
```

### Como Parar

Pressione `Ctrl+C` no terminal onde o script está rodando.

### Configuração

As principais configurações ficam no começo do arquivo `move_when_idle.py`:

```python
IDLE_SECONDS = 60
POLL_SECONDS = 0.5
USER_MOVE_TOLERANCE_PIXELS = 4

ACTIVE_WINDOWS = (
    (time(8, 0), time(12, 0)),
    (time(13, 12), time(18, 0)),
)
```

Você pode editar esses valores para mudar o tempo de espera, a frequência de verificação, a tolerância de movimento do mouse ou as janelas de horário ativas.
