// The TensorFold tab: the server's /health, /stats and /v1/models through plugin_api.py, read every 2 s.
(function () {
  "use strict";
  const SDK = window.__HERMES_PLUGIN_SDK__;
  const { React } = SDK;
  const { useState, useEffect } = SDK.hooks;
  const { Card, CardHeader, CardTitle, CardContent, Badge } = SDK.components;
  const h = React.createElement;

  const gib = (b) => (typeof b === "number" ? (b / 2 ** 30).toFixed(1) + " GiB" : "–");
  const num = (n, d = 0) => (typeof n === "number" ? n.toLocaleString(undefined, { maximumFractionDigits: d }) : "–");

  function Rows(props) {
    return h("dl", { className: "grid grid-cols-2 gap-x-4 gap-y-1 text-sm" },
      props.rows.flatMap(([k, v]) => [
        h("dt", { key: k + ":k", className: "text-muted-foreground" }, k),
        h("dd", { key: k + ":v", className: "font-mono" }, v),
      ]));
  }

  function Box(props) {
    return h(Card, null, h(CardHeader, null, h(CardTitle, null, props.title)), h(CardContent, null, h(Rows, { rows: props.rows })));
  }

  function Page() {
    const [d, setD] = useState(null);
    const [err, setErr] = useState(null);
    useEffect(() => {
      let live = true;
      const tick = () =>
        SDK.fetchJSON("/api/plugins/tensorfold/summary")
          .then((x) => live && (setD(x), setErr(null)))
          .catch((e) => live && setErr(String(e)));
      tick();
      const t = setInterval(tick, 2000);
      return () => { live = false; clearInterval(t); };
    }, []);
    if (err) return h("p", { className: "text-sm text-destructive" }, err);
    if (!d) return h("p", { className: "text-sm text-muted-foreground" }, "Reading the server…");
    const hl = d.health.ok ? d.health.body : {};
    const st = d.stats.ok ? d.stats.body : {};
    const models = d.models.ok ? d.models.body.data || [] : [];
    const errors = [d.health, d.stats, d.models].filter((x) => !x.ok).map((x) => x.error);
    const drafted = st.mtp_drafted_total, accepted = st.mtp_accepted_total;
    return h("div", { className: "flex flex-col gap-4" },
      h("div", { className: "flex items-center gap-2" },
        h(Badge, null, hl.status === "ok" ? "serving" : "not answering"),
        h("span", { className: "text-sm text-muted-foreground font-mono" }, d.server)),
      errors.length ? h("p", { className: "text-sm text-destructive" }, errors.join(" · ")) : null,
      h("div", { className: "grid gap-4 md:grid-cols-2" },
        h(Box, { title: "Model", rows: [
          ["served", hl.model || "–"],
          ["context", models.length ? num(models[0].context_length) + " tokens" : "–"],
          ["streams at once", num(hl.max_batch_size)],
          ["engine", [hl.version && "TensorFold " + hl.version, hl.backend, hl.device].filter(Boolean).join(" · ") || "–"],
        ] }),
        h(Box, { title: "Now", rows: [
          ["decode", num(st.decode_tokens_per_second, 1) + " tok/s"],
          ["prefill", num(st.prefill_tokens_per_second, 1) + " tok/s"],
          ["running", num(st.running)],
          ["waiting", num(st.waiting)],
        ] }),
        h(Box, { title: "Since start", rows: [
          ["prompt tokens", num(st.prompt_tokens_total)],
          ["generated tokens", num(st.generation_tokens_total)],
          ["decode rounds", num(st.decode_rounds_total)],
          ["MTP drafts accepted", drafted ? num(accepted) + " of " + num(drafted) + " (" + num((100 * accepted) / drafted, 1) + "%)" : "–"],
        ] }),
        h(Box, { title: "Memory", rows: [
          ["active", gib(st.memory && st.memory.active)],
          ["cache", gib(st.memory && st.memory.cache)],
          ["peak", gib(st.memory && st.memory.peak)],
        ] })));
  }

  window.__HERMES_PLUGINS__.register("tensorfold", Page);
})();
