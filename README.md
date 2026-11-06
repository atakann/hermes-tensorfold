# hermes-tensorfold

A [Hermes Agent](https://github.com/NousResearch/hermes-agent) plugin for [TensorFold](https://github.com/ashhart/TensorFold)'s native server:

- **A model provider.** TensorFold appears in Hermes' model picker as "TensorFold". Hermes reads the served models from the server's `/v1/models` and each model's context window from the same list.
- **A dashboard tab.** The web dashboard gets a TensorFold page with the server's model, speed, streams, token counts, MTP acceptance and memory, read from its `/health`, `/stats` and `/v1/models` every 2 s.

The plugin talks to `http://127.0.0.1:8000/v1` by default, which is `tensorfold serve`'s own bind: the engine stays on loopback with its API key. Nothing changes the engine's tokens.

## Install

```sh
hermes plugins install atakann/hermes-tensorfold
hermes plugins enable tensorfold
```

Then give Hermes the server's API key and pick the model:

```sh
echo 'TENSORFOLD_API_KEY=<the key you gave tensorfold serve>' >> ~/.hermes/.env
hermes model        # choose TensorFold, then the served model
```

A server started without `--api-key` takes any value. For the dashboard tab, start the server with `--dashboard` (it serves `/stats` only then), and open `hermes dashboard`.

## Settings

| Variable | Default | Meaning |
|---|---|---|
| `TENSORFOLD_API_KEY` | none | The key the server was started with |
| `TENSORFOLD_BASE_URL` | `http://127.0.0.1:8000/v1` | The server's OpenAI-compatible root |

A server on another machine: keep it on that machine's loopback and forward a port, for example `ssh -N -L 8000:127.0.0.1:8000 my-gpu-box`. Then the default base URL works unchanged.

## Tool calls

Hermes' agent loop sends no `tool_choice`, so the server's `auto` applies. Some auxiliary requests can ask for `required`, which TensorFold enforces with its grammar library: the release archives include it (`lib/libtfgrammar.so`). A source build without it answers such a request with HTTP 400 and the reason.

## What it does on your machine

- It registers one model provider and one dashboard tab, and nothing else: no tools, hooks, commands, skills or background threads.
- It connects only to the TensorFold server at `TENSORFOLD_BASE_URL` (the loopback default unless you set it): Hermes' own client sends the chat requests, the provider reads `/v1/models` for the context window, and the tab's route reads `/health`, `/stats` and `/v1/models`. The API key goes only to that server, from the tab's route on the dashboard's side, never to the browser.
- It reads and writes no files, starts no processes and reports nothing anywhere.

## Checked with

Hermes Agent v0.23.0 and TensorFold 1.2.3 serving Qwen3.8-Flash-Next FP4-Local on a DGX Spark (GB10): `hermes plugins doctor` passes; the model picker lists TensorFold; chat and tool use work; a reply cancelled mid-stream frees its stream on the server, and the next request answers; with the server stopped Hermes reports an error, and it answers again once the server is back; the dashboard's numbers equal `/stats`.

## License

MIT
