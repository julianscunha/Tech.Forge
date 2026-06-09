import React from 'react'
import ReactDOM from 'react-dom/client'
import { AppRouter } from './AppRouter'
import './styles/globals.css'

// Apply persisted theme before first paint to prevent flash
const stored = localStorage.getItem('techforge-ui')
if (stored) {
  try {
    const { state } = JSON.parse(stored) as { state: { theme: string } }
    document.documentElement.classList.add(`theme-${state.theme}`)
  } catch {
    document.documentElement.classList.add('theme-dark')
  }
} else {
  document.documentElement.classList.add('theme-dark')
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AppRouter />
  </React.StrictMode>
)
