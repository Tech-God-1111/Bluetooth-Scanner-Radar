(() => {
  const byId = id => document.getElementById(id);
  const escapeText = value => String(value ?? "—").replace(/[&<>"']/g, ch => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]));
  const markerClass = status => status === "trusted" ? "trusted-marker" : status === "ignored" ? "ignored-marker" : "unknown-marker";

  function markerPosition(index, total) {
    // Deterministic decorative placement only; these coordinates are not geography or distance.
    const angle = index * 2.399963229728653;
    const ring = total <= 1 ? 72 : 62 + (index % 3) * 43;
    return {x: 210 + Math.cos(angle) * ring, y: 210 + Math.sin(angle) * ring};
  }

  function renderRadar(data) {
    const svg = byId("network-radar");
    const markers = byId("radar-markers");
    const devices = data.devices || [];
    const sorted = [...devices].sort((a,b) => String(a.mac_address || a.ip_address).localeCompare(String(b.mac_address || b.ip_address)));
    let html = '<circle cx="210" cy="210" r="8" class="gateway-marker"/><text x="222" y="214" class="radar-label">GATEWAY</text>';
    sorted.forEach((device, index) => {
      const p = markerPosition(index, sorted.length);
      const label = device.hostname || device.ip_address || "Device";
      html += '<g class="device-marker" tabindex="0" role="img" aria-label="' + escapeText(label) + ' · ' + escapeText(device.trust_status) + '"><title>' + escapeText(label) + ' — ' + escapeText(device.ip_address) + ' — ' + escapeText(device.trust_status) + '</title><circle cx="' + p.x.toFixed(1) + '" cy="' + p.y.toFixed(1) + '" r="12" class="' + markerClass(device.trust_status) + '"/><circle cx="' + p.x.toFixed(1) + '" cy="' + p.y.toFixed(1) + '" r="3" class="marker-core"/></g>';
    });
    markers.innerHTML = html;
    byId("radar-empty").hidden = devices.length > 0;
    byId("radar-state").classList.toggle("scanning", !!data.scan?.running);
    byId("radar-state").innerHTML = '<i></i> ' + (data.scan?.running ? "SCANNING" : "READY");
    svg.classList.toggle("is-scanning", !!data.scan?.running);
  }

  function renderWifi(wifi) {
    const connected = !!wifi.connected;
    const signal = Number.isInteger(wifi.signal_percent) ? wifi.signal_percent : null;
    byId("wifi-connection-state").textContent = connected ? "CONNECTED" : "NOT CONNECTED";
    byId("wifi-signal").innerHTML = signal === null ? "—<small>%</small>" : signal + "<small>%</small>";
    byId("wifi-signal-bar").style.width = (signal ?? 0) + "%";
    byId("wifi-quality").textContent = wifi.quality || "Unavailable";
    byId("wifi-ssid").textContent = wifi.ssid || "—";
    byId("wifi-bssid").textContent = wifi.bssid || "—";
    byId("wifi-channel").textContent = wifi.channel ?? "—";
    byId("wifi-radio").textContent = wifi.radio_type || "—";
    byId("wifi-rx").textContent = wifi.receive_rate_mbps == null ? "—" : wifi.receive_rate_mbps + " Mbps";
    byId("wifi-tx").textContent = wifi.transmit_rate_mbps == null ? "—" : wifi.transmit_rate_mbps + " Mbps";
    const samples = wifi.history || [];
    byId("wifi-history").innerHTML = samples.length ? samples.map(s => '<span class="history-bar" style="height:' + Math.max(5, s.signal_percent) + '%" title="' + s.signal_percent + '% · ' + escapeText(s.quality) + '"></span>').join("") : '<span class="history-empty">Samples appear while connected.</span>';
  }

  async function updateRadar() {
    try {
      const response = await fetch("/api/radar", {cache:"no-store"});
      if (!response.ok) throw new Error("Radar data unavailable");
      const data = await response.json();
      renderRadar(data);
      renderWifi(data.wifi || {});
    } catch (error) {
      byId("radar-state").textContent = "DATA UNAVAILABLE";
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    updateRadar();
    window.setInterval(updateRadar, 5000);
  });
})();