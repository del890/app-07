#!/usr/bin/env node
// Fetches the full Mega Sena draw history from the Caixa public API and writes
// mega-sena.json to the project root in the same schema as data.json.
//
// Usage: node client/scripts/fetch-mega-sena.js
//
// The API returns all draws in one shot at /api/megasena — no pagination needed.

import { writeFileSync } from 'fs'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const OUT_PATH = resolve(__dirname, '../../mega-sena.json')
const API_URL = 'https://loteriascaixa-api.herokuapp.com/api/megasena'

console.log('Fetching Mega Sena history from', API_URL)

const response = await fetch(API_URL)
if (!response.ok) {
  console.error(`API error: ${response.status} ${response.statusText}`)
  process.exit(1)
}

/** @type {Array<{concurso:number, data:string, dezenas:string[], acumulou:boolean}>} */
const raw = await response.json()

console.log(`Received ${raw.length} draws`)

// Transform to project schema
// data.json format: { id, date: "DD-MM-YYYY", numbers: [...sorted ints] }
const dataset = raw
  .map(draw => {
    // date comes as "DD/MM/YYYY" from API — convert separators
    const date = draw.data.replace(/\//g, '-')
    const numbers = draw.dezenas.map(Number).sort((a, b) => a - b)
    return { id: draw.concurso, date, numbers }
  })
  .sort((a, b) => b.id - a.id) // newest first, matching data.json

const allowed_numbers = Array.from({ length: 60 }, (_, i) => i + 1)

const output = JSON.stringify({ allowed_numbers, dataset }, null, 2)
writeFileSync(OUT_PATH, output, 'utf8')

console.log(`✓ Wrote ${dataset.length} records to ${OUT_PATH}`)
