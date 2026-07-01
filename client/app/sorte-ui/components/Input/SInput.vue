<script setup>
/**
 * SInput — text field with optional leading icon, label and hint/error.
 * v-model works out of the box. Use `type="search"` for the search variant.
 */
import { computed, useId } from 'vue';
import SIcon from '../Icon/SIcon.vue';

const props = defineProps({
  modelValue: { type: [String, Number], default: '' },
  label: { type: String, default: null },
  type: { type: String, default: 'text' },
  placeholder: { type: String, default: '' },
  icon: { type: String, default: null },
  hint: { type: String, default: null },
  error: { type: String, default: null },
  size: { type: String, default: 'md' }, // sm | md | lg
  pill: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
});
defineEmits(['update:modelValue']);

const uid = useId();
const describedBy = computed(() => (props.error ? `${uid}-err` : props.hint ? `${uid}-hint` : undefined));
</script>

<template>
  <div class="s-field" :class="[`s-field--${size}`, { 's-field--error': error, 's-field--disabled': disabled }]">
    <label v-if="label" :for="uid" class="s-field__label">{{ label }}</label>
    <div class="s-field__control" :class="{ 's-field__control--pill': pill }">
      <SIcon v-if="icon" :name="icon" class="s-field__icon" :size="size === 'lg' ? 22 : 18" />
      <input
        :id="uid"
        class="s-field__input"
        :type="type"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :aria-invalid="!!error || undefined"
        :aria-describedby="describedBy"
        @input="$emit('update:modelValue', $event.target.value)"
      />
      <slot name="trailing" />
    </div>
    <p v-if="error" :id="`${uid}-err`" class="s-field__msg s-field__msg--error">{{ error }}</p>
    <p v-else-if="hint" :id="`${uid}-hint`" class="s-field__msg">{{ hint }}</p>
  </div>
</template>

<style scoped>
.s-field { display: flex; flex-direction: column; gap: var(--space-2); }
.s-field__label {
  font-family: var(--font-display);
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-sm);
  color: var(--color-text);
}

.s-field__control {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  background: var(--color-surface);
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius-md);
  padding-inline: var(--space-3);
  transition: border-color var(--dur-base) var(--ease-out), box-shadow var(--dur-base) var(--ease-out);
}
.s-field__control--pill { border-radius: var(--radius-pill); padding-inline: var(--space-4); }

.s-field--sm .s-field__control { min-block-size: 38px; }
.s-field--md .s-field__control { min-block-size: 46px; }
.s-field--lg .s-field__control { min-block-size: 54px; }

.s-field__control:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 4px var(--color-primary-soft);
}
.s-field--error .s-field__control { border-color: var(--color-danger); }
.s-field--error .s-field__control:focus-within { box-shadow: 0 0 0 4px var(--color-danger-soft); }

.s-field__icon { color: var(--color-text-muted); }
.s-field__input {
  flex: 1;
  border: 0;
  background: transparent;
  outline: none;
  padding-block: var(--space-2);
  font-family: var(--font-body);
  font-size: var(--font-size-md);
  color: var(--color-text);
  min-inline-size: 0;
}
.s-field__input::placeholder { color: var(--color-text-subtle); }

.s-field--disabled { opacity: 0.6; }
.s-field--disabled .s-field__control { background: var(--color-surface-sunken); cursor: not-allowed; }

.s-field__msg { font-size: var(--font-size-xs); color: var(--color-text-muted); margin: 0; }
.s-field__msg--error { color: var(--color-danger); font-weight: var(--font-weight-medium); }
</style>
