type GeoLocation = {
  country: string
  country_name: string
  state: string
  city: string
}

type GeoState = {
  location: GeoLocation | null
  loading: boolean
}

const FALLBACK: GeoLocation = { country: 'IN', country_name: 'India', state: '', city: '' }

let cached: GeoLocation | null = null

export async function detectGeolocation(): Promise<GeoLocation> {
  if (cached) return cached
  try {
    const res = await fetch('https://ipapi.co/json/', { signal: AbortSignal.timeout(5000) })
    const data = await res.json()
    cached = {
      country: (data.country_code as string) || 'IN',
      country_name: (data.country_name as string) || 'India',
      state: (data.region as string) || '',
      city: (data.city as string) || '',
    }
    return cached
  } catch {
    return FALLBACK
  }
}

import { useEffect, useState } from 'react'

export function useGeolocation(): GeoState {
  const [state, setState] = useState<GeoState>({ location: cached, loading: !cached })

  useEffect(() => {
    if (cached) return
    let cancelled = false
    detectGeolocation().then((loc) => {
      if (!cancelled) setState({ location: loc, loading: false })
    })
    return () => {
      cancelled = true
    }
  }, [])

  return state
}
