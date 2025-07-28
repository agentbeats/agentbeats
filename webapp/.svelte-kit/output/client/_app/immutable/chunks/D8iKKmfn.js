var I=t=>{throw TypeError(t)};var W=(t,e,n)=>e.has(t)||I("Cannot "+n);var r=(t,e,n)=>(W(t,e,"read from private field"),n?n.call(t):e.get(t)),p=(t,e,n)=>e.has(t)?I("Cannot add the same private member more than once"):e instanceof WeakSet?e.add(t):e.set(t,n),$=(t,e,n,o)=>(W(t,e,"write to private field"),o?o.call(t,n):e.set(t,n),n);import{u as S,i as L,p as b,l as T,d as A,ay as N,az as v,a as k,b as z}from"./D_E79TID.js";import{b as V}from"./1q5JTXAK.js";import"./CWj6FrbW.js";import{s as O,r as R}from"./gMceMjmh.js";import{I as D}from"./DAY4XnSZ.js";function U(t,e,n=!0){if(!(t.length===0||e<0||e>=t.length))return t.length===1&&e===0?t[0]:e===t.length-1?n?t[0]:void 0:t[e+1]}function X(t,e,n=!0){if(!(t.length===0||e<0||e>=t.length))return t.length===1&&e===0?t[0]:e===0?n?t[t.length-1]:void 0:t[e-1]}function Y(t,e,n,o=!0){if(t.length===0||e<0||e>=t.length)return;let h=e+n;return o?h=(h%t.length+t.length)%t.length:h=Math.max(0,Math.min(h,t.length-1)),t[h]}function Z(t,e,n,o=!0){if(t.length===0||e<0||e>=t.length)return;let h=e-n;return o?h=(h%t.length+t.length)%t.length:h=Math.max(0,Math.min(h,t.length-1)),t[h]}function P(t,e,n){const o=e.toLowerCase();if(o.endsWith(" ")){const s=o.slice(0,-1);if(t.filter(g=>g.toLowerCase().startsWith(s)).length<=1)return P(t,s,n);const M=n==null?void 0:n.toLowerCase();if(M&&M.startsWith(s)&&M.charAt(s.length)===" "&&e.trim()===s)return n;const x=t.filter(g=>g.toLowerCase().startsWith(o));if(x.length>0){const g=n?t.indexOf(n):-1;return _(x,Math.max(g,0)).find(E=>E!==n)||n}}const d=e.length>1&&Array.from(e).every(s=>s===e[0])?e[0]:e,i=d.toLowerCase(),c=n?t.indexOf(n):-1;let a=_(t,Math.max(c,0));d.length===1&&(a=a.filter(s=>s!==n));const u=a.find(s=>s==null?void 0:s.toLowerCase().startsWith(i));return u!==n?u:void 0}function _(t,e){return t.map((n,o)=>t[(e+o)%t.length])}var l,f,m,w;class y{constructor(e){p(this,l);p(this,f);p(this,m,S(()=>r(this,l).onMatch?r(this,l).onMatch:e=>e.focus()));p(this,w,S(()=>r(this,l).getCurrentItem?r(this,l).getCurrentItem:r(this,l).getActiveElement));$(this,l,e),$(this,f,V("",{afterMs:1e3,getWindow:e.getWindow})),this.handleTypeaheadSearch=this.handleTypeaheadSearch.bind(this),this.resetTypeahead=this.resetTypeahead.bind(this)}handleTypeaheadSearch(e,n){var a,C;if(!n.length)return;r(this,f).current=r(this,f).current+e;const o=L(r(this,w))(),h=((C=(a=n.find(u=>u===o))==null?void 0:a.textContent)==null?void 0:C.trim())??"",d=n.map(u=>{var s;return((s=u.textContent)==null?void 0:s.trim())??""}),i=P(d,r(this,f).current,h),c=n.find(u=>{var s;return((s=u.textContent)==null?void 0:s.trim())===i});return c&&L(r(this,m))(c),c}resetTypeahead(){r(this,f).current=""}get search(){return r(this,f).current}}l=new WeakMap,f=new WeakMap,m=new WeakMap,w=new WeakMap;function tt(t,e){b(e,!0);/**
 * @license @lucide/svelte v0.515.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2022 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2022.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 */let n=R(e,["$$slots","$$events","$$legacy"]);const o=[["path",{d:"M20 6 9 17l-5-5"}]];D(t,O({name:"check"},()=>n,{get iconNode(){return o},children:(h,d)=>{var i=T(),c=A(i);N(c,()=>e.children??v),k(h,i)},$$slots:{default:!0}})),z()}function et(t,e){b(e,!0);/**
 * @license @lucide/svelte v0.515.0 - ISC
 *
 * ISC License
 *
 * Copyright (c) for portions of Lucide are held by Cole Bemis 2013-2022 as part of Feather (MIT). All other copyright (c) for Lucide are held by Lucide Contributors 2022.
 *
 * Permission to use, copy, modify, and/or distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
 * WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
 * ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
 * WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
 * ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
 * OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
 *
 */let n=R(e,["$$slots","$$events","$$legacy"]);const o=[["path",{d:"m6 9 6 6 6-6"}]];D(t,O({name:"chevron-down"},()=>n,{get iconNode(){return o},children:(h,d)=>{var i=T(),c=A(i);N(c,()=>e.children??v),k(h,i)},$$slots:{default:!0}})),z()}export{tt as C,y as D,et as a,Z as b,Y as f,P as g,U as n,X as p};
