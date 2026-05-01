import { openDB, type IDBPDatabase } from 'idb'
import type { DreamOracleEntry } from '~/types/api'

const DB_NAME = 'lotofacil-oracle'
const DB_VERSION = 1
const STORE_NAME = 'entries'

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

try {
  getDb()
} catch {
  // handled above
}

export function useDreamOracleStore() {
  const storeAvailable = computed(() => storeAvailableFlag)

  async function saveEntry(payload: Omit<DreamOracleEntry, 'id' | 'savedAt'>): Promise<number | null> {
    try {
      const db = await getDb()
      const entry: Omit<DreamOracleEntry, 'id'> = {
        savedAt: new Date().toISOString(),
        ...payload,
      }
      const id = await db.add(STORE_NAME, entry)
      return id as number
    } catch {
      return null
    }
  }

  async function listEntries(): Promise<DreamOracleEntry[]> {
    try {
      const db = await getDb()
      const all = await db.getAll(STORE_NAME)
      return (all as DreamOracleEntry[]).sort((a, b) => b.savedAt.localeCompare(a.savedAt))
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
