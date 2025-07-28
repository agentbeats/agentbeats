import { P as escape_html, y as pop, w as push } from "../../../../chunks/index.js";
import "clsx";
import "../../../../chunks/client.js";
import "../../../../chunks/supabase.js";
import { C as Card, a as Card_header, b as Card_title, c as Card_content } from "../../../../chunks/card-title.js";
import { C as Card_description } from "../../../../chunks/card-description.js";
function _page($$payload, $$props) {
  push();
  $$payload.out += `<div class="min-h-screen flex items-center justify-center bg-gray-50 p-4">`;
  Card($$payload, {
    class: "shadow-lg max-w-md w-full p-6",
    children: ($$payload2) => {
      Card_header($$payload2, {
        class: "text-center space-y-2",
        children: ($$payload3) => {
          Card_title($$payload3, {
            class: "text-2xl font-bold break-words",
            children: ($$payload4) => {
              $$payload4.out += `<!---->${escape_html("Signing you in...")}`;
            },
            $$slots: { default: true }
          });
          $$payload3.out += `<!----> `;
          Card_description($$payload3, {
            class: "break-words",
            children: ($$payload4) => {
              $$payload4.out += `<!---->${escape_html("Please wait while we complete your sign-in")}`;
            },
            $$slots: { default: true }
          });
          $$payload3.out += `<!---->`;
        },
        $$slots: { default: true }
      });
      $$payload2.out += `<!----> `;
      Card_content($$payload2, {
        class: "text-center flex flex-col items-center gap-6",
        children: ($$payload3) => {
          {
            $$payload3.out += "<!--[-->";
            $$payload3.out += `<div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>`;
          }
          $$payload3.out += `<!--]-->`;
        },
        $$slots: { default: true }
      });
      $$payload2.out += `<!---->`;
    },
    $$slots: { default: true }
  });
  $$payload.out += `<!----></div>`;
  pop();
}
export {
  _page as default
};
