<script>import Icon from '../Icon.svelte';
const iconNode = [["path", { "d": "M4 7l16 0" }], ["path", { "d": "M10 11l0 6" }], ["path", { "d": "M14 11l0 6" }], ["path", { "d": "M5 7l1 12a2 2 0 0 0 2 2h8a2 2 0 0 0 2 -2l1 -12" }], ["path", { "d": "M9 7v-3a1 1 0 0 1 1 -1h4a1 1 0 0 1 1 1v3" }]];
</script>
<Icon type="outline" name="trash" {...$$props} iconNode={iconNode}>
  <slot/>
</Icon>
