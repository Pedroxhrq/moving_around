# Moving Around

## English

`move_when_idle.py` is a small Windows Python script that watches the Windows keyboard/mouse idle state and moves the cursor only when there has been no user input for the configured amount of time.

The script does not click, drag, type, or interact with windows. It only changes the cursor position.

### Behavior

- Runs only during the local time windows configured in `move_when_idle_config.json`.
- Starts counting idle time when Windows receives no keyboard or mouse input.
- After 60 seconds of no keyboard or mouse input by default, it starts moving the cursor in smooth, human-like paths.
- If you use the keyboard or mouse at any time, the automatic movement pauses immediately.
- After input stops again, the script starts a new idle countdown.
- Outside the configured time windows, the script stays running but does not move the cursor.
- If the Windows session is confirmed locked, the script pauses until a confirmed unlock, then resumes without counting the paused time as active work. Ordinary keyboard/mouse idle time is not treated as a lock. Recurring lock-status messages are printed only during configured active time windows.
- CLI action messages include the local time in `HH:MM:SS` format by default. Set `log_include_date` to `true` to print `YYYY-MM-DD HH:MM:SS`.
- When the script stops, it prints the session totals for `IDLE` and `not IDLE` in `HH:MM:SS` format. `IDLE` begins when the configured idle threshold is reached; lock-screen time is excluded from both totals.
- Session totals cover all unlocked runtime, including periods outside the configured active time windows.

### Requirements

- Windows
- Python 3.10 or newer

The script uses Windows APIs through Python's built-in `ctypes` module, so no external Python packages are required.

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

The final log entry shows the session totals, for example:

```text
[18:03:27] Session totals (lock-screen time excluded): IDLE 00:42:18; not IDLE 01:16:09.
```

### Configuration

Edit `move_when_idle_config.json` to change the idle delay, polling frequency, lock-screen polling, log format, movement tolerance, or active time windows:

```json
{
  "idle_seconds": 60,
  "poll_seconds": 0.5,
  "lock_poll_seconds": 1.0,
  "lock_status_log_seconds": 60,
  "user_move_tolerance_pixels": 4,
  "log_include_date": false,
  "active_windows": [
    {
      "start": "08:00",
      "end": "12:00"
    },
    {
      "start": "13:12",
      "end": "18:00"
    }
  ]
}
```

Times use `HH:MM` format. End times are exclusive.

### Troubleshooting

If running `python` opens the Microsoft Store, fails through `C:\Users\<you>\AppData\Local\Microsoft\WindowsApps\python.exe`, or shows a logon-session error, Windows is using the Python app execution alias instead of a real Python install.

Check what is being launched:

```powershell
where.exe python
```

Install Python from python.org, or disable the `python.exe` and `python3.exe` app execution aliases in Windows Settings > Apps > Advanced app settings > App execution aliases. You can also run the script with the full path to a real Python executable.

---

## Português do Brasil

`move_when_idle.py` é um pequeno script Python para Windows que monitora o estado de ociosidade do teclado e do mouse no Windows e só move o cursor quando não há entrada do usuário pelo tempo configurado.

O script não clica, não arrasta, não digita e não interage com janelas. Ele apenas muda a posição do cursor.

### Comportamento

- Funciona apenas nas janelas de horário local configuradas em `move_when_idle_config.json`.
- Começa a contar o tempo ocioso quando o Windows não recebe entrada de teclado ou mouse.
- Depois de 60 segundos sem entrada de teclado ou mouse por padrão, começa a mover o cursor com trajetórias suaves e parecidas com movimento humano.
- Se você usar o teclado ou o mouse em qualquer momento, o movimento automático pausa imediatamente.
- Depois que a entrada parar novamente, o script começa uma nova contagem de ociosidade.
- Fora das janelas de horário configuradas, o script continua rodando, mas não move o cursor.
- Se a sessão do Windows estiver confirmadamente bloqueada, o script pausa até o desbloqueio ser confirmado e depois continua sem contar o tempo pausado como trabalho ativo. A ociosidade normal do teclado e do mouse não é tratada como bloqueio. As mensagens periódicas sobre o bloqueio são exibidas apenas durante as janelas de horário ativas configuradas.
- As mensagens de ação no CLI incluem o horário local no formato `HH:MM:SS` por padrão. Defina `log_include_date` como `true` para imprimir `YYYY-MM-DD HH:MM:SS`.
- Quando o script para, ele mostra os totais da sessão para `IDLE` e `not IDLE` no formato `HH:MM:SS`. O tempo `IDLE` começa quando o limite de ociosidade configurado é atingido; o tempo da tela bloqueada não entra em nenhum dos totais.
- Os totais da sessão cobrem todo o tempo desbloqueado, inclusive os períodos fora das janelas de horário ativas configuradas.

### Requisitos

- Windows
- Python 3.10 ou mais recente

O script usa APIs do Windows através do módulo `ctypes`, que já vem com o Python. Por isso, nenhum pacote externo é necessário.

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

A última entrada do log mostra os totais da sessão, por exemplo:

```text
[18:03:27] Session totals (lock-screen time excluded): IDLE 00:42:18; not IDLE 01:16:09.
```

### Configuração

Edite `move_when_idle_config.json` para mudar o tempo de espera, a frequência de verificação, a verificação de tela bloqueada, o formato do log, a tolerância de movimento do mouse ou as janelas de horário ativas:

```json
{
  "idle_seconds": 60,
  "poll_seconds": 0.5,
  "lock_poll_seconds": 1.0,
  "lock_status_log_seconds": 60,
  "user_move_tolerance_pixels": 4,
  "log_include_date": false,
  "active_windows": [
    {
      "start": "08:00",
      "end": "12:00"
    },
    {
      "start": "13:12",
      "end": "18:00"
    }
  ]
}
```

Os horários usam o formato `HH:MM`. Os horários de fim são exclusivos.

### Solução de Problemas

Se executar `python` abrir a Microsoft Store, falhar através de `C:\Users\<você>\AppData\Local\Microsoft\WindowsApps\python.exe`, ou mostrar erro de sessão de logon, o Windows está usando o alias de execução de aplicativo do Python em vez de uma instalação real do Python.

Verifique o que está sendo executado:

```powershell
where.exe python
```

Instale o Python pelo python.org, ou desative os aliases `python.exe` e `python3.exe` em Configurações do Windows > Aplicativos > Configurações avançadas de aplicativos > Aliases de execução de aplicativo. Você também pode executar o script com o caminho completo para um executável real do Python.
