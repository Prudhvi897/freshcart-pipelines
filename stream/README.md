# RabbitMQ stream setup

This directory contains the assignment dispatcher and topic-based consumer drivers for the FreshCart order stream.

## Assignment routing patterns

| Driver | Binding pattern |
|---|---|
| Ravi | `bangalore.koramangala.*` |
| Priya | `bangalore.indiranagar.*` |
| Arjun | `bangalore.*.ride` |
| Meena | `bangalore.*.food` |
| Karthik | `chennai.tnagar.food` |
| Control | `bangalore.#` |

For the assignment's D1 routing keys, the expected recipients are:

| Routing key | Expected queue(s) |
|---|---|
| `bangalore.koramangala.food` | Ravi, Meena, Control |
| `bangalore.indiranagar.ride` | Priya, Arjun, Control |
| `bangalore.whitefield.ride` | Arjun, Control |
| `chennai.tnagar.food` | Karthik |
| `chennai.whitefield.ride` | dropped |
| `bangalore.koramangala` | Control |

`*` matches exactly one word; `#` matches zero or more words. The two-word final key matches Control's `bangalore.#`: the `#` consumes the one remaining word, `koramangala`.

## Start RabbitMQ locally

In PowerShell with Docker Desktop running:

```powershell
docker run -d --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
Test-NetConnection localhost -Port 5672
```

## Run the dispatcher

In a separate terminal:

```powershell
$env:RABBITMQ_URL = "amqp://localhost:5672/"
python stream/dispatcher.py
```

The dispatcher sends JSON messages every 2 seconds to the `rapido-dispatch` topic exchange. Every 10th message is intentionally malformed and missing `zone` to exercise the NACK path.

## Run three or more drivers for two minutes

In separate terminals, start at least three drivers. For full D1 coverage, start all six:

```powershell
$env:RABBITMQ_URL = "amqp://localhost:5672/"
python stream/driver.py Ravi "bangalore.koramangala.*"
```

```powershell
$env:RABBITMQ_URL = "amqp://localhost:5672/"
python stream/driver.py Priya "bangalore.indiranagar.*"
```

```powershell
$env:RABBITMQ_URL = "amqp://localhost:5672/"
python stream/driver.py Arjun "bangalore.*.ride"
```

```powershell
$env:RABBITMQ_URL = "amqp://localhost:5672/"
python stream/driver.py Meena "bangalore.*.food"
```

```powershell
$env:RABBITMQ_URL = "amqp://localhost:5672/"
python stream/driver.py Karthik "chennai.tnagar.food"
```

```powershell
$env:RABBITMQ_URL = "amqp://localhost:5672/"
python stream/driver.py Control "bangalore.#"
```

Let the dispatcher and drivers run for two minutes, then stop each with Ctrl+C. The private queue and binding are declared by each driver on startup. Good messages are ACKed. The dispatcher routes its deliberately malformed messages under the `bangalore` prefix so the Control queue can receive and NACK them with `requeue=False`.

These are instructions, not evidence that a broker run has occurred. Capture actual console output and verify the routing before claiming D2/D3 live verification. Use a protected local environment variable for remote broker URLs; never paste credentials into logs, source control, or screenshots.