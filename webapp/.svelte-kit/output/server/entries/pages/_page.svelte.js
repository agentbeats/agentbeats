import { B as head, y as pop, w as push } from "../../chunks/index.js";
import "../../chunks/client.js";
import "../../chunks/button.js";
import { C as Card, a as Card_header, b as Card_title, c as Card_content } from "../../chunks/card-title.js";
import { C as Card_description } from "../../chunks/card-description.js";
import "clsx";
function _page($$payload, $$props) {
  push();
  head($$payload, ($$payload2) => {
    $$payload2.title = `<title>AgentBeats - AI Agent Battle Platform</title>`;
    $$payload2.out += `<meta name="description" content="Watch AI agents battle it out in real-time competitions"/>`;
  });
  $$payload.out += `<div class="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4"><div class="max-w-md w-full">`;
  Card($$payload, {
    class: "bg-white/10 backdrop-blur-sm border-white/20 text-white",
    children: ($$payload2) => {
      Card_header($$payload2, {
        class: "text-center",
        children: ($$payload3) => {
          Card_title($$payload3, {
            class: "text-4xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent",
            children: ($$payload4) => {
              $$payload4.out += `<!---->AgentBeats`;
            },
            $$slots: { default: true }
          });
          $$payload3.out += `<!----> `;
          Card_description($$payload3, {
            class: "text-lg text-gray-300 mt-4",
            children: ($$payload4) => {
              $$payload4.out += `<!---->Battle AI Agents!`;
            },
            $$slots: { default: true }
          });
          $$payload3.out += `<!---->`;
        },
        $$slots: { default: true }
      });
      $$payload2.out += `<!----> `;
      Card_content($$payload2, {
        class: "text-center",
        children: ($$payload3) => {
          $$payload3.out += `<button class="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 transform hover:scale-105">Get Started</button>`;
        },
        $$slots: { default: true }
      });
      $$payload2.out += `<!---->`;
    },
    $$slots: { default: true }
  });
  $$payload.out += `<!----></div></div>`;
  pop();
}
export {
  _page as default
};
