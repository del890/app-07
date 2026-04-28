import { openDB, type IDBPDatabase } from 'idb'
import type { DrawProfileResponse, MyDrawEntry } from '~/types/api'

const DB_NAME = 'lotofacil-app'
const DB_VERSION = 1
const STORE_NAME = 'entries'

// Module-level singleton: shared across all composable calls within a page session.
let dbPromise: Promise<IDBPDatabase> | null = null
let storeAvailableFlag = true

function getDb(): Promise<IDBPDatabase> {
  if (!dbPromise) {
    dbPromise = openDB(DB_NAME, DB_VERSION, {
      upgrade(db) {
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          const store = db.createObjectStore(STORE_NAME, {
            keyPath: 'id',
            autoIncrement: true,
          })
          store.createIndex('savedAt', 'savedAt', { unique: false })
        }
      },
    }).catch((err) => {
      storeAvailableFlag = false
      dbPromise = null
      throw err
    })
  }
  return dbPromise
}

// Eagerly attempt to open the DB so failures are caught early.
try {
  getDb()
} catch {
  // Already handled inside getDb — storeAvailableFlag is set to false.
}

export function useMyDrawStore() {
  const storeAvailable = computed(() => storeAvailableFlag)

  async function saveEntry(payload: {
    numbers: number[]
    profile: DrawProfileResponse
  }): Promise<number | null> {
    try {
      const db = await getDb()
      const entry: Omit<MyDrawEntry, 'id'> = {
        savedAt: new Date().toISOString(),
        numbers: payload.numbers,
        profile: payload.profile,
      }
      const id = await db.add(STORE_NAME, entry)
      return id as number
    } catch {
      return null
    }
  }

  async function listEntries(): Promise<MyDrawEntry[]> {
    try {
      const db = await getDb()
      const all = await db.getAll(STORE_NAME)
      return (all as MyDrawEntry[]).sort((a, b) => b.savedAt.localeCompare(a.savedAt))
    } catch {
      return []
    }
  }

  async function deleteEntry(id: number): Promise<void> {
    try {
      const db = await getDb()
      await db.delete(STORE_NAME, id)
    } catch {
      // no-op
    }
  }

  async function clearEntries(): Promise<void> {
    try {
      const db = await getDb()
      await db.clear(STORE_NAME)
    } catch {
      // no-op
    }
  }

  return { storeAvailable, saveEntry, listEntries, deleteEntry, clearEntries }
}
