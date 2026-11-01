// Einstieg: Tabs „Einkaufsliste“, „Meine Orders“ und „Gewinn“.

import { initAccount, onAccountTabShown } from "./account-ui.js";
import { $ } from "./dom.js";
import { initShopping } from "./shopping.js";

const TABS = ["liste", "orders", "gewinn"];

function show(tab) {
  const active = TABS.includes(tab) ? tab : "liste";
  for (const t of TABS) {
    $(`panel-${t}`).hidden = t !== active;
    const btn = $(`tab-${t}`);
    btn.setAttribute("aria-selected", t === active ? "true" : "false");
    btn.tabIndex = t === active ? 0 : -1;
  }
  $("key-panel").hidden = active === "liste";
  if (active !== "liste") onAccountTabShown();
}

for (const t of TABS) {
  $(`tab-${t}`).addEventListener("click", () => {
    window.location.hash = t;
  });
}
window.addEventListener("hashchange", () => show(window.location.hash.slice(1)));

initAccount();
show(window.location.hash.slice(1));
initShopping();
