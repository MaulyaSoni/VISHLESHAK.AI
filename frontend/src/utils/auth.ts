import type { Domain, User } from '@/store/useAppStore'

const VALID_DOMAINS: Domain[] = ['general', 'finance', 'insurance', 'ecommerce']

function normalizeDomain(value: unknown): Domain {
  if (typeof value === 'string' && VALID_DOMAINS.includes(value as Domain)) {
    return value as Domain
  }
  return 'general'
}

export function normalizeUserPayload(payload: unknown): User | null {
  if (!payload || typeof payload !== 'object') {
    return null
  }

  const maybeWrapped = payload as Record<string, unknown>
  const raw = (
    maybeWrapped.user && typeof maybeWrapped.user === 'object'
      ? maybeWrapped.user
      : maybeWrapped
  ) as Record<string, unknown>

  const email = typeof raw.email === 'string' ? raw.email.trim() : ''
  const username = typeof raw.username === 'string' && raw.username.trim()
    ? raw.username.trim()
    : (typeof raw.full_name === 'string' ? raw.full_name.trim() : '') ||
      (email.includes('@') ? email.split('@')[0] : '') ||
      'user'

  const id =
    typeof raw.id === 'number' || typeof raw.id === 'string'
      ? raw.id
      : 'unknown'

  if (!email && !username) {
    return null
  }

  return {
    id,
    email: email || `${username}@local`,
    username,
    domain: normalizeDomain(raw.domain),
  }
}
