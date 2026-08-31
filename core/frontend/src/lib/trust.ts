// Fase 17 §38/§39 — traduz os códigos de Trust/Integrity/Signature em
// linguagem clara pra UI. TRUSTED/VERIFIED/UNVERIFIED/INVALID/REVOKED
// nunca devem aparecer "nus" (só o enum) sem uma frase explicando o
// que significam pro usuário.
import type { ModuleTrust } from '@/types'

const INTEGRITY_TEXT: Record<string, string> = {
  VALID: 'Package integrity confirmed.',
  MODIFIED: 'Files have been modified since installation.',
  MISSING_FILE: 'Files are missing since installation.',
  UNEXPECTED_FILE: 'Unexpected files found that were not part of the original install.',
  INVALID_MANIFEST: 'Integrity manifest is missing or corrupted.',
}

const SIGNATURE_TEXT: Record<string, string> = {
  VALID: 'Publisher signature verified.',
  INVALID: 'Publisher signature is invalid — content may not match the publisher.',
  NOT_CONFIGURED: 'Publisher signature not configured.',
  UNSUPPORTED: 'Signature could not be verified.',
}

export interface TrustDescription {
  /** One-line human summary, e.g. "Verified — Package integrity confirmed. Publisher signature not configured." */
  summary: string
  /** Concrete, actionable warnings — empty when nothing needs attention. */
  warnings: string[]
}

export function describeTrust(trust: ModuleTrust): TrustDescription {
  const integrityText = INTEGRITY_TEXT[trust.integrity_status] ?? trust.integrity_status
  const signatureText = SIGNATURE_TEXT[trust.signature_status] ?? trust.signature_status
  const levelLabel = trust.trust_level.charAt(0) + trust.trust_level.slice(1).toLowerCase()

  const summary = `${levelLabel} — ${integrityText} ${signatureText}`

  const warnings: string[] = []
  if (trust.integrity_status !== 'VALID') {
    warnings.push(integrityText)
  }
  if (trust.signature_status === 'INVALID') {
    warnings.push(signatureText)
  }
  if (trust.publisher?.trust_status === 'REVOKED') {
    warnings.push(`Publisher "${trust.publisher.name}" has been revoked.`)
  }

  return { summary, warnings }
}
