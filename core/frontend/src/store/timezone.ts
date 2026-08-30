import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface TimezoneState {
  timezone: string
  setTimezone: (tz: string) => void
}

export const useTimezoneStore = create<TimezoneState>()(
  persist(
    (set) => ({
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      setTimezone: (tz) => set({ timezone: tz }),
    }),
    { name: 'techforge-timezone' }
  )
)
