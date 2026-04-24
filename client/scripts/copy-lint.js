#!/usr/bin/env node
/**
 * copy-lint.js — checks all client Vue/TS source files for banned marketing words.
 * Banned: "guaranteed", "winning", "sure" (case-insensitive, whole-word).
 * Exit code 1 if any violations found (fails CI).
 *
 * Usage: node scripts/copy-lint.js
 */

import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join, extname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { dirname } from 'node:path'

const __dirname = dirname(fileURLToPath(import.meta.url))
const appDir = join(__dirname, '..', 'app')

const BANNED = [/\bguaranteed\b/gi, /\bwinning\b/gi, /\bsure\b/gi]
const EXTENSIONS = new Set(['.vue', '.ts'])

let violations = 0

function walk(dir) {
  for (const name of readdirSync(dir)) {
    const full = join(dir, name)
    if (statSync(full).isDirectory()) {
      walk(full)
      continue
    }
    if (!EXTENSIONS.has(extname(name))) continue
    const src = readFileSync(full, 'utf8')
    const lines = src.split('\n')
    for (let i = 0; i < lines.length; i++) {
      for (const pattern of BANNED) {
        pattern.lastIndex = 0
        if (pattern.test(lines[i])) {
          console.error(`${full}:${i + 1}: banned word "${pattern.source}" found: ${lines[i].trim()}`)
          violations++
        }
      }
    }
  }
}

walk(appDir)

if (violations > 0) {
  console.error(`\ncopy-lint: ${violations} violation(s) found.`)
  process.exit(1)
} else {
  console.log('copy-lint: OK — no banned words found.')
}
